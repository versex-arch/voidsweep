"""Local HTTP backend for the interface.

Security model: the server listens on 127.0.0.1 only, on a random port, and
every API call must carry a random per-launch token. Requests whose Host or
Origin is not this server are rejected, which blocks DNS-rebinding and
cross-site requests from web pages open in the user's browser.
"""

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from . import APP_NAME, __version__
from .cleaner import PERMANENT, TRASH, clean
from .config import Store, data_dir
from .markers import MARKERS
from .platforms import Env, LINUX, MACOS, WINDOWS, is_admin, list_drives
from .safety import Guard
from .scanner import Cancelled, Finding, ScanOptions, Scanner, summarize

WEB_ROOT = Path(__file__).with_name("web")


class Job:
    def __init__(self, kind: str):
        self.kind = kind
        self.state = "running"  # running | done | cancelled | error
        self.progress: Dict[str, object] = {}
        self.error = ""
        self.started = time.time()
        self.finished: Optional[float] = None
        self.result: object = None

    def to_dict(self) -> dict:
        return {"kind": self.kind, "state": self.state, "progress": self.progress,
                "error": self.error, "started": self.started, "finished": self.finished}


class App:
    """State shared by all request handler threads."""

    def __init__(self, env: Optional[Env] = None, store: Optional[Store] = None,
                 demo: bool = False):
        self.env = env or Env.detect()
        self.store = store or Store(self.env)
        self.demo = demo
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.Lock()
        self.findings: List[Finding] = []
        self.scanner: Optional[Scanner] = None
        self.job: Optional[Job] = None
        self.last_ping = time.time()

    # ------------------------------------------------------------- helpers
    def guard(self) -> Guard:
        return Guard(self.env, self.store.ignore_list() + [str(data_dir(self.env))])

    def busy(self) -> bool:
        return self.job is not None and self.job.state == "running"

    def info(self) -> dict:
        if self.demo:
            from .demo import demo_drives
            drives = demo_drives()
        else:
            drives = list_drives(self.env)
        return {
            "app": APP_NAME, "version": __version__, "os": self.env.os,
            "home": str(self.env.home), "admin": is_admin(), "demo": self.demo,
            "drives": [d.to_dict() for d in drives],
            "markers": [m.to_dict() for m in MARKERS.values()],
            "settings": self.store.settings(), "ignore": self.store.ignore_list(),
        }

    # ---------------------------------------------------------------- scan
    def start_scan(self, deep: bool, drives: List[str]) -> Job:
        with self.lock:
            if self.busy():
                raise RuntimeError("busy")
            job = self.job = Job("scan")
            self.findings = []
        if self.demo:
            from .demo import demo_findings
            self.findings = demo_findings()
            job.progress = {"phase": "done", "found": len(self.findings)}
            job.state, job.finished = "done", time.time()
            return job
        scanner = self.scanner = Scanner(self.env, self.guard().ignore)

        def progress(info: dict) -> None:
            job.progress = info

        def run() -> None:
            try:
                self.findings = scanner.run(ScanOptions(deep=deep, drives=drives), progress)
                job.state = "done"
            except Cancelled:
                self.findings = scanner.findings
                job.state = "cancelled"
            except Exception as exc:  # surfaced to the UI, never swallowed
                job.state, job.error = "error", f"{type(exc).__name__}: {exc}"
            job.finished = time.time()

        threading.Thread(target=run, daemon=True, name="voidsweep-scan").start()
        return job

    def cancel(self) -> None:
        if self.scanner and self.busy():
            self.scanner.cancel()

    def results(self) -> dict:
        return {"findings": [f.to_dict() for f in self.findings],
                "summary": summarize(self.findings)}

    # --------------------------------------------------------------- clean
    def start_clean(self, ids: List[int], mode: str) -> Job:
        if mode not in (TRASH, PERMANENT):
            raise ValueError("mode")
        by_id = {f.id: f for f in self.findings}
        chosen = [by_id[i] for i in ids if i in by_id]
        with self.lock:
            if self.busy():
                raise RuntimeError("busy")
            job = self.job = Job("clean")

        def progress(i: int, total: int, path: str) -> None:
            job.progress = {"phase": "clean", "step": i, "total": total, "detail": path}

        def run() -> None:
            try:
                if self.demo:
                    from .cleaner import Result
                    results = [Result(f.id, f.path, f.marker, f.size, "ok") for f in chosen]
                else:
                    results = clean(chosen, self.guard(), mode, progress)
                freed = sum(r.size for r in results if r.status == "ok")
                removed = {r.id for r in results if r.ok}
                self.findings = [f for f in self.findings if f.id not in removed]
                job.result = {"results": [r.to_dict() for r in results], "freed": freed,
                              "mode": mode}
                if not self.demo:
                    self.store.add_history({
                        "mode": mode, "freed": freed,
                        "ok": sum(1 for r in results if r.ok),
                        "failed": sum(1 for r in results if not r.ok),
                        "items": [{"path": r.path, "marker": r.marker, "size": r.size,
                                   "status": r.status} for r in results][:2000],
                    })
                job.state = "done"
            except Exception as exc:
                job.state, job.error = "error", f"{type(exc).__name__}: {exc}"
            job.finished = time.time()

        threading.Thread(target=run, daemon=True, name="voidsweep-clean").start()
        return job

    # -------------------------------------------------------------- reveal
    def reveal(self, finding_id: int) -> None:
        f = next((x for x in self.findings if x.id == finding_id), None)
        if f is None:
            raise KeyError(finding_id)
        path = f.path if os.path.lexists(f.path) else os.path.dirname(f.path)
        if self.env.os == WINDOWS:
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif self.env.os == MACOS:
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path) or path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"{APP_NAME}/{__version__}"

        def log_message(self, fmt, *args):  # keep the console quiet
            pass

        # ---------------------------------------------------------- utils
        def _send(self, code: int, body: bytes, ctype: str, extra: Optional[dict] = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; img-src 'self' data:; style-src 'self'; "
                             "script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, obj, code: int = 200):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def _host_ok(self) -> bool:
            port = self.server.server_address[1]
            allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if self.headers.get("Host") not in allowed:
                return False
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc not in allowed:
                return False
            return True

        def _authorized(self) -> bool:
            got = self.headers.get("X-Voidsweep-Token", "")
            return secrets.compare_digest(got, app.token)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 1_000_000:
                raise ValueError("body too large")
            raw = self.rfile.read(n) if n else b"{}"
            data = json.loads(raw or b"{}")
            if not isinstance(data, dict):
                raise ValueError("object expected")
            return data

        # --------------------------------------------------------- routes
        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if not self._host_ok():
                return self._send(403, b"forbidden", "text/plain")
            path = urlparse(self.path).path
            if path.startswith("/api/"):
                if not self._authorized():
                    return self._json({"error": "unauthorized"}, 401)
                app.last_ping = time.time()
                if path == "/api/info":
                    return self._json(app.info())
                if path == "/api/job":
                    return self._json(app.job.to_dict() if app.job else {"state": "idle"})
                if path == "/api/results":
                    return self._json(app.results())
                if path == "/api/clean/result":
                    return self._json(app.job.result if app.job and app.job.kind == "clean"
                                      else {})
                if path == "/api/history":
                    return self._json({"history": app.store.history()})
                return self._json({"error": "not found"}, 404)
            return self._static(path)

        def do_POST(self):
            if not self._host_ok():
                return self._send(403, b"forbidden", "text/plain")
            if not self._authorized():
                return self._json({"error": "unauthorized"}, 401)
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._json({"error": "json required"}, 415)
            app.last_ping = time.time()
            path = urlparse(self.path).path
            try:
                body = self._body()
                if path == "/api/scan":
                    drives = [str(d) for d in body.get("drives", [])]
                    known = {d.path for d in list_drives(app.env)}
                    drives = [d for d in drives if d in known]
                    job = app.start_scan(bool(body.get("deep")), drives)
                    return self._json(job.to_dict())
                if path == "/api/cancel":
                    app.cancel()
                    return self._json({"ok": True})
                if path == "/api/clean":
                    ids = [int(i) for i in body.get("ids", [])]
                    job = app.start_clean(ids, str(body.get("mode", TRASH)))
                    return self._json(job.to_dict())
                if path == "/api/reveal":
                    app.reveal(int(body["id"]))
                    return self._json({"ok": True})
                if path == "/api/ignore":
                    target = str(body["path"])
                    if body.get("remove"):
                        items = app.store.remove_ignore(target)
                    else:
                        items = app.store.add_ignore(target)
                        app.findings = [f for f in app.findings
                                        if not Guard(app.env, [target]).is_ignored(f.path)]
                    return self._json({"ignore": items})
                if path == "/api/settings":
                    lang = body.get("lang")
                    if lang not in (None, "ru", "en"):
                        raise ValueError("lang")
                    return self._json(app.store.save_settings(lang=lang))
                if path == "/api/ping":
                    return self._json({"ok": True})
                if path == "/api/quit":
                    self._json({"ok": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return None
                return self._json({"error": "not found"}, 404)
            except RuntimeError:
                return self._json({"error": "busy"}, 409)
            except (KeyError, ValueError, TypeError) as exc:
                return self._json({"error": f"bad request: {exc}"}, 400)

        def _static(self, path: str):
            if path in ("", "/"):
                path = "/index.html"
            target = (WEB_ROOT / path.lstrip("/")).resolve()
            if WEB_ROOT.resolve() not in target.parents or not target.is_file():
                return self._send(404, b"not found", "text/plain")
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
                ctype += "; charset=utf-8"
            return self._send(200, target.read_bytes(), ctype)

    return Handler


def serve(app: App, port: int = 0) -> ThreadingHTTPServer:
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
    httpd.daemon_threads = True
    return httpd


def url_for(httpd: ThreadingHTTPServer, app: App) -> str:
    port = httpd.server_address[1]
    return f"http://127.0.0.1:{port}/#t={app.token}"


def watchdog(httpd: ThreadingHTTPServer, app: App, idle: float = 45.0) -> None:
    """Stop the server once the interface has been closed (no pings) and nothing runs."""
    def loop():
        while True:
            time.sleep(5)
            if time.time() - app.last_ping > idle and not app.busy():
                httpd.shutdown()
                return
    threading.Thread(target=loop, daemon=True, name="voidsweep-watchdog").start()
