"""Operating-system detection, well-known folders and drive enumeration."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

WINDOWS, MACOS, LINUX = "windows", "macos", "linux"


def current_os() -> str:
    if sys.platform.startswith("win"):
        return WINDOWS
    if sys.platform == "darwin":
        return MACOS
    return LINUX


@dataclass
class Env:
    """Everything the rules need to know about the machine.

    Kept as a plain object so tests can describe a fake Windows or macOS
    machine while running on Linux.
    """

    os: str
    home: Path
    vars: Dict[str, str] = field(default_factory=dict)
    uid: Optional[int] = None

    @classmethod
    def detect(cls) -> "Env":
        uid = os.getuid() if hasattr(os, "getuid") else None
        return cls(os=current_os(), home=Path.home(), vars=dict(os.environ), uid=uid)

    def var(self, name: str, default: str = "") -> str:
        # Windows env names are case-insensitive.
        if name in self.vars:
            return self.vars[name]
        upper = name.upper()
        for k, v in self.vars.items():
            if k.upper() == upper:
                return v
        return default

    def path_var(self, name: str, fallback: Optional[Path] = None) -> Optional[Path]:
        v = self.var(name)
        if v:
            return Path(v)
        return fallback

    # Windows ---------------------------------------------------------------
    @property
    def appdata(self) -> Path:
        return self.path_var("APPDATA", self.home / "AppData" / "Roaming")

    @property
    def localappdata(self) -> Path:
        return self.path_var("LOCALAPPDATA", self.home / "AppData" / "Local")

    @property
    def systemroot(self) -> Path:
        return self.path_var("SystemRoot", Path("C:/Windows"))

    @property
    def programdata(self) -> Path:
        return self.path_var("ProgramData", Path("C:/ProgramData"))

    # XDG (Linux) -------------------------------------------------------------
    @property
    def xdg_cache(self) -> Path:
        return self.path_var("XDG_CACHE_HOME", self.home / ".cache")

    @property
    def xdg_config(self) -> Path:
        return self.path_var("XDG_CONFIG_HOME", self.home / ".config")

    @property
    def xdg_data(self) -> Path:
        return self.path_var("XDG_DATA_HOME", self.home / ".local" / "share")

    @property
    def library(self) -> Path:
        return self.home / "Library"

    def temp_dirs(self) -> List[Path]:
        out: List[Path] = []
        if self.os == WINDOWS:
            for name in ("TEMP", "TMP"):
                p = self.path_var(name)
                if p:
                    out.append(p)
            out.append(self.localappdata / "Temp")
            out.append(self.systemroot / "Temp")
        elif self.os == MACOS:
            p = self.path_var("TMPDIR")
            if p:
                out.append(p)
            out += [Path("/private/var/tmp"), Path("/private/tmp")]
        else:
            p = self.path_var("TMPDIR")
            if p:
                out.append(p)
            out += [Path("/tmp"), Path("/var/tmp")]
        return dedupe_paths(out)

    def user_folders(self) -> List[Path]:
        names = ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos",
                 "Movies", "Public", "OneDrive", "Dropbox", "iCloud Drive"]
        return [self.home / n for n in names]

    def downloads(self) -> Path:
        xdg = self._xdg_user_dir("DOWNLOAD")
        return xdg or self.home / "Downloads"

    def desktop(self) -> Path:
        xdg = self._xdg_user_dir("DESKTOP")
        return xdg or self.home / "Desktop"

    def _xdg_user_dir(self, key: str) -> Optional[Path]:
        if self.os != LINUX:
            return None
        cfg = self.xdg_config / "user-dirs.dirs"
        try:
            for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line.startswith(f"XDG_{key}_DIR="):
                    val = line.split("=", 1)[1].strip().strip('"')
                    return Path(val.replace("$HOME", str(self.home)))
        except OSError:
            pass
        return None


def dedupe_paths(paths) -> List[Path]:
    seen, out = set(), []
    for p in paths:
        key = norm(p)
        if key not in seen:
            seen.add(key)
            out.append(Path(p))
    return out


def norm(p) -> str:
    """Normalised string form used for comparisons (case-folded on Windows/macOS)."""
    s = os.path.normpath(os.path.abspath(str(p)))
    if current_os() in (WINDOWS, MACOS):
        s = s.lower()
    return s


def is_within(child, parent) -> bool:
    c, p = norm(child), norm(parent)
    if c == p:
        return True
    return c.startswith(p.rstrip(os.sep) + os.sep)


# ---------------------------------------------------------------------------
# Drives
# ---------------------------------------------------------------------------

@dataclass
class Drive:
    path: str
    label: str
    total: int
    free: int
    removable: bool = False

    def to_dict(self) -> dict:
        return {"path": self.path, "label": self.label, "total": self.total,
                "free": self.free, "removable": self.removable}


_LINUX_FS = {"ext2", "ext3", "ext4", "btrfs", "xfs", "f2fs", "vfat", "exfat", "ntfs",
             "ntfs3", "fuseblk", "zfs", "jfs", "reiserfs", "hfsplus", "apfs", "bcachefs"}
_LINUX_SKIP_PREFIX = ("/boot", "/snap", "/var/lib/docker", "/var/lib/containers",
                      "/var/snap", "/run", "/proc", "/sys", "/dev")


def _usage(path: str):
    try:
        u = shutil.disk_usage(path)
        return u.total, u.free
    except OSError:
        return 0, 0


def list_drives(env: Optional[Env] = None) -> List[Drive]:
    env = env or Env.detect()
    drives: List[Drive] = []
    if env.os == WINDOWS:
        drives = _windows_drives()
    elif env.os == MACOS:
        data = "/System/Volumes/Data"
        root = data if os.path.isdir(data) else "/"
        t, f = _usage(root)
        drives.append(Drive(root, "Macintosh HD", t, f))
        try:
            for entry in os.scandir("/Volumes"):
                if entry.is_symlink():  # "Macintosh HD" -> /
                    continue
                if entry.is_dir():
                    t, f = _usage(entry.path)
                    drives.append(Drive(entry.path, entry.name, t, f, removable=True))
        except OSError:
            pass
    else:
        seen = set()
        try:
            with open("/proc/mounts", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError:
            lines = ["/ / ext4"]
        for line in lines:
            parts = line.split()
            if len(parts) < 3:
                continue
            dev, mnt, fstype = parts[0], parts[1].replace("\\040", " "), parts[2]
            if fstype not in _LINUX_FS or any(mnt == p or mnt.startswith(p + "/")
                                               for p in _LINUX_SKIP_PREFIX):
                continue
            if dev in seen or not os.path.isdir(mnt):
                continue
            seen.add(dev)
            t, f = _usage(mnt)
            label = "/" if mnt == "/" else os.path.basename(mnt) or mnt
            drives.append(Drive(mnt, label, t, f,
                                removable=mnt.startswith(("/media", "/run/media", "/mnt"))))
        if not drives:
            t, f = _usage("/")
            drives.append(Drive("/", "/", t, f))
    return drives


def _windows_drives() -> List[Drive]:
    out: List[Drive] = []
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        mask = kernel32.GetLogicalDrives()
        for i in range(26):
            if not mask & (1 << i):
                continue
            root = f"{chr(65 + i)}:\\"
            dtype = kernel32.GetDriveTypeW(ctypes.c_wchar_p(root))
            # 2 = removable, 3 = fixed. Skip network (4), CD (5), RAM disk (6).
            if dtype not in (2, 3):
                continue
            buf = ctypes.create_unicode_buffer(261)
            kernel32.GetVolumeInformationW(ctypes.c_wchar_p(root), buf, 261,
                                           None, None, None, None, 0)
            t, f = _usage(root)
            if t == 0:
                continue
            label = f"{root[:2]} {buf.value}".strip()
            out.append(Drive(root, label, t, f, removable=dtype == 2))
    except Exception:  # pragma: no cover - only on exotic setups
        for i in range(2, 26):
            root = f"{chr(65 + i)}:\\"
            if os.path.exists(root):
                t, f = _usage(root)
                out.append(Drive(root, root[:2], t, f))
    return out


def is_admin() -> bool:
    try:
        if current_os() == WINDOWS:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        return os.geteuid() == 0
    except Exception:
        return False
