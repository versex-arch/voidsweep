# Contributing

Thanks for helping out. The project is small; the process is too.

## Setup

```bash
git clone https://github.com/versex-arch/voidsweep.git
cd voidsweep
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before you open a pull request

```bash
pytest           # builds fake home folders in a temp dir, never touches your real files
voidsweep --demo # check the interface with sample data
```

## Ground rules

- **Never lose user data.** When in doubt, a rule does not report. A missed cache file costs nothing;
  a deleted photo cannot be undone.
- **Every item explains itself.** A new rule comes with a reason text in Russian and English that says, in plain
  words, why *this* item can go.
- **Rules only propose.** Size, age, de-duplication and the safety guard are the scanner's job; do not bypass them.
- **No dependencies** in the core. Optional extras are fine.
- **Stable marker codes.** A new kind of junk gets a new code in `voidsweep/markers.py`; never rename or reuse
  a code, people learn them.
- **Test with real files.** Create the situation in a temporary folder and assert on what the scanner reports.
  A bug fix comes with a test that fails without it.
- User-visible changes go into [CHANGELOG.md](CHANGELOG.md) under "Unreleased".

## Releasing

1. Bump `__version__` in `voidsweep/__init__.py` and move the changelog entries under the new version.
2. Tag and push: `git tag v0.2.0 && git push --tags`. The release workflow builds the Windows, macOS and Linux
   archives and creates the GitHub release.

## Reporting bugs

Open an issue with your OS, what you did, and the marker code and path of the item involved
(`voidsweep scan --json -m CODE` is ideal).
Something offered that must never be removed is a security problem: see [SECURITY.md](SECURITY.md).
