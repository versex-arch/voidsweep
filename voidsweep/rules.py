"""Where junk lives on each operating system.

A *rule* is a small generator that yields :class:`Candidate` objects. Rules
only *propose*; the scanner measures, age-filters, de-duplicates and runs
every candidate through :class:`voidsweep.safety.Guard` before it reaches the
user.
"""

from __future__ import annotations

import fnmatch
import ntpath
import os
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence

from . import lnk
from .platforms import Env, LINUX, MACOS, WINDOWS


@dataclass
class Candidate:
    path: Path
    marker: str
    reason: str
    params: Dict[str, object] = field(default_factory=dict)
    min_age_days: float = 0.0
    needs_admin: bool = False
    owner_check: bool = False  # only offer if owned by the current user (shared /tmp etc.)


@dataclass
class Rule:
    name: str
    marker: str
    collect: Callable[[], Iterator[Candidate]]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def ls(path: Path) -> List[os.DirEntry]:
    try:
        with os.scandir(path) as it:
            return list(it)
    except OSError:
        return []


def is_dir(e: os.DirEntry) -> bool:
    try:
        return e.is_dir(follow_symlinks=False)
    except OSError:
        return False


def is_regular_or_dir(e: os.DirEntry) -> bool:
    try:
        st = e.stat(follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)


def children(root: Path, marker: str, reason: str, *, params: Optional[dict] = None,
             min_age: float = 0, skip: Sequence[str] = (), only: Optional[Sequence[str]] = None,
             needs_admin: bool = False, owner_check: bool = False,
             label: Optional[Callable[[str], dict]] = None) -> Iterator[Candidate]:
    """Each direct child of *root* becomes a candidate (sockets/devices are ignored)."""
    for e in ls(root):
        if any(fnmatch.fnmatch(e.name, s) for s in skip):
            continue
        if only is not None and not any(fnmatch.fnmatch(e.name.lower(), o) for o in only):
            continue
        if not is_regular_or_dir(e):
            continue
        p = dict(params or {})
        if label:
            p.update(label(e.name))
        yield Candidate(Path(e.path), marker, reason, p, min_age, needs_admin, owner_check)


def single(path: Path, marker: str, reason: str, params: Optional[dict] = None,
           min_age: float = 0, needs_admin: bool = False) -> Iterator[Candidate]:
    if os.path.lexists(path):
        yield Candidate(path, marker, reason, dict(params or {}), min_age, needs_admin)


def walk_files(root: Path, max_depth: int = 6) -> Iterator[os.DirEntry]:
    stack = [(root, 0)]
    while stack:
        d, depth = stack.pop()
        for e in ls(d):
            if is_dir(e):
                if depth < max_depth:
                    stack.append((Path(e.path), depth + 1))
            else:
                yield e


def prettify(name: str) -> str:
    """Turn ``com.spotify.client`` into ``spotify.client`` and similar."""
    for prefix in ("com.", "org.", "net.", "io.", "dev.", "app."):
        if name.lower().startswith(prefix) and name.count(".") >= 2:
            return name[len(prefix):]
    return name


# ---------------------------------------------------------------------------
# Browsers
# ---------------------------------------------------------------------------

# name -> per-OS list of "User Data" style roots (relative to the OS base dir)
_CHROMIUM = {
    "Google Chrome": {WINDOWS: ["Google/Chrome/User Data"], MACOS: ["Google/Chrome"],
                      LINUX: ["google-chrome"]},
    "Chromium": {WINDOWS: ["Chromium/User Data"], MACOS: ["Chromium"], LINUX: ["chromium"]},
    "Microsoft Edge": {WINDOWS: ["Microsoft/Edge/User Data"], MACOS: ["Microsoft Edge"],
                       LINUX: ["microsoft-edge"]},
    "Brave": {WINDOWS: ["BraveSoftware/Brave-Browser/User Data"],
              MACOS: ["BraveSoftware/Brave-Browser"], LINUX: ["BraveSoftware/Brave-Browser"]},
    "Vivaldi": {WINDOWS: ["Vivaldi/User Data"], MACOS: ["Vivaldi"], LINUX: ["vivaldi"]},
    "Yandex Browser": {WINDOWS: ["Yandex/YandexBrowser/User Data"],
                       MACOS: ["Yandex/YandexBrowser"], LINUX: ["yandex-browser"]},
    "Opera": {WINDOWS: ["Opera Software/Opera Stable", "Opera Software/Opera GX Stable"],
              MACOS: ["com.operasoftware.Opera"], LINUX: ["opera"]},
}

