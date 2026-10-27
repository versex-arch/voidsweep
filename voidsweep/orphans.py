"""Leftovers of uninstalled applications (marker ORP-01).

The idea: build an inventory of what *is* installed (registry uninstall keys,
``.app`` bundles, package managers, PATH, ``.desktop`` files…), then look at
per-app data folders and flag those that match nothing in the inventory and
have not been touched for a long time. It is a heuristic, which is why
ORP-01 is a CAUTION marker and is never pre-selected.
"""

from __future__ import annotations

import os
import plistlib
import re
import subprocess
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set

from .platforms import Env, LINUX, MACOS, WINDOWS
from .rules import Candidate, is_dir, ls

ORPHAN_MIN_AGE = 60  # days without any change inside the folder

_word = re.compile(r"[a-z0-9]+")


def normalize(name: str) -> str:
    return "".join(_word.findall(name.lower()))


class Inventory:
    """Fuzzy set of installed-software names."""

    STOP = {"the", "inc", "llc", "ltd", "corp", "corporation", "software", "app", "apps",
            "com", "org", "net", "for", "and", "update", "updater", "helper", "x64", "x86",
            "bit", "version", "edition", "free", "pro", "studio", "tools", "client",
            "desktop", "launcher", "setup", "service", "runtime"}

    def __init__(self) -> None:
        self.full: Set[str] = set()
        self.words: Set[str] = set()
        self.bundle_ids: Set[str] = set()
        self.vendors: Set[str] = set()

    def add(self, name: Optional[str]) -> None:
        if not name:
            return
        n = normalize(name)
        if len(n) >= 3:
            self.full.add(n)
        for w in _word.findall(name.lower()):
            if len(w) >= 4 and w not in self.STOP and not w.isdigit():
                self.words.add(w)

    def add_bundle(self, bundle_id: Optional[str]) -> None:
        if not bundle_id:
            return
        b = bundle_id.lower()
        self.bundle_ids.add(b)
        parts = b.split(".")
        if len(parts) >= 2:
            self.vendors.add(normalize(parts[1]))
        for p in parts[1:]:
            self.add(p)

    def matches_name(self, name: str) -> bool:
        n = normalize(name)
        if len(n) < 3:
            return True  # too short to judge -> assume installed
        if n in self.full:
            return True
        for w in self.words:
            if w in n:
                return True
        if len(n) >= 4:
            for f in self.full:
                if n in f:
                    return True
        return False

    def matches_bundle(self, bundle_id: str) -> bool:
        b = bundle_id.lower()
        for known in self.bundle_ids:
            if b.startswith(known) or known.startswith(b):
                return True
        parts = b.split(".")
        if len(parts) >= 2 and normalize(parts[1]) in self.vendors:
            return True
        return self.matches_name(".".join(parts[1:]))


def looks_like_bundle_id(name: str) -> bool:
    return name.count(".") >= 2 and re.match(r"^[A-Za-z0-9-]+(\.[A-Za-z0-9_-]+){2,}$", name) is not None


# ---------------------------------------------------------------------------
# Inventories
# ---------------------------------------------------------------------------

def windows_inventory(env: Env) -> Inventory:
    inv = Inventory()
    try:
        import winreg  # type: ignore
        roots = [(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY),
                 (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
                 (winreg.HKEY_CURRENT_USER, 0)]
        path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
        for hive, view in roots:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | view)
            except OSError:
                continue
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(key, i)
                except OSError:
                    break
                i += 1
                inv.add(sub)
                try:
                    with winreg.OpenKey(key, sub) as sk:
                        for value in ("DisplayName", "Publisher", "InstallLocation"):
                            try:
                                v, _ = winreg.QueryValueEx(sk, value)
                            except OSError:
                                continue
                            if value == "InstallLocation" and v:
                                v = os.path.basename(str(v).rstrip("\\/"))
                            inv.add(str(v))
                except OSError:
                    continue
    except ImportError:
        pass
    for base in (env.var("ProgramFiles", "C:/Program Files"),
                 env.var("ProgramFiles(x86)", "C:/Program Files (x86)"),
                 env.var("ProgramW6432", ""), str(env.localappdata / "Programs"),
                 str(env.programdata / "Microsoft/Windows/Start Menu/Programs"),
                 str(env.appdata / "Microsoft/Windows/Start Menu/Programs")):
        if not base:
            continue
        for e in ls(Path(base)):
            inv.add(e.name.rsplit(".", 1)[0] if e.name.endswith(".lnk") else e.name)
            if is_dir(e):
                for sub in ls(e.path):
                    if is_dir(sub):
                        inv.add(sub.name)
    _add_path_programs(inv, env)
    return inv


def _read_bundle(app: Path, inv: Inventory) -> None:
    inv.add(app.stem)
    try:
        with open(app / "Contents" / "Info.plist", "rb") as fh:
            info = plistlib.load(fh)
    except Exception:
        return
    inv.add_bundle(info.get("CFBundleIdentifier"))
    inv.add(info.get("CFBundleName"))
    inv.add(info.get("CFBundleExecutable"))


