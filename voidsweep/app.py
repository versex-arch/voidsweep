"""Launches the interface in its own window.

Preference order:
1. a native window via pywebview (``pip install voidsweep[window]``);
2. a Chromium-family browser in "app mode" with an isolated profile
   (Edge ships with every Windows 10/11, so this almost always works);
3. the default browser.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import List, Optional

from . import APP_NAME
from .config import data_dir
from .platforms import Env, LINUX, MACOS, WINDOWS
from .server import App, serve, url_for, watchdog

BG = "#09070D"


def _chromium_candidates(env: Env) -> List[str]:
    if env.os == WINDOWS:
        roots = [env.var("ProgramFiles", r"C:\Program Files"),
                 env.var("ProgramFiles(x86)", r"C:\Program Files (x86)"), str(env.localappdata)]
        rels = [r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe",
                r"BraveSoftware\Brave-Browser\Application\brave.exe",
                r"Chromium\Application\chrome.exe", r"Yandex\YandexBrowser\Application\browser.exe"]
        return [os.path.join(r, rel) for r in roots for rel in rels]
    if env.os == MACOS:
        apps = ["Google Chrome", "Microsoft Edge", "Brave Browser", "Chromium", "Yandex", "Vivaldi"]
        out = []
        for base in ("/Applications", str(env.home / "Applications")):
            for a in apps:
                out.append(f"{base}/{a}.app/Contents/MacOS/{a}")
        return out
    names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
             "microsoft-edge", "brave-browser", "vivaldi", "yandex-browser"]
    return [p for p in (shutil.which(n) for n in names) if p]


def find_chromium(env: Env) -> Optional[str]:
    for c in _chromium_candidates(env):
        if c and os.path.isfile(c):
            return c
    return None


def launch(port: int = 0, demo: bool = False, browser: bool = False) -> int:
    env = Env.detect()
    app = App(env, demo=demo)
    httpd = serve(app, port)
    url = url_for(httpd, app)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    if sys.stdout is not None:  # windowed builds have no console
        print(f"{APP_NAME} is running at {url.split('#')[0]}  (Ctrl+C to stop)")

    if not browser:
        try:
            import webview  # type: ignore
        except ImportError:
            webview = None
        if webview is not None:
            try:
                webview.create_window(APP_NAME, url, width=1280, height=820,
                                      min_size=(900, 600), background_color=BG)
                webview.start()
                httpd.shutdown()
                return 0
            except Exception:  # no usable native backend: fall back to a browser window
                pass

        exe = find_chromium(env)
        if exe:
            profile = data_dir(env) / "window-profile"
            profile.mkdir(parents=True, exist_ok=True)
            args = [exe, f"--app={url}", f"--user-data-dir={profile}", "--window-size=1280,820",
                    "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                    "--disable-sync", f"--class={APP_NAME}"]
            flags = 0x08000000 if env.os == WINDOWS else 0  # CREATE_NO_WINDOW
            try:
                proc = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, creationflags=flags)
                watchdog(httpd, app)
                try:
                    proc.wait()
                    # The window may hand off to an existing process; keep serving until idle.
                    server_thread.join()
                except KeyboardInterrupt:
                    httpd.shutdown()
                return 0
            except OSError:
                pass

    webbrowser.open(url)
    watchdog(httpd, app, idle=120)
    try:
        server_thread.join()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0