# OS-level cache roots that belong wholly to a browser (macOS/Linux keep them apart).
_BROWSER_CACHE_ROOTS = {
    "Google Chrome": {MACOS: ["Google/Chrome"], LINUX: ["google-chrome"]},
    "Chromium": {MACOS: ["Chromium"], LINUX: ["chromium"]},
    "Microsoft Edge": {MACOS: ["Microsoft Edge"], LINUX: ["microsoft-edge"]},
    "Brave": {MACOS: ["BraveSoftware/Brave-Browser"], LINUX: ["BraveSoftware/Brave-Browser"]},
    "Vivaldi": {MACOS: ["Vivaldi"], LINUX: ["vivaldi"]},
    "Yandex Browser": {MACOS: ["Yandex/YandexBrowser"], LINUX: ["yandex-browser"]},
    "Opera": {MACOS: ["com.operasoftware.Opera"], LINUX: ["opera"],
              WINDOWS: ["Opera Software/Opera Stable/Cache",
                        "Opera Software/Opera GX Stable/Cache"]},
    "Firefox": {MACOS: ["Firefox"], LINUX: ["mozilla/firefox"]},
    "Safari": {MACOS: ["com.apple.Safari"]},
}

_PROFILE_CACHE_DIRS = ["Cache", "Code Cache", "GPUCache", "DawnCache", "DawnGraphiteCache",
                       "DawnWebGPUCache", "Media Cache", "Application Cache",
                       "Service Worker/CacheStorage", "Service Worker/ScriptCache"]
_USERDATA_CACHE_DIRS = ["ShaderCache", "GrShaderCache", "GraphiteDawnCache", "component_crx_cache"]


def _chromium_bases(env: Env) -> List[Path]:
    if env.os == WINDOWS:
        return [env.localappdata, env.appdata]
    if env.os == MACOS:
        return [env.library / "Application Support"]
    return [env.xdg_config]


def _cache_base(env: Env) -> Path:
    if env.os == WINDOWS:
        return env.localappdata
    if env.os == MACOS:
        return env.library / "Caches"
    return env.xdg_cache


def _profiles(user_data: Path) -> List[Path]:
    # Opera keeps the profile in the root itself.
    out = [user_data] if (user_data / "Preferences").exists() else []
    for e in ls(user_data):
        if is_dir(e) and (e.name in ("Default", "Guest Profile", "System Profile")
                          or e.name.startswith("Profile ")):
            out.append(Path(e.path))
    return out


def browser_cache_rules(env: Env) -> Iterator[Candidate]:
    cache_base = _cache_base(env)
    for browser, per_os in _BROWSER_CACHE_ROOTS.items():
        for rel in per_os.get(env.os, []):
            yield from single(cache_base / rel, "CCH-02", "browser_cache", {"app": browser})
    for browser, per_os in _CHROMIUM.items():
        for base in _chromium_bases(env):
            for rel in per_os.get(env.os, []):
                ud = base / rel
                if not ud.is_dir():
                    continue
                for name in _USERDATA_CACHE_DIRS:
                    yield from single(ud / name, "CCH-02", "browser_cache", {"app": browser})
                for prof in _profiles(ud):
                    for name in _PROFILE_CACHE_DIRS:
                        yield from single(prof / name, "CCH-02", "browser_cache",
                                          {"app": browser})
    # Firefox profile caches on Windows live under Local.
    if env.os == WINDOWS:
        root = env.localappdata / "Mozilla/Firefox/Profiles"
        for e in ls(root):
            if is_dir(e):
                yield from single(Path(e.path) / "cache2", "CCH-02", "browser_cache",
                                  {"app": "Firefox"})
                yield from single(Path(e.path) / "startupCache", "CCH-02", "browser_cache",
                                  {"app": "Firefox"})