def _find_bundles(root: Path, depth: int) -> Iterator[Path]:
    for e in ls(root):
        if not is_dir(e):
            continue
        if e.name.endswith((".app", ".prefPane", ".appex", ".plugin", ".bundle")):
            yield Path(e.path)
        elif depth > 0:
            yield from _find_bundles(Path(e.path), depth - 1)


def macos_inventory(env: Env) -> Inventory:
    inv = Inventory()
    roots = [(Path("/Applications"), 3), (env.home / "Applications", 3),
             (Path("/System/Applications"), 2), (Path("/Library/Application Support"), 3),
             (Path("/Library/PreferencePanes"), 0), (env.library / "PreferencePanes", 0),
             (Path("/Library/Input Methods"), 0), (env.library / "Application Support", 2)]
    for root, depth in roots:
        for app in _find_bundles(root, depth):
            _read_bundle(app, inv)
    for cellar in ("/opt/homebrew/Cellar", "/usr/local/Cellar", "/opt/homebrew/Caskroom",
                   "/usr/local/Caskroom"):
        for e in ls(Path(cellar)):
            inv.add(e.name)
    for launch in (Path("/Library/LaunchAgents"), Path("/Library/LaunchDaemons"),
                   env.library / "LaunchAgents"):
        for e in ls(launch):
            if e.name.endswith(".plist"):
                inv.add_bundle(e.name[:-6])
    _add_path_programs(inv, env)
    return inv


def _run(cmd: List[str]) -> List[str]:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return out.stdout.splitlines()
    except Exception:
        return []


def linux_inventory(env: Env) -> Inventory:
    inv = Inventory()
    _add_path_programs(inv, env)
    app_dirs = [Path("/usr/share/applications"), Path("/usr/local/share/applications"),
                env.xdg_data / "applications", Path("/var/lib/flatpak/exports/share/applications"),
                env.xdg_data / "flatpak/exports/share/applications",
                Path("/var/lib/snapd/desktop/applications")]
    for d in app_dirs:
        for e in ls(d):
            if e.name.endswith(".desktop"):
                stem = e.name[:-8]
                inv.add(stem)
                if looks_like_bundle_id(stem):
                    inv.add_bundle(stem)
                for part in re.split(r"[._-]", stem):
                    inv.add(part)
    for e in ls(Path("/snap")):
        inv.add(e.name)
    for root in (Path("/var/lib/flatpak/app"), env.xdg_data / "flatpak/app"):
        for e in ls(root):
            inv.add_bundle(e.name)
    for cmd in (["dpkg-query", "-W", "-f=${Package}\n"], ["rpm", "-qa", "--qf", "%{NAME}\n"],
                ["pacman", "-Qq"]):
        if _which(cmd[0], env):
            for line in _run(cmd):
                inv.add(line.strip())
    return inv


def _which(prog: str, env: Env) -> bool:
    import shutil
    return shutil.which(prog, path=env.var("PATH", os.defpath)) is not None


def _add_path_programs(inv: Inventory, env: Env) -> None:
    for d in env.var("PATH", "").split(os.pathsep):
        if not d:
            continue
        for e in ls(Path(d)):
            name = e.name
            if env.os == WINDOWS:
                low = name.lower()
                if not low.endswith((".exe", ".cmd", ".bat")):
                    continue
                name = name.rsplit(".", 1)[0]
            inv.add(name)


def build_inventory(env: Env) -> Inventory:
    if env.os == WINDOWS:
        return windows_inventory(env)
    if env.os == MACOS:
        return macos_inventory(env)
    return linux_inventory(env)


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

_WIN_KEEP = {"microsoft", "packages", "temp", "programs", "comms", "connecteddevicesplatform",
             "crashdumps", "d3dscache", "peerdistrepub", "publishers", "virtualstore", "npm",
             "npmcache", "pip", "yarn", "nuget", "gobuild", "history", "microsoftedge",
             "applicationdata", "identities", "media center programs", "cef", "intel", "nvidia",
             "nvidiacorporation", "amd", "realtek", "dell", "lenovo", "hp", "asus", "acer",
             "sun", "java", "oracle", "python", "pypa", "jedi", "code", "github", "githubdesktop",
             "squirreltemp", "electron", "pki", "fontcache", "iconcache", "placeholdertilelogo",
             "windowsapps", "elevateddiagnostics", "uwpapplicationdatacache", "programdata"}

