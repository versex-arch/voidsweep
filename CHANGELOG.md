# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-27

### Added
- First release: scan for junk on Windows, macOS and Linux, review the list, clean only what you approve.
- 15 marker codes (`TMP-01` … `DL-01`) with a risk level and a reason in Russian and English for every item.
- Detection of leftovers of uninstalled apps (`ORP-01`) and broken shortcuts (`LNK-01`, with a built-in `.lnk`
  reader).
- Deep scan of all drives for `Thumbs.db`, `.DS_Store`, orphaned `._*` files, stray temp files and abandoned
  downloads.
- Removal to the Recycle Bin / Trash on all three systems without dependencies; optional permanent delete.
- Safety guard, re-check before removal, exclusions and cleanup history.
- Window interface (black, violet, teal, milk) served on a token-protected localhost API; Russian and English.
- Command line: `scan`, `clean`, `markers`, `--json`, `--demo`.
- CI on Windows, macOS and Linux; release builds for all three.
