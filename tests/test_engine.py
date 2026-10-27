import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from voidsweep import lnk
from voidsweep.cleaner import PERMANENT, TRASH, clean
from voidsweep.config import Store
from voidsweep.deep import classify
from voidsweep.markers import MARKERS, REASONS, format_age, render_reason
from voidsweep.orphans import Inventory, looks_like_bundle_id
from voidsweep.platforms import Env, LINUX, MACOS, WINDOWS
from voidsweep.rules import Candidate, Rule, build_rules, _desktop_exec
from voidsweep.safety import Guard
from voidsweep.scanner import ScanOptions, Scanner

DAY = 86400


def fake_vars(home: Path) -> dict:
    """Point every system location into a temp dir so tests never read the real machine."""
    names = ["LOCALAPPDATA", "APPDATA", "ProgramData", "PUBLIC", "SystemRoot", "ProgramFiles",
             "ProgramFiles(x86)", "ProgramW6432", "TEMP", "TMP", "TMPDIR", "OneDrive"]
    out = {n: str(home / "sys" / n.replace("(", "_").replace(")", "")) for n in names}
    out["PATH"] = ""
    return out


def touch(path: Path, size: int = 10, age_days: float = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    t = time.time() - age_days * DAY
    os.utime(path, (t, t))
    return path


def age_tree(path: Path, age_days: float) -> None:
    t = time.time() - age_days * DAY
    for root, dirs, files in os.walk(path):
        for n in files + dirs:
            os.utime(os.path.join(root, n), (t, t))
    os.utime(path, (t, t))


POSIX_ONLY = unittest.skipIf(os.name == "nt", "simulates a Linux machine (symlinks, uid)")


@POSIX_ONLY
class FakeLinux(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home" / "user"
        self.home.mkdir(parents=True)
        self.env = Env(LINUX, self.home, {"PATH": str(self.root / "bin"),
                                         "TMPDIR": str(self.root / "tmpdir")},
                       uid=os.getuid())

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, rules=None, **kw):
        s = Scanner(self.env, rules=rules)
        return s, s.run(ScanOptions(**kw))


class MarkerTests(unittest.TestCase):
    def test_every_rule_reason_renders_in_both_languages(self):
        for key, langs in REASONS.items():
            self.assertEqual(set(langs), {"ru", "en"}, key)
        for m in MARKERS.values():
            self.assertEqual(set(m.title), {"ru", "en"})

    def test_age_formatting(self):
        self.assertEqual(format_age(1, "ru"), "1 день")
        self.assertEqual(format_age(3, "ru"), "3 дня")
        self.assertEqual(format_age(11, "ru"), "11 дней")
        self.assertEqual(format_age(21, "ru"), "21 день")
        self.assertEqual(format_age(800, "en"), "2 years")

    def test_missing_param_never_crashes(self):
        self.assertTrue(render_reason("broken_lnk", {}, "ru"))


class RulesBuildForEveryOS(unittest.TestCase):
    def test_rules_iterate_without_errors_on_fake_machines(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d) / "u"
            for system in (WINDOWS, MACOS, LINUX):
                env = Env(system, home, fake_vars(home))
                for rule in build_rules(env):
                    self.assertIn(rule.marker, MARKERS)
                    list(rule.collect())  # must not raise on a near-empty machine


@POSIX_ONLY
class ScannerTests(FakeLinux):
    def test_cache_temp_and_age_filter(self):
        cache = self.env.xdg_cache
        touch(cache / "someapp" / "blob.bin", 1000)
        touch(cache / "google-chrome" / "Default" / "Cache" / "f", 500)
        tmpdir = self.root / "tmpdir"
        touch(tmpdir / "old.tmp", 50, age_days=3)
        touch(tmpdir / "fresh.tmp", 50, age_days=0)
        _, found = self.scan()
        by_path = {f.path: f for f in found}
        self.assertEqual(by_path[str(cache / "someapp")].marker, "CCH-01")
        self.assertEqual(by_path[str(cache / "someapp")].size, 1000)
        self.assertEqual(by_path[str(cache / "google-chrome")].marker, "CCH-02")
        self.assertIn(str(tmpdir / "old.tmp"), by_path)
        self.assertNotIn(str(tmpdir / "fresh.tmp"), by_path, "temp files under a day stay")

    def test_specific_rule_wins_and_no_duplicates(self):
        touch(self.env.xdg_cache / "pip" / "wheels" / "a.whl", 100)
        _, found = self.scan()
        pip = [f for f in found if f.path.endswith("/pip")]
        self.assertEqual(len(pip), 1)
        self.assertEqual(pip[0].marker, "CCH-04")

    def test_dir_age_uses_newest_file_inside(self):
        d = self.root / "tmpdir" / "job"
        touch(d / "old", age_days=10)
        touch(d / "new", age_days=0)
        os.utime(d, (time.time() - 10 * DAY,) * 2)
        _, found = self.scan()
        self.assertNotIn(str(d), [f.path for f in found])

    def test_ignore_list(self):
        touch(self.env.xdg_cache / "keepme" / "x", 10)
        s = Scanner(self.env, ignore=[str(self.env.xdg_cache / "keepme")])
        found = s.run()
        self.assertNotIn(str(self.env.xdg_cache / "keepme"), [f.path for f in found])

    def test_coverage_links_nested_findings(self):
        outer = self.home / "outer"
        inner = outer / "inner"
        touch(inner / "f", 100)
        rules = [Rule("a", "CCH-01", lambda: iter([Candidate(inner, "CCH-01", "app_cache", {"app": "x"})])),
                 Rule("b", "ORP-01", lambda: iter([Candidate(outer, "ORP-01", "orphan_dir", {"name": "o"})]))]
        _, found = self.scan(rules=rules)
        by = {f.path: f for f in found}
        self.assertEqual(by[str(inner)].covered_by, by[str(outer)].id)

    def test_broken_desktop_and_symlink(self):
        apps = self.env.xdg_data / "applications"
        apps.mkdir(parents=True)
        (apps / "gone.desktop").write_text("[Desktop Entry]\nType=Application\nExec=/opt/nothing/here %U\n")
        (apps / "ok.desktop").write_text("[Desktop Entry]\nType=Application\nExec=env A=1 sh -c x\n")
        bindir = self.root / "bin"
        bindir.mkdir()
        os.symlink("/bin/sh", bindir / "sh")
        local_bin = self.home / ".local" / "bin"
        local_bin.mkdir(parents=True)
        os.symlink(self.root / "missing-target", local_bin / "dangling")
        _, found = self.scan()
        paths = {f.path: f.marker for f in found}
        self.assertEqual(paths.get(str(apps / "gone.desktop")), "LNK-01")
        self.assertNotIn(str(apps / "ok.desktop"), paths)
        self.assertEqual(paths.get(str(local_bin / "dangling")), "LNK-02")

    def test_desktop_exec_parsing(self):
        p = self.root / "a.desktop"
        p.write_text('[Desktop Entry]\nExec="/opt/My App/run" --x\n[Desktop Action new]\nExec=other\n')
        self.assertEqual(_desktop_exec(str(p)), "/opt/My App/run")

    def test_deep_scan_finds_junk_by_name(self):
        drive = self.root / "drive"
        touch(drive / "photos" / "Thumbs.db")
        touch(drive / "usb" / "._ghost.pdf", 4096)
        touch(drive / "usb" / "._alive.pdf", 4096)
        touch(drive / "usb" / "alive.pdf")
        touch(drive / "docs" / "~$report.docx", 162, age_days=2)
        touch(drive / "dl" / "big.iso.crdownload", 10, age_days=30)
        touch(drive / "dl" / "now.part", 10, age_days=0)
        touch(drive / "node_modules" / "x.tmp", 10, age_days=30)
        _, found = self.scan(rules=[], deep=True, drives=[str(drive)])
        got = {os.path.relpath(f.path, drive): f.marker for f in found}
        self.assertEqual(got, {
            os.path.join("photos", "Thumbs.db"): "SYS-01",
            os.path.join("usb", "._ghost.pdf"): "SYS-01",
            os.path.join("docs", "~$report.docx"): "TMP-02",
            os.path.join("dl", "big.iso.crdownload"): "TMP-02",
        })

    def test_classify(self):
        self.assertEqual(classify("x.DMP", "", 1, "/")[0], "DMP-01")
        self.assertIsNone(classify("readme.md", "", 1, "/"))


@POSIX_ONLY
class SafetyTests(FakeLinux):
    def test_guard_blocks_roots_and_user_folders(self):
        g = Guard(self.env)
        for p in ["/", "/usr", str(self.home), str(self.home / "Documents"),
                  str(self.env.xdg_cache), str(self.home.parent)]:
            self.assertFalse(g.allows(p), p)
        self.assertTrue(g.allows(self.env.xdg_cache / "foo"))
        self.assertFalse(g.allows(self.home / ".ssh" / "id_rsa"))

    def test_scanner_never_offers_protected_paths(self):
        rules = [Rule("bad", "CCH-01", lambda: iter([
            Candidate(self.home, "CCH-01", "app_cache", {}),
            Candidate(self.home / "Documents", "CCH-01", "app_cache", {}),
        ]))]
        (self.home / "Documents").mkdir()
        _, found = self.scan(rules=rules)
        self.assertEqual(found, [])


@POSIX_ONLY
class CleanerTests(FakeLinux):
    def _findings(self, *paths):
        rules = [Rule("t", "CCH-01", lambda: iter([Candidate(p, "CCH-01", "app_cache", {"app": "t"})
                                                 for p in paths]))]
        s, found = self.scan(rules=rules)
        return s, found

    def test_permanent_clean_and_changed_file_is_skipped(self):
        a = touch(self.home / "c" / "a.bin", 100)
        b = touch(self.home / "c" / "b.bin", 100)
        d = self.home / "c" / "dir"
        touch(d / "x", 5)
        s, found = self._findings(a, b, d)
        time.sleep(0.01)
        with open(b, "ab") as fh:
            fh.write(b"more")
        os.utime(b, (time.time() + 5,) * 2)
        res = {r.path: r.status for r in clean(found, s.guard, PERMANENT)}
        self.assertEqual(res[str(a)], "ok")
        self.assertEqual(res[str(b)], "changed")
        self.assertEqual(res[str(d)], "ok")
        self.assertFalse(a.exists())
        self.assertTrue(b.exists())
        self.assertFalse(d.exists())

    def test_symlink_is_removed_not_followed(self):
        target = touch(self.home / "precious" / "data.txt", 10)
        link = self.home / "c" / "link"
        link.parent.mkdir()
        os.symlink(target.parent, link)
        s, found = self._findings(link)
        res = clean(found, s.guard, PERMANENT)
        self.assertEqual(res[0].status, "ok")
        self.assertFalse(os.path.lexists(link))
        self.assertTrue(target.exists())

    @unittest.skipUnless(sys.platform.startswith("linux"), "freedesktop Trash is Linux-only")
    def test_trash_follows_freedesktop_spec(self):
        os.environ["XDG_DATA_HOME"] = str(self.home / ".local" / "share")
        try:
            f = touch(self.home / "c" / "trash me.bin", 10)
            s, found = self._findings(f)
            res = clean(found, s.guard, TRASH)
            self.assertEqual(res[0].status, "ok", res[0].message)
            trash = self.home / ".local" / "share" / "Trash"
            self.assertTrue((trash / "files" / "trash me.bin").exists())
            info = (trash / "info" / "trash me.bin.trashinfo").read_text()
            self.assertIn("Path=" + str(f).replace(" ", "%20"), info)
        finally:
            del os.environ["XDG_DATA_HOME"]

    def test_parent_and_child_both_selected(self):
        outer = self.home / "c" / "outer"
        touch(outer / "inner" / "f")
        s, found = self._findings(outer / "inner", outer)
        res = {r.path: r.status for r in clean(found, s.guard, PERMANENT)}
        self.assertEqual(res[str(outer)], "ok")
        self.assertEqual(res[str(outer / "inner")], "missing")


class LnkTests(unittest.TestCase):
    def test_roundtrip(self):
        data = lnk.build_lnk(r"C:\Program Files\Gone\gone.exe")
        self.assertEqual(lnk.read_target(data), r"C:\Program Files\Gone\gone.exe")

    def test_garbage(self):
        self.assertIsNone(lnk.read_target(b"not a shortcut"))
        self.assertIsNone(lnk.read_target(lnk.build_lnk("x")[:90]))

    def test_broken_lnk_rule(self):
        from voidsweep.rules import broken_lnk_rules
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            desk = home / "Desktop"
            desk.mkdir()
            (desk / "Gone.lnk").write_bytes(lnk.build_lnk(r"C:\Gone\app.exe"))
            (desk / "Here.lnk").write_bytes(lnk.build_lnk(r"C:\Here\app.exe"))
            (desk / "Usb.lnk").write_bytes(lnk.build_lnk(r"F:\Stick\app.exe"))
            env = Env(WINDOWS, home, fake_vars(home))
            exists = lambda p: p in ("C:\\", r"C:\Here\app.exe")
            got = [c.path.name for c in broken_lnk_rules(env, exists=exists)]
            self.assertEqual(got, ["Gone.lnk"])


class InventoryTests(unittest.TestCase):
    def test_fuzzy_matching(self):
        inv = Inventory()
        inv.add("Mozilla Firefox (x64 en-US)")
        inv.add("JetBrains Toolbox")
        inv.add_bundle("com.spotify.client")
        self.assertTrue(inv.matches_name("Mozilla"))
        self.assertTrue(inv.matches_name("JetBrains"))
        self.assertFalse(inv.matches_name("uTorrent"))
        self.assertTrue(inv.matches_bundle("com.spotify.client.helper"))
        self.assertFalse(inv.matches_bundle("com.skype.skype"))
        self.assertTrue(looks_like_bundle_id("com.foo.bar"))
        self.assertFalse(looks_like_bundle_id("Foo Bar"))


class StoreTests(unittest.TestCase):
    def test_settings_ignore_history(self):
        with tempfile.TemporaryDirectory() as d:
            st = Store(Env(LINUX, Path(d)), root=Path(d) / "cfg")
            st.save_settings(lang="en")
            self.assertEqual(st.settings()["lang"], "en")
            st.add_ignore("/a/b")
            st.add_ignore("/a/b")
            self.assertEqual(st.ignore_list(), ["/a/b"])
            st.add_history({"freed": 1})
            st.add_history({"freed": 2})
            self.assertEqual([h["freed"] for h in st.history()], [2, 1])


if __name__ == "__main__":
    unittest.main()
