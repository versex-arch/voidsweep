"""Deep scan: walk a whole drive looking for junk by *name* (Thumbs.db, ._*, *.tmp…)."""

from __future__ import annotations

import os
import stat
import threading
from pathlib import Path
from typing import Callable, Iterator, Set

from .platforms import Env, LINUX, MACOS, WINDOWS, norm
from .rules import Candidate
from .safety import Guard

# Directory names never entered, wherever they appear.
SKIP_NAMES = {
    "$recycle.bin", "system volume information", "$winreagent", "$sysreset", "$windows.~bt",
    "$windows.~ws", "windows.old", "winsxs", "node_modules", ".git", ".svn", ".hg",
    ".trash", ".trashes", ".spotlight-v100", ".fseventsd", ".documentrevisions-v100",
    ".temporaryitems", "backups.backupdb", ".mobilebackups", "lost+found", "__pycache__",
    ".venv", "venv", "site-packages", ".cache", "appdata", ".npm", ".cargo", ".rustup",
    ".gradle", ".m2", ".nuget", ".local", ".var", ".wine", "snap",
}
# Bundles on macOS are opaque.
SKIP_SUFFIXES = (".app", ".photoslibrary", ".musiclibrary", ".tvlibrary", ".fcpbundle",
                 ".logicx", ".imovielibrary", ".xcarchive", ".framework", ".bundle", ".kext")

_ROOT_SKIP_POSIX = {"/proc", "/sys", "/dev", "/run", "/snap", "/boot", "/var/lib/docker",
                    "/var/lib/containers", "/var/lib/flatpak", "/var/lib/snapd", "/usr", "/bin",
                    "/sbin", "/lib", "/lib32", "/lib64", "/libx32", "/etc", "/opt", "/var/cache",
                    "/var/log", "/var/lib", "/tmp", "/var/tmp", "/System", "/private/var",
                    "/private/etc", "/private/tmp", "/cores", "/nix", "/Volumes",
                    "/System/Volumes/Data/System", "/System/Volumes/Data/private",
                    "/System/Volumes/Data/Library", "/System/Volumes/Data/Applications",
                    "/System/Volumes/Data/usr", "/System/Volumes/Data/opt",
                    "/System/Volumes/Data/Volumes", "/System/Volumes/Data/cores",
                    "/System/Volumes/Data/sw"}

TEMP_SUFFIX = (".tmp", ".temp", ".~tmp")
PARTIAL_SUFFIX = (".crdownload", ".part", ".partial", ".opdownload", ".!ut", ".!qb")
DUMP_SUFFIX = (".dmp", ".mdmp", ".hdmp")


def _root_skips(env: Env, drive: str) -> Set[str]:
    skips = set()
    if env.os == WINDOWS:
        d = drive.rstrip("\\/")
        for name in ("Windows", "Program Files", "Program Files (x86)", "ProgramData",
                     "Recovery", "PerfLogs", "MSOCache", "Intel", "AMD", "NVIDIA",
                     "$GetCurrent", "OneDriveTemp"):
            skips.add(norm(d + "\\" + name))
    else:
        skips = {norm(p) for p in _ROOT_SKIP_POSIX}
    return skips


def classify(name: str, path: str, size: int, parent: str):
    """Return (marker, reason, params, min_age) for a junk file name, or None."""
    low = name.lower()
    if low in ("thumbs.db", "ehthumbs.db", "ehthumbs_vista.db"):
        return "SYS-01", "os_junk", {"os": "Windows"}, 0
    if name == ".DS_Store":
        return "SYS-01", "os_junk", {"os": "macOS"}, 0
    if name.startswith("._") and len(name) > 2 and size <= 4 * 1024 * 1024:
        companion = name[2:]
        if not os.path.lexists(os.path.join(parent, companion)):
            return "SYS-01", "appledouble", {"target": companion}, 0
        return None
    if name.startswith("~$") and size <= 4096:
        return "TMP-02", "office_lock", {}, 1
    if low.endswith(TEMP_SUFFIX):
        return "TMP-02", "temp_name", {"pattern": "*" + low[low.rfind("."):]}, 7
    if low.endswith(PARTIAL_SUFFIX):
        return "TMP-02", "partial_download", {"pattern": "*" + low[low.rfind("."):]}, 7
    if low.endswith(DUMP_SUFFIX):
        return "DMP-01", "crash_dump", {}, 1
    return None


def deep_candidates(env: Env, drive: str, guard: Guard, tick: Callable[[str], None],
                    cancel: threading.Event) -> Iterator[Candidate]:
    root_skips = _root_skips(env, drive)
    never = set(guard.never)
    skip_names = SKIP_NAMES | ({"library"} if env.os == MACOS else set())
    check_dev = env.os != WINDOWS
    if env.os == MACOS and drive.rstrip("/") == "/System/Volumes/Data":
        # Walk the firmlinked view so paths look like /Users/…, as everywhere else.
        drive, check_dev = "/", False
    try:
        root_dev = os.stat(drive).st_dev
    except OSError:
        return
    stack = [drive]
    while stack:
        if cancel.is_set():
            return
        d = stack.pop()
        try:
            it = os.scandir(d)
        except OSError:
            continue
        with it:
            for e in it:
                tick(e.path)
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    continue
                if stat.S_ISDIR(st.st_mode):
                    low = e.name.lower()
                    if low in skip_names or low.endswith(SKIP_SUFFIXES):
                        continue
                    if getattr(st, "st_file_attributes", 0) & 0x400:  # junction/reparse
                        continue
                    if check_dev and st.st_dev != root_dev:
                        continue
                    n = norm(e.path)
                    if n in root_skips or n in never:
                        continue
                    stack.append(e.path)
                elif stat.S_ISREG(st.st_mode):
                    hit = classify(e.name, e.path, st.st_size, d)
                    if hit:
                        marker, reason, params, min_age = hit
                        yield Candidate(Path(e.path), marker, reason, params, min_age,
                                        owner_check=True)
