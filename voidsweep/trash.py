"""Move files to the system Recycle Bin / Trash without third-party dependencies.

Uses ``send2trash`` when it is installed, otherwise:

* Windows — ``SHFileOperationW`` with ``FOF_ALLOWUNDO`` (real Recycle Bin);
* macOS — rename into ``~/.Trash`` (or the volume's ``.Trashes``), falling back
  to asking Finder;
* Linux — the freedesktop.org Trash specification (works with every desktop's
  "Restore" button).
"""

from __future__ import annotations

import errno
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

from .platforms import LINUX, MACOS, WINDOWS, current_os


class TrashError(OSError):
    pass


def available() -> bool:
    return True


def send(path: str) -> None:
    try:
        from send2trash import send2trash  # type: ignore
    except ImportError:
        send2trash = None
    if send2trash is not None:
        try:
            send2trash(path)
            return
        except Exception:  # fall through to the built-in strategies
            pass
    system = current_os()
    if system == WINDOWS:
        _windows(path)
    elif system == MACOS:
        _macos(path)
    else:
        _freedesktop(path)


# ---------------------------------------------------------------- Windows
def _windows(path: str) -> None:
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT),
                    ("pFrom", wintypes.LPCWSTR), ("pTo", wintypes.LPCWSTR),
                    ("fFlags", ctypes.c_uint16), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]

    FO_DELETE = 3
    FOF_SILENT, FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_NOERRORUI = 0x4, 0x10, 0x40, 0x400
    op = SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    op.pFrom = os.path.abspath(path) + "\0"  # ctypes adds the second terminator
    op.fFlags = FOF_SILENT | FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_NOERRORUI
    rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))  # type: ignore[attr-defined]
    if rc != 0 or op.fAnyOperationsAborted:
        raise TrashError(f"Recycle Bin refused the item (code {rc})")


# ---------------------------------------------------------------- macOS
def _unique(folder: Path, name: str) -> Path:
    target = folder / name
    stem, dot, ext = name.partition(".") if not name.startswith(".") else (name, "", "")
    n = 1
    while os.path.lexists(target):
        n += 1
        target = folder / (f"{stem} {n}{dot}{ext}" if dot else f"{name} {n}")
    return target


def _macos(path: str) -> None:
    trash = Path.home() / ".Trash"
    try:
        os.rename(path, _unique(trash, os.path.basename(path)))
        return
    except OSError as exc:
        if exc.errno not in (errno.EXDEV, errno.ENOENT, errno.EPERM, errno.EACCES):
            raise TrashError(str(exc)) from exc
    script = 'tell application "Finder" to delete POSIX file "%s"' % path.replace('"', '\\"')
    rc = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=30)
    if rc.returncode != 0:
        raise TrashError(rc.stderr.decode(errors="replace").strip() or "Finder refused")


# ---------------------------------------------------------------- Linux
def _home_trash() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / "Trash"


def _mount_point(path: str) -> str:
    p = os.path.abspath(path)
    while not os.path.ismount(p):
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return p


def _trash_into(trash: Path, path: str, info_path_value: str) -> None:
    files, info = trash / "files", trash / "info"
    files.mkdir(parents=True, exist_ok=True, mode=0o700)
    info.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = os.path.basename(path.rstrip("/"))
    target = _unique(files, name)
    info_file = info / (target.name + ".trashinfo")
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    fd = os.open(info_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(f"[Trash Info]\nPath={quote(info_path_value)}\nDeletionDate={stamp}\n")
    try:
        os.rename(path, target)
    except OSError:
        info_file.unlink(missing_ok=True)
        raise


def _freedesktop(path: str) -> None:
    abspath = os.path.abspath(path)
    home_trash = _home_trash()
    try:
        _trash_into(home_trash, abspath, abspath)
        return
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise TrashError(str(exc)) from exc
    top = _mount_point(abspath)
    uid = os.getuid()
    rel = os.path.relpath(abspath, top)
    for trash in (Path(top) / ".Trash" / str(uid), Path(top) / f".Trash-{uid}"):
        if trash.parent.name == ".Trash" and not (trash.parent.is_dir()
                                                  and not trash.parent.is_symlink()):
            continue
        try:
            _trash_into(trash, abspath, rel)
            return
        except OSError:
            continue
    raise TrashError("no Trash folder available on this drive")
