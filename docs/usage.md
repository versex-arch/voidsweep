# voidsweep: full reference

[← Back to README](../README.md) · [Русская версия](usage.ru.md)

- [The window](#the-window)
- [Commands](#commands)
- [Marker codes](#marker-codes)
- [Where it looks](#where-it-looks)
- [Safety model](#safety-model)
- [How the interface is protected](#how-the-interface-is-protected)
- [JSON output](#json-output)
- [Files voidsweep keeps](#files-voidsweep-keeps)
- [Adding a rule](#adding-a-rule)
- [Limitations](#limitations)
- [Development](#development)

## The window

1. **Scan.** Pick the drives, decide whether to *search all drives for junk* (the deep scan), press *Start scan*.
   The ring shows how much was found while it runs and splits into coloured sectors by risk when it is done.
2. **Review.** Items are grouped by marker code. Click a group to expand it; click an item to see, on the right,
   *why it can go*, its size, age and full path. *Show in folder* opens your file manager there;
   *Never touch this* adds the path to your exclusions.
3. **Clean.** Choose *To Trash* (default) or *Delete forever*, press *Clean up*, check the summary and confirm.
   Items that changed after the scan, are in use or need administrator rights are skipped and listed.

Filters: search by name or path, and *All / Safe / Review / Caution*. *Select recommended* restores the default
selection (everything except caution items).

## Commands

| Command | Meaning |
|---|---|
| `voidsweep` | open the window (`--demo` with sample data, `--browser` in the default browser, `--port N`) |
| `voidsweep scan` | grouped list, five biggest items per group |
| `voidsweep scan -v` | every item with its reason |
| `voidsweep scan --deep [--drive PATH]...` | also walk whole drives (all of them by default) |
| `voidsweep scan -m CODE` | only these markers (repeatable) |
| `voidsweep scan --json` | machine-readable output, see below |
| `voidsweep clean -m CODE...` | remove items of the given markers; asks first, uses the Trash |
| `voidsweep clean ... --permanent` | delete instead of the Trash |
| `voidsweep clean ... --dry-run` | run every check, remove nothing |
| `voidsweep clean ... -y` | do not ask |
| `voidsweep markers` | print every marker code with its description |

`--lang ru|en` sets the language of titles and reasons (default: system locale).
Exit codes: `0` done, `1` cancelled at the prompt, `2` usage error, `3` some items were skipped.

## Marker codes

| Code | Risk | Preselected | What it is |
|---|---|---|---|
| `TMP-01` | safe | yes | contents of temp folders untouched for at least a day |
| `TMP-02` | review | yes | `*.tmp` / `*.temp` older than 7 days, Office `~$` lock files, `.crdownload` / `.part` / `.partial` downloads abandoned for 7 days |
| `CCH-01` | safe | yes | application caches, Chromium/Electron caches (`Cache`, `Code Cache`, `GPUCache`…), GPU shader caches |
| `CCH-02` | safe | yes | browser caches |
| `CCH-03` | safe | yes | thumbnail and icon caches |
| `CCH-04` | review | yes | package and build caches |
| `CKE-01` | caution | no | browser cookie stores — removing them signs you out |
| `LOG-01` | safe | yes | logs not written to for 14 days (rotated system logs: 7 days) |
| `DMP-01` | safe | yes | crash dumps, Windows Error Reporting, macOS DiagnosticReports, `/var/crash` |
| `UPD-01` | review | yes | downloaded update packages |
| `ORP-01` | caution | no | data folders of apps that are no longer installed, untouched for 60 days |
| `LNK-01` | safe | yes | `.lnk` shortcuts and `.desktop` launchers whose target is gone |
| `LNK-02` | review | yes | dangling symbolic links in `~/.local/bin`, `~/bin`, Desktop, autostart |
| `SYS-01` | safe | yes | `Thumbs.db`, `ehthumbs.db`, `.DS_Store`, `._name` files whose `name` is gone |
| `DL-01` | caution | no | installers in Downloads older than 30 days |

Codes are stable: new kinds of junk get new codes, existing codes are never renamed or reused.

## Where it looks

| | Windows | macOS | Linux |
|---|---|---|---|
| Temp | `%TEMP%`, `%LOCALAPPDATA%\Temp`, `%SystemRoot%\Temp` | `$TMPDIR`, `/private/tmp`, `/private/var/tmp` | `$TMPDIR`, `/tmp`, `/var/tmp` (your files only) |
| App cache | `INetCache`, `D3DSCache`, NVIDIA/AMD/Intel shader caches, Electron caches in `%APPDATA%` / `%LOCALAPPDATA%` | `~/Library/Caches/*` (not `com.apple.*`), Electron caches in Application Support | `~/.cache/*`, Electron caches in `~/.config` |
| Browsers | profiles under `User Data`, Firefox `cache2` | `~/Library/Caches/<browser>`, profiles in Application Support | `~/.cache/<browser>`, profiles in `~/.config` |
| Thumbnails | `Explorer\thumbcache_*.db`, `iconcache_*.db` | — | `~/.cache/thumbnails` |
| Packages | pip, npm, Yarn, Go, NuGet, Cargo, Bun | pip, npm, Yarn, Go, Homebrew, pnpm, Poetry, uv, Cargo | same as macOS under `~/.cache` |
| Dumps | `CrashDumps`, `WER\ReportArchive/Queue`, `Minidump`, `MEMORY.DMP` | `DiagnosticReports` | `/var/crash`, `systemd/coredump` |
| Updates | `SoftwareDistribution\Download` | `/Library/Updates` | apt `archives/*.deb`, pacman `pkg` |
| Shortcuts | Desktop, Public Desktop, Start Menu, Quick Launch, OneDrive Desktop | — | `~/.local/share/applications`, Desktop |
| Leftovers | `%APPDATA%`, `%LOCALAPPDATA%` vs. registry uninstall keys, Program Files, PATH | Preferences, Saved Application State, Application Support vs. `.app` bundles, Homebrew, LaunchAgents | `~/.config`, `~/.local/share`, `~/.var/app` vs. PATH, `.desktop` files, dpkg/rpm/pacman, Flatpak, Snap |

The deep scan walks each selected drive for `SYS-01`, `TMP-02` and `DMP-01` by name. It does not cross into other
file systems or junctions, and skips system folders, `node_modules`, `.git`, virtual environments, app bundles,
Time Machine backups and the Recycle Bin.

### How leftovers (ORP-01) are detected

voidsweep builds an inventory of installed software (names, publishers, install folders, bundle identifiers,
package names, executables in `PATH`) and compares each app-data folder against it with fuzzy matching. A folder is
reported only if **nothing** matches **and** nothing inside it changed for 60 days. Well-known system folders are
always skipped. This leans towards missing a leftover rather than flagging a live app, but it is still a guess,
which is why ORP-01 is a caution marker.

## Safety model

- **Guard.** Every candidate passes `voidsweep.safety.Guard` twice: before it is shown and right before removal.
  It refuses drive roots, system folders, the home folder and its user folders (Desktop, Documents, Downloads,
  Pictures, Music, Videos, OneDrive…), the temp and cache roots themselves, and anything at most two levels deep.
  It never enters `.ssh`, `.gnupg`, keyrings, macOS Keychains, iCloud Drive, iPhone backups, Mail, Messages,
  Photos libraries, sandboxed app containers or Windows credential stores.
- **Re-check.** If an item's modification time changed after the scan it is skipped as *changed*.
- **No following.** Symbolic links and junctions are removed as links; their targets are never touched, and the
  scanner never descends through them.
- **Ownership.** In shared folders (`/tmp`, `/var/tmp`) only your own files are offered.
- **Age.** Temp files must be a day old; stray temp files a week; logs two weeks; leftovers two months.
- **Trash by default.** Windows: the real Recycle Bin (`SHFileOperationW` with undo). macOS: `~/.Trash`, or Finder
  for other volumes. Linux: the freedesktop.org Trash, so *Restore* works in every desktop environment.
- **No double work.** If a folder and something inside it are both selected, the inner item is not counted twice
  and is reported as removed with its parent.
- **Exclusions and history.** *Never touch this* writes to `ignore.txt`; every cleanup is logged to
  `history.jsonl`.

## How the interface is protected

The window talks to a small HTTP server inside voidsweep:

- it listens on `127.0.0.1` only, on a random port;
- every API call needs a random token generated at each launch and passed to the window in the URL fragment
  (never sent over the network, removed from the address bar on load);
- requests whose `Host` or `Origin` is not that server are rejected, which blocks DNS rebinding and cross-site
  requests from web pages you have open;
- static files are served from the package folder only, with a strict Content-Security-Policy and no inline
  scripts;
- the server stops by itself once the window has been closed.

## JSON output

`voidsweep scan --json` prints:

```json
{
  "findings": [
    {
      "id": 0,
      "path": "C:\\Users\\Alex\\AppData\\Local\\Temp\\setup",
      "name": "setup",
      "kind": "dir",
      "size": 523000000,
      "files": 214,
      "mtime": 1789000000.0,
      "marker": "TMP-01",
      "risk": "safe",
      "reason": {"ru": "…", "en": "…"},
      "needs_admin": false,
      "covered_by": null,
      "preselect": true
    }
  ],
  "summary": {"TMP-01": {"count": 1, "size": 523000000}}
}
```

`kind` is `file`, `dir` or `link`; `mtime` is the newest modification inside a folder; `covered_by` is the `id` of
another finding that contains this one.

## Files voidsweep keeps

| OS | Folder |
|---|---|
| Windows | `%LOCALAPPDATA%\Voidsweep` |
| macOS | `~/Library/Application Support/Voidsweep` |
| Linux | `~/.config/voidsweep` |

`settings.json` (language), `ignore.txt` (exclusions, one path per line), `history.jsonl` (last 100 cleanups) and
`window-profile` (isolated browser profile for the app window). Set `VOIDSWEEP_HOME` to use another folder.
voidsweep never offers its own folder for removal.

## Adding a rule

Rules live in `voidsweep/rules.py`. A rule is a generator that yields candidates:

```python
def my_rule(env):
    yield from single(env.home / ".myapp" / "cache", "CCH-01", "app_cache", {"app": "MyApp"})
```

Add it to `build_rules()` (more specific rules go first: the first rule to claim a path wins), write a test in
`tests/`, and open a pull request. A new kind of junk needs a new marker in `voidsweep/markers.py` with a title,
description and reason text in both languages.

## Limitations

- The release builds are not code-signed, so SmartScreen and Gatekeeper warn on first launch.
- Some items need administrator rights (system temp, Windows Update, `/var/crash`). Without them they are shown with
  a badge and skipped on cleanup; voidsweep never asks for elevation itself.
- Files open in another program (a running browser's cache, thumbnail databases) may be skipped as *in use*.
- macOS privacy protection (TCC) hides some folders unless the app has Full Disk Access.
- Leftover detection is heuristic, see above.

## Development

```console
git clone https://github.com/versex-arch/voidsweep && cd voidsweep
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
voidsweep --demo
```

See [CONTRIBUTING.md](../CONTRIBUTING.md).
