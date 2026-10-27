"""Command-line interface.

    voidsweep                    open the window
    voidsweep scan [--deep]      list what would be removed, with reasons
    voidsweep clean -m TMP-01    remove items of the given markers (asks first)
    voidsweep markers            explain every marker code
"""

from __future__ import annotations

import argparse
import json
import locale
import sys
from typing import List, Optional

from . import APP_NAME, __version__
from .cleaner import PERMANENT, TRASH, clean
from .config import Store, data_dir
from .markers import MARKERS
from .platforms import Env, list_drives
from .safety import Guard
from .scanner import Cancelled, ScanOptions, Scanner, summarize

RISK_ICON = {"safe": "●", "review": "◐", "caution": "○"}


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def default_lang() -> str:
    try:
        loc = (locale.getlocale()[0] or "").lower()
    except Exception:
        loc = ""
    return "ru" if loc.startswith(("ru", "russian", "kk", "be", "uk")) else "en"


def _scan(args, env: Env, store: Store):
    drives = args.drive or [d.path for d in list_drives(env)]
    scanner = Scanner(env, store.ignore_list() + [str(data_dir(env))])

    def progress(info):
        if sys.stderr.isatty() and not args.json:
            detail = str(info.get("detail", ""))[-60:]
            sys.stderr.write(f"\r  {info.get('found', 0):>6} found · {detail:<60}")
            sys.stderr.flush()

    try:
        findings = scanner.run(ScanOptions(deep=args.deep, drives=drives), progress)
    except (Cancelled, KeyboardInterrupt):
        findings = scanner.findings
    if sys.stderr.isatty() and not args.json:
        sys.stderr.write("\r" + " " * 80 + "\r")
    if args.marker:
        wanted = {m.upper() for m in args.marker}
        findings = [f for f in findings if f.marker in wanted]
    return scanner, findings


def cmd_scan(args, env: Env, store: Store) -> int:
    _, findings = _scan(args, env, store)
    lang = args.lang
    if args.json:
        json.dump({"findings": [f.to_dict() for f in findings], "summary": summarize(findings)},
                  sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    groups = summarize(findings)
    total = sum(g["size"] for g in groups.values())
    for code in MARKERS:
        if code not in groups:
            continue
        m = MARKERS[code]
        g = groups[code]
        print(f"\n{RISK_ICON[m.risk]} {code}  {m.title[lang]}  —  {g['count']} · {human(g['size'])}")
        items = [f for f in findings if f.marker == code]
        items.sort(key=lambda f: -f.size)
        shown = items if args.verbose else items[:5]
        for f in shown:
            d = f.to_dict()
            print(f"    {human(f.size):>9}  {f.path}")
            if args.verbose:
                print(f"               {d['reason'][lang]}")
        if len(items) > len(shown):
            print(f"               … +{len(items) - len(shown)}")
    word = "Итого" if lang == "ru" else "Total"
    print(f"\n{word}: {len(findings)} · {human(total)}")
    return 0


def cmd_clean(args, env: Env, store: Store) -> int:
    if not args.marker:
        print("Choose what to remove with --marker CODE (see `voidsweep markers`).",
              file=sys.stderr)
        return 2
    scanner, findings = _scan(args, env, store)
    findings = [f for f in findings if f.covered_by is None]
    size = sum(f.size for f in findings)
    mode = PERMANENT if args.permanent else TRASH
    where = "permanently" if mode == PERMANENT else "to the Trash / Recycle Bin"
    print(f"{len(findings)} items, {human(size)} will be moved {where}.")
    if not findings:
        return 0
    if not args.yes:
        try:
            ok = input("Continue? [y/N] ").strip().lower() in ("y", "yes", "д", "да")
        except EOFError:
            ok = False
        if not ok:
            print("Nothing removed.")
            return 1
    results = clean(findings, scanner.guard, mode, dry_run=args.dry_run)
    freed = sum(r.size for r in results if r.status == "ok")
    failed = [r for r in results if not r.ok]
    for r in failed:
        print(f"  skipped [{r.status}] {r.path} {r.message}")
    print(f"Freed {human(freed)}; {len(failed)} skipped.")
    if not args.dry_run:
        store.add_history({"mode": mode, "freed": freed, "ok": len(results) - len(failed),
                           "failed": len(failed), "source": "cli",
                           "items": [{"path": r.path, "marker": r.marker, "size": r.size,
                                      "status": r.status} for r in results][:2000]})
    return 0 if not failed else 3


def cmd_markers(args, env: Env, store: Store) -> int:
    for m in MARKERS.values():
        print(f"{RISK_ICON[m.risk]} {m.code}  [{m.risk}]  {m.title[args.lang]}")
        print(f"         {m.description[args.lang]}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="voidsweep",
        description=f"voidsweep v{__version__}: find junk on every drive, explain each item, remove only what you approve.",
        epilog="Without a command the window opens. Removal goes to the Trash unless --permanent is given.\n"
               "Exit codes: 0 = done, 1 = cancelled at the prompt, 2 = usage error, 3 = some items were skipped.\n"
               "Run `voidsweep markers` to see what every marker code means.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    p.add_argument("--demo", action="store_true", help="open the window with sample data")
    p.add_argument("--browser", action="store_true", help="use the default browser, not a window")
    p.add_argument("--port", type=int, default=0, help="local port for the interface (default: random)")
    sub = p.add_subparsers(dest="command")

    def common(sp):
        sp.add_argument("--deep", action="store_true", help="also walk whole drives")
        sp.add_argument("--drive", action="append", help="drive/mount to deep-scan (repeatable)")
        sp.add_argument("-m", "--marker", action="append", help="only these marker codes")
        sp.add_argument("--lang", choices=["ru", "en"], default=default_lang(),
                        help="language of titles and reasons (default: system)")

    s = sub.add_parser("scan", help="show what can be removed and why")
    common(s)
    s.add_argument("--json", action="store_true", help="print machine-readable JSON")
    s.add_argument("-v", "--verbose", action="store_true", help="every item with its reason")

    c = sub.add_parser("clean", help="remove items of the chosen markers")
    common(c)
    c.add_argument("--permanent", action="store_true", help="delete instead of using the Trash")
    c.add_argument("--dry-run", action="store_true", help="re-check everything, remove nothing")
    c.add_argument("-y", "--yes", action="store_true", help="do not ask for confirmation")
    c.set_defaults(json=False)

    mk = sub.add_parser("markers", help="explain marker codes")
    mk.add_argument("--lang", choices=["ru", "en"], default=default_lang(),
                    help="language (default: system)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    env = Env.detect()
    store = Store(env)
    if args.command == "scan":
        return cmd_scan(args, env, store)
    if args.command == "clean":
        return cmd_clean(args, env, store)
    if args.command == "markers":
        return cmd_markers(args, env, store)
    from .app import launch
    return launch(port=args.port, demo=args.demo, browser=args.browser)