def _firefox_profile_roots(env: Env) -> List[Path]:
    if env.os == WINDOWS:
        return [env.appdata / "Mozilla/Firefox/Profiles"]
    if env.os == MACOS:
        return [env.library / "Application Support/Firefox/Profiles"]
    return [env.home / ".mozilla/firefox", env.home / "snap/firefox/common/.mozilla/firefox",
            env.home / ".var/app/org.mozilla.firefox/.mozilla/firefox"]


def cookie_rules(env: Env) -> Iterator[Candidate]:
    for browser, per_os in _CHROMIUM.items():
        for base in _chromium_bases(env):
            for rel in per_os.get(env.os, []):
                ud = base / rel
                for prof in _profiles(ud) if ud.is_dir() else []:
                    for name in ("Network/Cookies", "Network/Cookies-journal", "Cookies",
                                 "Cookies-journal"):
                        yield from single(prof / name, "CKE-01", "cookies", {"app": browser})
    for root in _firefox_profile_roots(env):
        for e in ls(root):
            if is_dir(e):
                for name in ("cookies.sqlite", "cookies.sqlite-wal", "cookies.sqlite-shm"):
                    yield from single(Path(e.path) / name, "CKE-01", "cookies",
                                      {"app": "Firefox"})


# ---------------------------------------------------------------------------
# Caches
# ---------------------------------------------------------------------------

_ELECTRON_CACHE_NAMES = {"Cache", "Code Cache", "GPUCache", "DawnCache", "DawnGraphiteCache",
                         "DawnWebGPUCache", "GrShaderCache", "ShaderCache", "CachedData",
                         "CachedExtensionVSIXs", "Crashpad"}
_ELECTRON_SKIP_APPS = {"Microsoft", "Google", "Mozilla", "Packages", "Temp", "Programs",
                       "BraveSoftware", "Yandex", "Vivaldi", "Chromium", "Opera Software"}


def electron_cache_rules(env: Env) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        bases = [env.appdata, env.localappdata]
    elif env.os == MACOS:
        bases = [env.library / "Application Support"]
    else:
        bases = [env.xdg_config]
    for base in bases:
        for app in ls(base):
            if not is_dir(app) or app.name in _ELECTRON_SKIP_APPS or app.name.startswith("com.apple."):
                continue
            levels = [(Path(app.path), app.name)]
            for sub in ls(app.path):
                if is_dir(sub) and sub.name not in _ELECTRON_CACHE_NAMES:
                    levels.append((Path(sub.path), app.name))
            for folder, app_name in levels:
                for e in ls(folder):
                    if is_dir(e) and e.name in _ELECTRON_CACHE_NAMES:
                        reason = "crash_dump" if e.name == "Crashpad" else "electron_cache"
                        marker = "DMP-01" if e.name == "Crashpad" else "CCH-01"
                        yield Candidate(Path(e.path), marker, reason,
                                        {"app": app_name, "name": e.name},
                                        min_age_days=1 if marker == "DMP-01" else 0)


def app_cache_rules(env: Env) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        la = env.localappdata
        for rel, app in [("Microsoft/Windows/INetCache", "Internet Explorer / WinINet"),
                         ("D3DSCache", "DirectX"), ("NVIDIA/DXCache", "NVIDIA"),
                         ("NVIDIA/GLCache", "NVIDIA"), ("NVIDIA Corporation/NV_Cache", "NVIDIA"),
                         ("AMD/DxCache", "AMD"), ("AMD/GLCache", "AMD"), ("AMD/VkCache", "AMD"),
                         ("Intel/ShaderCache", "Intel"), ("Steam/htmlcache", "Steam"),
                         ("Spotify/Data", "Spotify"), ("Microsoft/Teams/Cache", "Teams")]:
            yield from single(la / rel, "CCH-01", "app_cache", {"app": app})
    elif env.os == MACOS:
        yield from children(env.library / "Caches", "CCH-01", "app_cache",
                            skip=["com.apple.*", "CloudKit", "FamilyCircle", "GeoServices",
                                  "familycircled", "com.crashlytics.data",
                                  "storeassetd", ".*"],
                            label=lambda n: {"app": prettify(n)})
    else:
        yield from children(env.xdg_cache, "CCH-01", "app_cache",
                            skip=["thumbnails", "fontconfig", "ibus", "dconf", "keyring-*",
                                  "gnome-software", "flatpak", "sessions", ".*"],
                            label=lambda n: {"app": n})


