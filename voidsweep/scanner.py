"""The scan engine: runs rules, walks drives, measures and filters findings."""

from __future__ import annotations

import os
import re
import stat
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from .markers import MARKERS, render_reason
from .platforms import Env, MACOS, WINDOWS, norm
from .rules import Candidate, Rule, build_rules
from .safety import Guard, owned_by_user

Progress = Callable[[dict], None]


@dataclass
class Finding:
    id: int
    path: str
    kind: str            # file | dir | link
    size: int
    files: int
    mtime: float         # newest modification time (whole tree for directories)
    self_mtime: float    # lstat mtime of the item itself, used to detect changes
    marker: str
    reason: str
    params: Dict[str, object]
    needs_admin: bool = False
    covered_by: Optional[int] = None

    def to_dict(self) -> dict:
        m = MARKERS[self.marker]
        return {
            "id": self.id, "path": self.path,
            "name": re.split(r"[\\/]", self.path.rstrip("\\/"))[-1] or self.path,
            "kind": self.kind, "size": self.size, "files": self.files, "mtime": self.mtime,
            "marker": self.marker, "risk": m.risk,
            "reason": {lang: render_reason(self.reason, self.params, lang) for lang in ("ru", "en")},
            "needs_admin": self.needs_admin, "covered_by": self.covered_by,
            "preselect": m.preselect,
        }


class Cancelled(Exception):
    pass


@dataclass
class ScanOptions:
    deep: bool = False
    drives: Sequence[str] = ()
    skip_markers: Sequence[str] = ()


_IS_REPARSE = 0x400  # FILE_ATTRIBUTE_REPARSE_POINT


def _is_reparse(st: os.stat_result) -> bool:
    return bool(getattr(st, "st_file_attributes", 0) & _IS_REPARSE)


class Scanner:
    def __init__(self, env: Optional[Env] = None, ignore: Iterable[str] = (),
                 rules: Optional[List[Rule]] = None, now: Optional[float] = None):
        self.env = env or Env.detect()
        self.guard = Guard(self.env, ignore)
        self._rules = rules
        self.now = now or time.time()
        self.findings: List[Finding] = []
        self._claimed: set = set()
        self._cancel = threading.Event()
        self._progress: Progress = lambda info: None
        self._last_emit = 0.0
        self.stats = {"scanned": 0, "found": 0, "bytes": 0}

    # ------------------------------------------------------------------ api
    def cancel(self) -> None:
        self._cancel.set()

    def run(self, options: Optional[ScanOptions] = None, progress: Optional[Progress] = None
            ) -> List[Finding]:
        options = options or ScanOptions()
        if progress:
            self._progress = progress
        rules = self._rules if self._rules is not None else build_rules(self.env)
        rules = [r for r in rules if r.marker not in options.skip_markers]
        total_steps = len(rules) + (len(options.drives) if options.deep else 0)
        step = 0
        try:
            for rule in rules:
                step += 1
                self._emit("rules", rule.name, step, total_steps, force=True)
                for cand in rule.collect():
                    self._check_cancel()
                    self._consider(cand)
            if options.deep:
                from .deep import deep_candidates
                for drive in options.drives:
                    step += 1
                    self._emit("deep", drive, step, total_steps, force=True)
                    for cand in deep_candidates(self.env, drive, self.guard, self._tick,
                                                self._cancel):
                        self._consider(cand)
        except Cancelled:
            self._emit("cancelled", "", step, total_steps, force=True)
            raise
        self._link_coverage()
        self._emit("done", "", total_steps, total_steps, force=True)
        return self.findings

    # ------------------------------------------------------------ internals
    def _check_cancel(self) -> None:
        if self._cancel.is_set():
            raise Cancelled()

    def _tick(self, current: str) -> None:
        self.stats["scanned"] += 1
        if self.stats["scanned"] % 256 == 0:
            self._check_cancel()
            self._emit("walk", current)

    def _emit(self, phase: str, detail: str, step: int = 0, total: int = 0,
              force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_emit < 0.12:
            return
        self._last_emit = now
        info = {"phase": phase, "detail": detail, **self.stats}
        if total:
            info.update(step=step, total=total)
        try:
            self._progress(info)
        except Exception:
            pass

    def _claimed_by_ancestor(self, key: str) -> bool:
        if key in self._claimed:
            return True
        p = os.path.dirname(key)
        while p and p not in ("/", "\\") and len(p) > 3:
            if p in self._claimed:
                return True
            parent = os.path.dirname(p)
            if parent == p:
                break
            p = parent
        return False

    def _consider(self, cand: Candidate) -> None:
        key = norm(cand.path)
        if self._claimed_by_ancestor(key) or not self.guard.allows(cand.path):
            return
        try:
            st = os.lstat(cand.path)
        except OSError:
            return
        if cand.owner_check and not owned_by_user(st, self.env):
            return
        measured = self._measure(cand.path, st)
        if measured is None:
            return
        kind, size, files, newest = measured
        age_days = max(0.0, (self.now - newest) / 86400)
        if age_days < cand.min_age_days:
            return
        params = dict(cand.params)
        params.setdefault("name", os.path.basename(str(cand.path)))
        params["age_days"] = age_days
        self._claimed.add(key)
        f = Finding(len(self.findings), str(cand.path), kind, size, files, newest, st.st_mtime,
                    cand.marker, cand.reason, params, cand.needs_admin)
        self.findings.append(f)
        self.stats["found"] += 1
        self.stats["bytes"] += size
        self._emit("found", str(cand.path))

    def _measure(self, path, st: os.stat_result):
        if stat.S_ISLNK(st.st_mode) or _is_reparse(st) and not stat.S_ISREG(st.st_mode):
            return "link", st.st_size if stat.S_ISLNK(st.st_mode) else 0, 1, st.st_mtime
        if stat.S_ISREG(st.st_mode):
            return "file", st.st_size, 1, st.st_mtime
        if not stat.S_ISDIR(st.st_mode):
            return None
        total, files, newest = 0, 0, st.st_mtime
        stack = [str(path)]
        while stack:
            d = stack.pop()
            try:
                it = os.scandir(d)
            except OSError:
                continue
            with it:
                for e in it:
                    try:
                        est = e.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    self._tick(e.path)
                    if est.st_mtime > newest:
                        newest = est.st_mtime
                    if stat.S_ISDIR(est.st_mode) and not _is_reparse(est):
                        stack.append(e.path)
                    else:
                        files += 1
                        if stat.S_ISREG(est.st_mode):
                            total += est.st_size
        # Ignore clock-skewed future timestamps.
        newest = min(newest, self.now)
        return "dir", total, files, newest

    def _link_coverage(self) -> None:
        """Mark findings that live inside another finding (avoid double counting)."""
        by_key = {norm(f.path): f.id for f in self.findings}
        for f in self.findings:
            p = os.path.dirname(norm(f.path))
            while p:
                if p in by_key and by_key[p] != f.id:
                    f.covered_by = by_key[p]
                    break
                parent = os.path.dirname(p)
                if parent == p:
                    break
                p = parent


def summarize(findings: Sequence[Finding]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for f in findings:
        g = out.setdefault(f.marker, {"count": 0, "size": 0})
        g["count"] += 1
        if f.covered_by is None:
            g["size"] += f.size
    return out
