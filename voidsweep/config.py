"""User settings, the ignore list and the cleanup history."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import List, Optional

from .platforms import Env, MACOS, WINDOWS

HISTORY_LIMIT = 100


def data_dir(env: Optional[Env] = None) -> Path:
    env = env or Env.detect()
    override = env.var("VOIDSWEEP_HOME")
    if override:
        return Path(override)
    if env.os == WINDOWS:
        return env.localappdata / "Voidsweep"
    if env.os == MACOS:
        return env.library / "Application Support" / "Voidsweep"
    return env.xdg_config / "voidsweep"


class Store:
    def __init__(self, env: Optional[Env] = None, root: Optional[Path] = None):
        self.env = env or Env.detect()
        self.root = root or data_dir(self.env)

    # ---------------------------------------------------------------- files
    def _path(self, name: str) -> Path:
        return self.root / name

    def _ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- settings
    def settings(self) -> dict:
        try:
            return json.loads(self._path("settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_settings(self, **values) -> dict:
        s = self.settings()
        s.update({k: v for k, v in values.items() if v is not None})
        self._ensure()
        self._path("settings.json").write_text(json.dumps(s, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
        return s

    # ---------------------------------------------------------------- ignore
    def ignore_list(self) -> List[str]:
        try:
            lines = self._path("ignore.txt").read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]

    def add_ignore(self, path: str) -> List[str]:
        items = self.ignore_list()
        if path not in items:
            items.append(path)
        self._write_ignore(items)
        return items

    def remove_ignore(self, path: str) -> List[str]:
        items = [i for i in self.ignore_list() if i != path]
        self._write_ignore(items)
        return items

    def _write_ignore(self, items: List[str]) -> None:
        self._ensure()
        header = "# Voidsweep never offers anything inside these paths. One path per line.\n"
        self._path("ignore.txt").write_text(header + "\n".join(items) + "\n", encoding="utf-8")

    # --------------------------------------------------------------- history
    def history(self) -> List[dict]:
        try:
            lines = self._path("history.jsonl").read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        out = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out[::-1]

    def add_history(self, entry: dict) -> None:
        self._ensure()
        entry = {"time": time.time(), **entry}
        items = self.history()[::-1][-(HISTORY_LIMIT - 1):] + [entry]
        tmp = self._path("history.jsonl.tmp")
        tmp.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n",
                       encoding="utf-8")
        os.replace(tmp, self._path("history.jsonl"))
