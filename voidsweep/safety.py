"""Hard safety rails.

No matter what a rule produces, these checks decide whether a path may ever
be offered for deletion. They are deliberately conservative: a rule bug
should result in a missed junk file, never in a lost photo.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Set

from .platforms import Env, LINUX, MACOS, WINDOWS, is_within, norm

# Folders whose *contents* may be junk but which must never be removed
# themselves (and nothing above them either).
_POSIX_SYSTEM = ["/", "/bin", "/sbin", "/usr", "/etc", "/lib", "/lib64", "/opt", "/var",
                 "/home", "/root", "/boot", "/dev", "/proc", "/sys", "/run", "/srv", "/mnt",
                 "/media", "/tmp", "/var/tmp", "/var/log", "/var/cache", "/snap",
                 "/System", "/Library", "/Applications", "/Users", "/Volumes", "/private",
                 "/private/var", "/private/tmp", "/private/var/tmp", "/cores"]

# Never descend into or delete anything under these (relative to home) —
# real user data lives here even if a rule thinks otherwise.
_NEVER_TOUCH_HOME = [
    "Library/Mobile Documents",          # iCloud Drive
    "Library/Application Support/MobileSync",  # iPhone backups
    "Library/Containers",                # sandboxed apps (TCC-protected)
    "Library/Group Containers",
    "Library/Mail",
    "Library/Messages",
    "Library/Keychains",
    "Library/Photos",
    "Pictures/Photos Library.photoslibrary",
    ".ssh", ".gnupg", ".password-store",
    ".local/share/keyrings",
    "AppData/Roaming/Microsoft/Credentials",
    "AppData/Local/Microsoft/Credentials",
    "AppData/Roaming/Microsoft/Protect",
]


def protected_paths(env: Env) -> Set[str]:
    """Exact paths that may never be deleted themselves."""
    p: List[Path] = [env.home, env.home.parent]
    p += env.user_folders()
    p += env.temp_dirs()
    if env.os == WINDOWS:
        sr = env.systemroot
        p += [sr, sr / "System32", sr / "SysWOW64", sr / "Temp", sr / "SoftwareDistribution",
              sr / "SoftwareDistribution" / "Download", env.programdata,
              Path(env.var("ProgramFiles", "C:/Program Files")),
              Path(env.var("ProgramFiles(x86)", "C:/Program Files (x86)")),
              env.appdata, env.localappdata, env.appdata.parent,
              env.localappdata / "Temp", env.localappdata / "Programs",
              env.localappdata / "Packages", env.localappdata / "Microsoft",
              env.appdata / "Microsoft"]
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            p.append(Path(f"{letter}:/"))
    else:
        p += [Path(x) for x in _POSIX_SYSTEM]
    if env.os == MACOS:
        lib = env.library
        p += [lib, lib / "Caches", lib / "Logs", lib / "Preferences",
              lib / "Application Support", lib / "Saved Application State",
              lib / "Logs" / "DiagnosticReports", Path("/Library/Caches"),
              Path("/Library/Logs"), Path("/Library/Logs/DiagnosticReports")]
    if env.os == LINUX:
        p += [env.xdg_cache, env.xdg_config, env.xdg_data, env.home / ".local",
              env.home / ".local" / "bin", env.home / ".var", env.home / ".var" / "app",
              Path("/var/crash"), Path("/var/cache/apt"), Path("/var/cache/apt/archives")]
    return {norm(x) for x in p}


def never_touch_roots(env: Env) -> List[str]:
    return [norm(env.home / rel) for rel in _NEVER_TOUCH_HOME]


class Guard:
    """Answers one question: may this path be offered for deletion?"""

    def __init__(self, env: Env, ignore: Iterable[str] = ()):
        self.env = env
        self.protected = protected_paths(env)
        self.never = never_touch_roots(env)
        self.ignore = [norm(i) for i in ignore if i]

    def allows(self, path) -> bool:
        n = norm(path)
        if n in self.protected:
            return False
        # Anything that *contains* a protected path (e.g. the home dir's parent).
        for prot in self.protected:
            if prot != n and is_within(prot, n):
                return False
        for root in self.never:
            if is_within(n, root) or is_within(root, n):
                return False
        for ig in self.ignore:
            if is_within(n, ig):
                return False
        # Paths must be at least two levels deep ("/a" or "C:\\a" are too close to the root).
        parts = Path(n).parts
        if len(parts) < 3:
            return False
        return True

    def is_ignored(self, path) -> bool:
        n = norm(path)
        return any(is_within(n, ig) for ig in self.ignore)


def owned_by_user(st: os.stat_result, env: Env) -> bool:
    """On POSIX, only offer files the current user owns (we could not delete others anyway)."""
    if env.uid is None or env.os == WINDOWS:
        return True
    return getattr(st, "st_uid", env.uid) == env.uid or env.uid == 0
