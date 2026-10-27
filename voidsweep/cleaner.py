"""Removes the findings the user approved — carefully.

Every item is re-checked right before removal: still allowed by the guard,
still there, and not modified since the scan. Anything that fails a check is
skipped and reported, never forced.
"""

from __future__ import annotations

import errno
import os
import shutil
import stat
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from . import trash
from .platforms import is_within, norm
from .safety import Guard
from .scanner import Finding

TRASH, PERMANENT = "trash", "permanent"


@dataclass
class Result:
    id: int
    path: str
    marker: str
    size: int
    status: str          # ok | missing | changed | protected | permission | in_use | error
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("ok", "missing")

    def to_dict(self) -> dict:
        return {"id": self.id, "path": self.path, "marker": self.marker, "size": self.size,
                "status": self.status, "message": self.message}


def _classify(exc: BaseException) -> str:
    winerr = getattr(exc, "winerror", None)
    if winerr in (32, 33):  # ERROR_SHARING_VIOLATION / ERROR_LOCK_VIOLATION
        return "in_use"
    if isinstance(exc, PermissionError) or getattr(exc, "errno", None) in (errno.EACCES,
                                                                         errno.EPERM):
        return "permission"
    if getattr(exc, "errno", None) == errno.EBUSY:
        return "in_use"
    return "error"


def _remove_permanently(path: str, is_dir: bool) -> List[str]:
    errors: List[str] = []
    if not is_dir:
        os.unlink(path)
        return errors

    def onexc(func, p, exc):
        # Read-only files on Windows: clear the flag and retry once.
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError as e:
            errors.append(f"{p}: {e.strerror or e}")

    try:
        shutil.rmtree(path, onexc=onexc)  # Python 3.12+
    except TypeError:
        shutil.rmtree(path, onerror=lambda f, p, ei: onexc(f, p, ei[1]))
    return errors


def clean(findings: Iterable[Finding], guard: Guard, mode: str = TRASH,
          progress: Optional[Callable[[int, int, str], None]] = None,
          dry_run: bool = False) -> List[Result]:
    items = sorted(findings, key=lambda f: len(norm(f.path)))
    done_dirs: List[str] = []
    results: List[Result] = []
    total = len(items)
    for i, f in enumerate(items, 1):
        if progress:
            progress(i, total, f.path)
        res = Result(f.id, f.path, f.marker, f.size, "ok")
        results.append(res)
        if any(is_within(f.path, d) for d in done_dirs):
            res.status, res.message = "missing", "removed with its parent folder"
            continue
        if not guard.allows(f.path):
            res.status = "protected"
            continue
        try:
            st = os.lstat(f.path)
        except FileNotFoundError:
            res.status = "missing"
            continue
        except OSError as exc:
            res.status, res.message = _classify(exc), str(exc)
            continue
        if abs(st.st_mtime - f.self_mtime) > 1e-3:
            res.status = "changed"
            continue
        is_dir = stat.S_ISDIR(st.st_mode)
        if dry_run:
            continue
        try:
            if mode == TRASH:
                trash.send(f.path)
            else:
                errs = _remove_permanently(f.path, is_dir)
                if errs:
                    res.status, res.message = "error", "; ".join(errs[:3])
        except trash.TrashError as exc:
            res.status, res.message = "error", str(exc)
        except OSError as exc:
            res.status, res.message = _classify(exc), exc.strerror or str(exc)
        if res.ok and is_dir:
            done_dirs.append(f.path)
    return results
