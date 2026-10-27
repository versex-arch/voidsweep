"""Entry point for the PyInstaller builds (keeps relative imports working)."""

import sys

from voidsweep.cli import main

if __name__ == "__main__":
    sys.exit(main())