def thumbnail_rules(env: Env) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        explorer = env.localappdata / "Microsoft/Windows/Explorer"
        yield from children(explorer, "CCH-03", "thumb_cache", params={"app": "Windows Explorer"},
                            only=["thumbcache_*.db", "iconcache_*.db"])
    elif env.os == LINUX:
        yield from single(env.xdg_cache / "thumbnails", "CCH-03", "thumb_cache",
                          {"app": "freedesktop"})
        yield from single(env.home / ".thumbnails", "CCH-03", "thumb_cache",
                          {"app": "freedesktop"})


def package_cache_rules(env: Env) -> Iterator[Candidate]:
    cb = _cache_base(env)
    items = [("npm", env.home / ".npm/_cacache"), ("Cargo", env.home / ".cargo/registry/cache"),
             ("Bun", env.home / ".bun/install/cache")]
    if env.os == WINDOWS:
        la = env.localappdata
        items += [("pip", la / "pip/cache"), ("npm", la / "npm-cache/_cacache"),
                  ("Yarn", la / "Yarn/Cache"), ("Go", la / "go-build"),
                  ("NuGet", la / "NuGet/v3-cache"), ("NuGet", la / "NuGet/plugins-cache")]
    else:
        items += [("pip", cb / "pip"), ("Yarn", cb / ("Yarn" if env.os == MACOS else "yarn")),
                  ("Go", cb / "go-build"), ("Homebrew", cb / "Homebrew"),
                  ("pnpm", cb / "pnpm"), ("Poetry", cb / "pypoetry/cache"),
                  ("uv", cb / "uv")]
    for app, path in items:
        yield from single(path, "CCH-04", "pkg_cache", {"app": app})


# ---------------------------------------------------------------------------
# Temp, logs, dumps, updates
# ---------------------------------------------------------------------------

_TMP_SKIP = [".X11-unix", ".ICE-unix", ".font-unix", ".XIM-unix", ".Test-unix", ".X*-lock",
             "systemd-private-*", "snap-private-tmp", "tmux-*", "ssh-*", "pulse-*",
             "*.sock", "com.apple.launchd*", "powerlog", "claude-*", ".vbox-*", "orbit-*",
             "dbus-*", "gdm*", "lightdm*", "sddm*", "kdeinit*", ".com.google.Chrome*",
             "runtime-*", "*.pid", "*.socket"]


def temp_rules(env: Env) -> Iterator[Candidate]:
    for tdir in env.temp_dirs():
        if not tdir.is_dir():
            continue
        admin = env.os == WINDOWS and tdir == env.systemroot / "Temp"
        yield from children(tdir, "TMP-01", "temp_dir", params={"root": str(tdir)},
                            min_age=1, skip=_TMP_SKIP, needs_admin=admin,
                            owner_check=env.os != WINDOWS)


def _log_files(folder: Path, min_age: float, needs_admin=False) -> Iterator[Candidate]:
    for e in walk_files(folder, max_depth=3):
        n = e.name.lower()
        if (n.endswith((".log", ".log.old", ".old", ".gz", ".bak", ".etl", ".txt"))
                or fnmatch.fnmatch(n, "*.log.[0-9]*") or fnmatch.fnmatch(n, "*.[0-9]")):
            yield Candidate(Path(e.path), "LOG-01", "old_log", {}, min_age, needs_admin)


