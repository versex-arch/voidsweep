"""Sample data for ``voidsweep --demo``: screenshots and UI work without touching any disk."""

from __future__ import annotations

import time
from typing import List

from .platforms import Drive
from .scanner import Finding

U = "C:\\Users\\Alex"
L = U + "\\AppData\\Local"
R = U + "\\AppData\\Roaming"

_ROWS = [
    # path, kind, size, files, age days, marker, reason, params
    (L + "\\Google\\Chrome\\User Data\\Default\\Cache", "dir", 812_400_000, 6120, 0.2, "CCH-02",
     "browser_cache", {"app": "Google Chrome"}),
    (L + "\\Google\\Chrome\\User Data\\Default\\Code Cache", "dir", 214_900_000, 1830, 0.2,
     "CCH-02", "browser_cache", {"app": "Google Chrome"}),
    (L + "\\Yandex\\YandexBrowser\\User Data\\Default\\Cache", "dir", 402_100_000, 3311, 3,
     "CCH-02", "browser_cache", {"app": "Yandex Browser"}),
    (L + "\\Mozilla\\Firefox\\Profiles\\k2x9.default-release\\cache2", "dir", 156_000_000, 902,
     11, "CCH-02", "browser_cache", {"app": "Firefox"}),
    (R + "\\discord\\Cache", "dir", 341_800_000, 2410, 1, "CCH-01", "electron_cache",
     {"app": "discord", "name": "Cache"}),
    (R + "\\Code\\CachedData", "dir", 98_300_000, 412, 6, "CCH-01", "electron_cache",
     {"app": "Code", "name": "CachedData"}),
    (R + "\\Telegram Desktop\\tdata\\user_data\\cache", "dir", 1_204_000_000, 9140, 2,
     "CCH-01", "app_cache", {"app": "Telegram Desktop"}),
    (L + "\\NVIDIA\\DXCache", "dir", 267_000_000, 320, 4, "CCH-01", "app_cache",
     {"app": "NVIDIA"}),
    (L + "\\D3DSCache", "dir", 61_200_000, 88, 9, "CCH-01", "app_cache", {"app": "DirectX"}),
    (L + "\\Microsoft\\Windows\\Explorer\\thumbcache_256.db", "file", 88_080_384, 1, 0.5,
     "CCH-03", "thumb_cache", {"app": "Windows Explorer"}),
    (L + "\\Microsoft\\Windows\\Explorer\\iconcache_32.db", "file", 1_048_576, 1, 0.5,
     "CCH-03", "thumb_cache", {"app": "Windows Explorer"}),
    (L + "\\Temp\\{7A1C-44B2}-setup", "dir", 523_000_000, 214, 46, "TMP-01", "temp_dir",
     {"root": L + "\\Temp"}),
    (L + "\\Temp\\chrome_installer.log", "file", 2_140_000, 1, 12, "TMP-01", "temp_dir",
     {"root": L + "\\Temp"}),
    (L + "\\Temp\\vcredist_x64_2026.log", "file", 410_000, 1, 80, "TMP-01", "temp_dir",
     {"root": L + "\\Temp"}),
    ("C:\\Windows\\Temp\\MsiA3F2.tmp", "file", 31_000_000, 1, 120, "TMP-01", "temp_dir",
     {"root": "C:\\Windows\\Temp"}),
    (L + "\\pip\\cache", "dir", 689_000_000, 1520, 30, "CCH-04", "pkg_cache", {"app": "pip"}),
    (R + "\\npm-cache\\_cacache", "dir", 1_301_000_000, 22000, 8, "CCH-04", "pkg_cache",
     {"app": "npm"}),
    (L + "\\Google\\Chrome\\User Data\\Default\\Network\\Cookies", "file", 1_310_720, 1, 0.1,
     "CKE-01", "cookies", {"app": "Google Chrome"}),
    (R + "\\Mozilla\\Firefox\\Profiles\\k2x9.default-release\\cookies.sqlite", "file", 524_288,
     1, 0.1, "CKE-01", "cookies", {"app": "Firefox"}),
    (L + "\\CrashDumps\\Discord.exe.12044.dmp", "file", 412_000_000, 1, 33, "DMP-01",
     "crash_dump", {}),
    (L + "\\Microsoft\\Windows\\WER\\ReportArchive\\AppCrash_steam.exe_4a1c", "dir", 9_300_000,
     3, 51, "DMP-01", "crash_dump", {}),
    ("C:\\Windows\\SoftwareDistribution\\Download\\a81f0c2e9b", "dir", 2_870_000_000, 40, 19,
     "UPD-01", "update_leftover", {"app": "Windows Update"}),
    (R + "\\Zoom\\logs\\zoom_stdout_stderr.log", "file", 18_200_000, 1, 64, "LOG-01", "old_log",
     {}),
    (R + "\\uTorrent", "dir", 41_000_000, 77, 410, "ORP-01", "orphan_dir", {"name": "uTorrent"}),
    (L + "\\Skype", "dir", 233_000_000, 610, 520, "ORP-01", "orphan_dir", {"name": "Skype"}),
    (R + "\\GameLauncherOld", "dir", 12_000_000, 30, 900, "ORP-01", "orphan_dir",
     {"name": "GameLauncherOld"}),
    (U + "\\Desktop\\Minecraft Launcher.lnk", "file", 2_100, 1, 300, "LNK-01", "broken_lnk",
     {"target": "C:\\Program Files (x86)\\Minecraft Launcher\\MinecraftLauncher.exe"}),
    (R + "\\Microsoft\\Windows\\Start Menu\\Programs\\Skype.lnk", "file", 1_900, 1, 520,
     "LNK-01", "broken_lnk", {"target": "C:\\Program Files\\Skype\\Skype.exe"}),
    ("D:\\Photos\\2023\\Thumbs.db", "file", 3_400_000, 1, 700, "SYS-01", "os_junk",
     {"os": "Windows"}),
    ("E:\\USB\\._report.pdf", "file", 4_096, 1, 200, "SYS-01", "appledouble",
     {"target": "report.pdf"}),
    ("D:\\Docs\\~$diploma.docx", "file", 162, 1, 90, "TMP-02", "office_lock", {}),
    ("D:\\Downloads\\ubuntu-24.04.iso.crdownload", "file", 1_830_000_000, 1, 140, "TMP-02",
     "partial_download", {"pattern": "*.crdownload"}),
    (U + "\\Downloads\\ChromeSetup.exe", "file", 1_400_000, 1, 210, "DL-01", "old_installer",
     {"name": "ChromeSetup.exe"}),
    (U + "\\Downloads\\python-3.12.4-amd64.exe", "file", 26_900_000, 1, 95, "DL-01",
     "old_installer", {"name": "python-3.12.4-amd64.exe"}),
]


def demo_findings() -> List[Finding]:
    now = time.time()
    out: List[Finding] = []
    for i, (path, kind, size, files, age, marker, reason, params) in enumerate(_ROWS):
        mtime = now - age * 86400
        p = dict(params)
        p.setdefault("name", path.rsplit("\\", 1)[-1])
        p["age_days"] = age
        out.append(Finding(i, path, kind, size, files, mtime, mtime, marker, reason, p,
                           needs_admin=path.startswith("C:\\Windows")))
    return out


def demo_drives() -> List[Drive]:
    gb = 1024 ** 3
    return [Drive("C:\\", "C: Windows", 476 * gb, 61 * gb),
            Drive("D:\\", "D: Data", 931 * gb, 402 * gb),
            Drive("E:\\", "E: USB", 58 * gb, 40 * gb, removable=True)]
