"""Minimal, dependency-free reader for Windows ``.lnk`` shortcut files.

Implements just enough of [MS-SHLLINK] to recover the target path stored in
the LinkInfo structure. Anything we cannot read with certainty returns
``None`` — an unreadable shortcut is never reported as broken.
"""

from __future__ import annotations

import struct
from typing import Optional

_HEADER_SIZE = 0x4C
_CLSID = bytes.fromhex("0114020000000000c000000000000046")

HAS_ID_LIST = 0x01
HAS_LINK_INFO = 0x02

VOLUME_ID_AND_LOCAL_BASE_PATH = 0x01
COMMON_NETWORK_RELATIVE_LINK = 0x02


def _cstr(data: bytes, off: int) -> str:
    end = data.find(b"\x00", off)
    if end < 0:
        end = len(data)
    return data[off:end].decode("mbcs" if _has_mbcs() else "cp1252", errors="replace")


def _wstr(data: bytes, off: int) -> str:
    end = off
    while end + 1 < len(data) and data[end:end + 2] != b"\x00\x00":
        end += 2
    return data[off:end].decode("utf-16-le", errors="replace")


def _has_mbcs() -> bool:
    try:
        "".encode("mbcs")
        return True
    except LookupError:
        return False


def read_target(data: bytes) -> Optional[str]:
    """Return the local target path of a shortcut, or ``None`` if unknown/network."""
    try:
        return _read_target(data)
    except (struct.error, IndexError, ValueError):
        return None  # truncated or unusual shortcut: never judge it


def _read_target(data: bytes) -> Optional[str]:
    if len(data) < _HEADER_SIZE:
        return None
    header_size, = struct.unpack_from("<I", data, 0)
    if header_size != _HEADER_SIZE or data[4:20] != _CLSID:
        return None
    flags, = struct.unpack_from("<I", data, 0x14)
    off = _HEADER_SIZE
    if flags & HAS_ID_LIST:
        if off + 2 > len(data):
            return None
        id_size, = struct.unpack_from("<H", data, off)
        off += 2 + id_size
    if not flags & HAS_LINK_INFO:
        return None
    if off + 28 > len(data):
        return None
    info = off
    (info_size, info_header_size, info_flags, _vol_off, base_off,
     _net_off, suffix_off) = struct.unpack_from("<7I", data, info)
    if info_size < 28 or info + info_size > len(data):
        return None
    if not info_flags & VOLUME_ID_AND_LOCAL_BASE_PATH:
        return None  # network-only shortcut: we do not judge those
    base = suffix = ""
    if info_header_size >= 0x24 and info_size >= 0x24:
        base_u, suffix_u = struct.unpack_from("<2I", data, info + 28)
        if base_u:
            base = _wstr(data, info + base_u)
        if suffix_u:
            suffix = _wstr(data, info + suffix_u)
    if not base:
        base = _cstr(data, info + base_off)
        if suffix_off:
            suffix = _cstr(data, info + suffix_off)
    target = base + suffix
    if not target or target.startswith("\\\\"):
        return None
    return target


def read_target_file(path) -> Optional[str]:
    try:
        with open(path, "rb") as fh:
            return read_target(fh.read(1 << 16))
    except OSError:
        return None


def build_lnk(target: str) -> bytes:
    """Build a minimal valid .lnk pointing at *target* (used by the test-suite)."""
    base = target.encode("cp1252") + b"\x00"
    suffix = b"\x00"
    info_header = 28
    # VolumeID: size, drive type (3 = fixed), serial, label offset, empty label.
    vol_id = struct.pack("<IIII", 17, 3, 0, 16) + b"\x00"
    vol_off = info_header
    base_off = vol_off + len(vol_id)
    suffix_off = base_off + len(base)
    size = suffix_off + len(suffix)
    info = struct.pack("<7I", size, info_header, VOLUME_ID_AND_LOCAL_BASE_PATH,
                       vol_off, base_off, 0, suffix_off) + vol_id + base + suffix
    header = struct.pack("<I", _HEADER_SIZE) + _CLSID + struct.pack("<I", HAS_LINK_INFO)
    header += b"\x00" * (_HEADER_SIZE - len(header))
    return header + info + b"\x00\x00\x00\x00"