def log_rules(env: Env) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        for base in (env.appdata, env.localappdata):
            for app in ls(base):
                if not is_dir(app) or app.name in ("Packages", "Microsoft", "Temp"):
                    continue
                for sub in [app] + [s for s in ls(app.path) if is_dir(s)]:
                    for e in ls(sub.path):
                        if is_dir(e) and e.name.lower() in ("log", "logs"):
                            yield from _log_files(Path(e.path), 14)
        yield from _log_files(env.systemroot / "Logs/CBS", 14, needs_admin=True)
    elif env.os == MACOS:
        yield from children(env.library / "Logs", "LOG-01", "old_log", min_age=14,
                            skip=["DiagnosticReports", "CoreSimulator"])
    else:
        yield from single(env.home / ".xsession-errors.old", "LOG-01", "old_log", min_age=1)
        for app in ls(env.xdg_config):
            if is_dir(app):
                for e in ls(app.path):
                    if is_dir(e) and e.name.lower() in ("log", "logs"):
                        yield from _log_files(Path(e.path), 14)
        for e in walk_files(Path("/var/log"), max_depth=2):
            n = e.name
            if n.endswith((".gz", ".old")) or fnmatch.fnmatch(n, "*.[0-9]"):
                yield Candidate(Path(e.path), "LOG-01", "old_log", {}, 7, needs_admin=True)


def dump_rules(env: Env) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        la, pd, sr = env.localappdata, env.programdata, env.systemroot
        yield from children(la / "CrashDumps", "DMP-01", "crash_dump", min_age=1)
        for base, admin in ((la, False), (pd, True)):
            for q in ("ReportArchive", "ReportQueue", "Temp"):
                yield from children(base / "Microsoft/Windows/WER" / q, "DMP-01", "crash_dump",
                                    min_age=1, needs_admin=admin)
        yield from children(sr / "Minidump", "DMP-01", "crash_dump", min_age=1, needs_admin=True)
        yield from single(sr / "MEMORY.DMP", "DMP-01", "crash_dump", min_age=1, needs_admin=True)
        yield from children(sr / "LiveKernelReports", "DMP-01", "crash_dump", min_age=1,
                            needs_admin=True, only=["*.dmp"])
    elif env.os == MACOS:
        yield from children(env.library / "Logs/DiagnosticReports", "DMP-01", "crash_dump",
                            min_age=1)
        yield from children(Path("/Library/Logs/DiagnosticReports"), "DMP-01", "crash_dump",
                            min_age=1, needs_admin=True)
    else:
        yield from children(Path("/var/crash"), "DMP-01", "crash_dump", min_age=1,
                            needs_admin=True)
        yield from children(Path("/var/lib/systemd/coredump"), "DMP-01", "crash_dump",
                            min_age=1, needs_admin=True)


def update_rules(env: Env) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        yield from children(env.systemroot / "SoftwareDistribution/Download", "UPD-01",
                            "update_leftover", params={"app": "Windows Update"}, min_age=3,
                            needs_admin=True)
    elif env.os == MACOS:
        yield from children(Path("/Library/Updates"), "UPD-01", "update_leftover",
                            params={"app": "macOS"}, min_age=7, needs_admin=True,
                            skip=["*.plist"])
    else:
        yield from children(Path("/var/cache/apt/archives"), "UPD-01", "update_leftover",
                            params={"app": "apt"}, only=["*.deb"], needs_admin=True)
        yield from children(Path("/var/cache/pacman/pkg"), "UPD-01", "update_leftover",
                            params={"app": "pacman"}, min_age=14, needs_admin=True)


# ---------------------------------------------------------------------------
# Broken links
# ---------------------------------------------------------------------------

def _lnk_folders(env: Env) -> List[tuple]:
    sm = "Microsoft/Windows/Start Menu/Programs"
    public = Path(env.var("PUBLIC", "C:/Users/Public"))
    out = [(env.desktop(), 0), (public / "Desktop", 0), (env.appdata / sm, 4),
           (env.programdata / sm, 4),
           (env.appdata / "Microsoft/Internet Explorer/Quick Launch", 3)]
    onedrive = env.var("OneDrive")
    if onedrive:
        out.append((Path(onedrive) / "Desktop", 0))
    return out


def broken_lnk_rules(env: Env, exists=os.path.exists) -> Iterator[Candidate]:
    if env.os != WINDOWS:
        return
    for folder, depth in _lnk_folders(env):
        for e in walk_files(folder, max_depth=depth):
            if not e.name.lower().endswith(".lnk"):
                continue
            target = lnk.read_target_file(e.path)
            if not target:
                continue
            drive = ntpath.splitdrive(target)[0]
            # A missing USB stick is not a broken shortcut.
            if drive and not exists(drive + "\\"):
                continue
            if not exists(target):
                admin = folder == env.programdata / "Microsoft/Windows/Start Menu/Programs"
                yield Candidate(Path(e.path), "LNK-01", "broken_lnk", {"target": target},
                                needs_admin=admin)