_MAC_KEEP = {"addressbook", "callhistorydb", "callhistorytransactions", "clouddocs",
             "crashreporter", "diskimages", "dock", "fileprovider", "knowledge", "mobilesync",
             "syncservices", "accountsd", "icloud", "icdd", "animoji", "appstore", "cloudkit",
             "controlcenter", "differentialprivacy", "facetime", "homeenergyd",
             "identityservicesd", "networkserviceproxy", "quicklook", "safari", "siri",
             "photos", "messages", "maps", "videosubscriptionsd", "contextstoreagent",
             "familycircle", "locationaccessstored", "dmd", "audiounitcache", "screentimeagent",
             "spotlight", "stocks", "weather", "nanoteams", "tipsd", "transparencyd",
             "keychainsharingmessagingd", "storeassetd", "privatecloudcompute"}

_LINUX_KEEP = {"autostart", "gtk20", "gtk30", "gtk40", "fontconfig", "dconf", "pulse", "systemd",
               "environmentd", "menus", "ibus", "applications", "icons", "fonts", "themes",
               "mime", "trash", "keyrings", "desktopdirectories", "sounds", "backgrounds",
               "gvfsmetadata", "flatpak", "recentlyused", "xorg", "session", "sessions",
               "evolution", "tracker", "tracker3", "gnomeshell", "gnomesettingsdaemon",
               "goa10", "dbus1", "xdgdesktopportal", "pipewire", "wireplumber", "kdeconnect",
               "plasma", "kde", "kdedefaults", "kwin", "akonadi", "baloo", "xfce4", "xsettingsd",
               "user", "local", "share", "nautilus", "gnome", "configstore", "procps",
               "yelp", "abrt", "containers", "nvim", "vim", "mc", "htop", "git", "pip",
               "python", "npm", "go", "rust", "cargo", "java", "jupyter", "ipython",
               "matplotlib", "vlc", "libreoffice", "enchant", "ubuntuadvantage",
               "update-notifier", "updatenotifier", "Trolltech", "trolltech", "qtproject",
               "speechdispatcher", "orca", "at-spi", "atspi", "zeitgeist", "telepathy",
               "geoclue", "colord", "cups", "gsconnect", "remmina", "secrets"}


def _age_ok_reason(name: str, reason: str, path: Path, env: Env) -> Candidate:
    return Candidate(path, "ORP-01", reason, {"name": name}, min_age_days=ORPHAN_MIN_AGE)


def orphan_candidates(env: Env, inv: Inventory) -> Iterator[Candidate]:
    if env.os == WINDOWS:
        for base in (env.appdata, env.localappdata):
            for e in ls(base):
                if not is_dir(e):
                    continue
                n = normalize(e.name)
                if n in _WIN_KEEP or e.name.startswith((".", "{")):
                    continue
                if not inv.matches_name(e.name):
                    yield _age_ok_reason(e.name, "orphan_dir", Path(e.path), env)
    elif env.os == MACOS:
        lib = env.library
        for e in ls(lib / "Preferences"):
            if not e.name.endswith(".plist"):
                continue
            stem = e.name[:-6]
            if stem.lower().startswith(("com.apple.", "apple.", "loginwindow", ".")):
                continue
            if looks_like_bundle_id(stem) and not inv.matches_bundle(stem):
                yield _age_ok_reason(stem, "orphan_bundle", Path(e.path), env)
        for e in ls(lib / "Saved Application State"):
            stem = e.name.rsplit(".savedState", 1)[0]
            if stem.lower().startswith("com.apple."):
                continue
            if looks_like_bundle_id(stem) and not inv.matches_bundle(stem):
                yield _age_ok_reason(stem, "orphan_bundle", Path(e.path), env)
        for e in ls(lib / "Application Support"):
            if not is_dir(e) or e.name.startswith("."):
                continue
            n = normalize(e.name)
            if n in _MAC_KEEP or "apple" in n:
                continue
            if looks_like_bundle_id(e.name):
                missing = not inv.matches_bundle(e.name)
            else:
                missing = not inv.matches_name(e.name)
            if missing:
                yield _age_ok_reason(e.name, "orphan_dir", Path(e.path), env)
    else:
        flatpak_installed = {e.name.lower() for root in (Path("/var/lib/flatpak/app"),
                                                         env.xdg_data / "flatpak/app")
                             for e in ls(root)}
        for e in ls(env.home / ".var/app"):
            if is_dir(e) and e.name.lower() not in flatpak_installed:
                yield Candidate(Path(e.path), "ORP-01", "orphan_flatpak", {"name": e.name})
        for base in (env.xdg_config, env.xdg_data):
            for e in ls(base):
                if not is_dir(e) or e.name.startswith("."):
                    continue
                n = normalize(e.name)
                if n in _LINUX_KEEP or n.startswith(("gtk", "kde", "plasma", "gnome", "xfce",
                                                     "dconf", "user")):
                    continue
                if not inv.matches_name(e.name):
                    yield _age_ok_reason(e.name, "orphan_dir", Path(e.path), env)


def orphan_rules(env: Env, inventory: Optional[Inventory] = None) -> Iterator[Candidate]:
    inv = inventory or build_inventory(env)
    yield from orphan_candidates(env, inv)