def _desktop_exec(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read(65536)
    except OSError:
        return None
    in_entry, try_exec, exec_ = False, None, None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            in_entry = line == "[Desktop Entry]"
            continue
        if not in_entry or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k == "TryExec":
            try_exec = v.strip()
        elif k == "Exec":
            exec_ = v.strip()
        elif k == "Type" and v.strip() != "Application":
            return None
    cmd = try_exec or exec_
    if not cmd:
        return None
    try:
        import shlex
        tokens = shlex.split(cmd)
    except ValueError:
        tokens = cmd.replace('"', " ").split()
    # skip "env VAR=1 prog" wrappers
    while tokens and (tokens[0] == "env" or "=" in tokens[0]):
        tokens.pop(0)
    return tokens[0] if tokens else None


def broken_desktop_rules(env: Env) -> Iterator[Candidate]:
    if env.os != LINUX:
        return
    path_dirs = env.var("PATH", "/usr/bin:/bin").split(os.pathsep)
    for folder in (env.xdg_data / "applications", env.desktop()):
        for e in ls(folder):
            if not e.name.endswith(".desktop") or not e.is_file():
                continue
            prog = _desktop_exec(e.path)
            if not prog or prog.startswith("%"):
                continue
            if os.path.isabs(prog):
                ok = os.path.exists(prog)
            else:
                ok = shutil.which(prog, path=os.pathsep.join(path_dirs)) is not None
            if not ok:
                yield Candidate(Path(e.path), "LNK-01", "broken_desktop", {"target": prog})


def broken_symlink_rules(env: Env) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        return
    folders = [(env.home / ".local/bin", 0), (env.home / "bin", 0), (env.desktop(), 0),
               (env.xdg_data / "applications", 0), (env.xdg_config / "autostart", 0)]
    for folder, _ in folders:
        for e in ls(folder):
            if e.is_symlink() and not os.path.exists(e.path):
                try:
                    target = os.readlink(e.path)
                except OSError:
                    target = "?"
                yield Candidate(Path(e.path), "LNK-02", "broken_symlink", {"target": target})


# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------

INSTALLER_EXT = (".exe", ".msi", ".msix", ".msixbundle", ".appx", ".dmg", ".pkg", ".mpkg",
                 ".deb", ".rpm", ".appimage", ".run", ".flatpakref", ".snap")


def installer_rules(env: Env) -> Iterator[Candidate]:
    for e in ls(env.downloads()):
        if e.is_file(follow_symlinks=False) and e.name.lower().endswith(INSTALLER_EXT):
            yield Candidate(Path(e.path), "DL-01", "old_installer", {"name": e.name}, 30)


# ---------------------------------------------------------------------------

def build_rules(env: Env) -> List[Rule]:
    """Ordered: the first rule to claim a path wins, so specific rules go first."""
    from .orphans import orphan_rules  # local import: orphans imports helpers from here

    def r(name, marker, fn):
        return Rule(name, marker, lambda: fn(env))

    return [
        r("browser-cache", "CCH-02", browser_cache_rules),
        r("cookies", "CKE-01", cookie_rules),
        r("thumbnails", "CCH-03", thumbnail_rules),
        r("package-caches", "CCH-04", package_cache_rules),
        r("crash-dumps", "DMP-01", dump_rules),
        r("updates", "UPD-01", update_rules),
        r("temp", "TMP-01", temp_rules),
        r("electron-caches", "CCH-01", electron_cache_rules),
        r("app-caches", "CCH-01", app_cache_rules),
        r("logs", "LOG-01", log_rules),
        r("broken-lnk", "LNK-01", broken_lnk_rules),
        r("broken-desktop", "LNK-01", broken_desktop_rules),
        r("broken-symlinks", "LNK-02", broken_symlink_rules),
        r("installers", "DL-01", installer_rules),
        r("orphans", "ORP-01", orphan_rules),
    ]
