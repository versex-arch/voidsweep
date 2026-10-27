"""Marker codes.

A marker is a short code (``CCH-02``) attached to every finding. It says
*what kind* of junk the item is, how risky removing it is, and — together
with the per-finding reason — *why* Voidsweep believes it can go.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

# Risk levels, from "just delete it" to "look before you leap".
SAFE = "safe"        # regenerated automatically; selected by default
REVIEW = "review"    # almost always fine, but has a side effect worth knowing
CAUTION = "caution"  # heuristic or user-visible effect; never pre-selected

RISKS = (SAFE, REVIEW, CAUTION)


@dataclass(frozen=True)
class Marker:
    code: str
    risk: str
    title: Dict[str, str]
    description: Dict[str, str]
    preselect: bool

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "risk": self.risk,
            "title": self.title,
            "description": self.description,
            "preselect": self.preselect,
        }


def _m(code, risk, title_ru, title_en, desc_ru, desc_en, preselect=None):
    if preselect is None:
        preselect = risk != CAUTION
    return Marker(code, risk, {"ru": title_ru, "en": title_en},
                  {"ru": desc_ru, "en": desc_en}, preselect)


MARKERS: Dict[str, Marker] = {m.code: m for m in [
    _m("TMP-01", SAFE,
       "Временные файлы", "Temporary files",
       "Содержимое системных и пользовательских временных папок, которое давно не менялось. "
       "Программы создают эти файлы на время работы и часто забывают убрать за собой.",
       "Contents of system and user temp folders that have not changed in a while. "
       "Programs create these while running and often forget to clean up."),
    _m("TMP-02", REVIEW,
       "Забытые временные файлы на дисках", "Stray temp files on drives",
       "Файлы с «временными» именами (*.tmp, ~$…, незавершённые загрузки), найденные при "
       "глубоком сканировании дисков.",
       "Files with temporary-looking names (*.tmp, ~$…, unfinished downloads) found by the "
       "deep drive scan."),
    _m("CCH-01", SAFE,
       "Кэш приложений", "Application cache",
       "Копии данных, которые приложения хранят для ускорения. Удаление безопасно: программа "
       "заново скачает или пересоздаст их.",
       "Data that apps keep around to go faster. Safe to remove: the app will re-download or "
       "rebuild it."),
    _m("CCH-02", SAFE,
       "Кэш браузеров", "Browser cache",
       "Сохранённые копии страниц, картинок и скриптов. Пароли, закладки и история не затрагиваются.",
       "Saved copies of pages, images and scripts. Passwords, bookmarks and history are untouched."),
    _m("CCH-03", SAFE,
       "Кэш миниатюр и иконок", "Thumbnail & icon cache",
       "Превью картинок и иконок, которые система пересоздаёт сама.",
       "Image previews and icons the system rebuilds on its own."),
    _m("CCH-04", REVIEW,
       "Кэш разработчика и пакетов", "Developer & package caches",
       "Скачанные пакеты pip, npm, yarn, Homebrew, Go и т.п. Удаление безопасно, но следующая "
       "установка пакетов будет дольше.",
       "Downloaded pip, npm, yarn, Homebrew, Go… packages. Safe, but the next install will be slower."),
    _m("CKE-01", CAUTION,
       "Cookies браузеров", "Browser cookies",
       "Файлы cookies. После удаления вы выйдете из аккаунтов на сайтах. Браузер нужно закрыть.",
       "Cookie stores. Removing them signs you out of websites. Close the browser first."),
    _m("LOG-01", SAFE,
       "Старые журналы", "Old logs",
       "Логи программ, которые давно не обновлялись. Нужны только для разбора старых ошибок.",
       "Program logs that have not been written to in a long time. Only useful for old bug hunts."),
    _m("DMP-01", SAFE,
       "Аварийные дампы и отчёты", "Crash dumps & reports",
       "Снимки памяти и отчёты о сбоях. Полезны только разработчикам.",
       "Memory snapshots and crash reports. Only useful to developers."),
    _m("UPD-01", REVIEW,
       "Остатки обновлений", "Update leftovers",
       "Скачанные пакеты уже установленных обновлений системы. Часто нужны права администратора.",
       "Downloaded packages of updates that are already installed. Often needs admin rights."),
    _m("ORP-01", CAUTION,
       "Остатки удалённых программ", "Leftovers of removed apps",
       "Папки настроек и данных, для которых не найдено установленной программы. Это эвристика — "
       "проверьте перед удалением.",
       "Settings and data folders with no matching installed app. This is a heuristic — check "
       "before removing."),
    _m("LNK-01", SAFE,
       "Битые ярлыки", "Broken shortcuts",
       "Ярлыки на рабочем столе и в меню, которые ведут на уже удалённые программы и файлы.",
       "Desktop and menu shortcuts that point to programs or files that no longer exist."),
    _m("LNK-02", REVIEW,
       "Битые символические ссылки", "Broken symlinks",
       "Ссылки, цель которых больше не существует.",
       "Links whose target no longer exists."),
    _m("SYS-01", SAFE,
       "Служебный мусор ОС", "OS clutter files",
       "Thumbs.db, .DS_Store, «осиротевшие» файлы ._* — служебные файлы, которые ОС рассыпает "
       "по папкам и флешкам.",
       "Thumbs.db, .DS_Store, orphaned ._* files — housekeeping files the OS sprinkles across "
       "folders and USB sticks."),
    _m("DL-01", CAUTION,
       "Старые установщики", "Old installers",
       "Файлы установки (.exe, .msi, .dmg, .pkg, .deb…) в Загрузках, которым больше месяца. "
       "Это ваши файлы — решайте сами.",
       "Installer files (.exe, .msi, .dmg, .pkg, .deb…) in Downloads older than a month. "
       "They are your files — your call."),
]}


# Reason templates. ``{age}`` is pre-formatted by :func:`format_age`.
REASONS: Dict[str, Dict[str, str]] = {
    "temp_dir": {
        "ru": "Лежит во временной папке «{root}» и не изменялся {age}. Программа, которая его "
              "создала, давно закончила работу.",
        "en": "Sits in the temp folder “{root}” and has not changed for {age}. Whatever created "
              "it finished long ago.",
    },
    "temp_name": {
        "ru": "Имя подходит под шаблон временного файла «{pattern}», файл не изменялся {age}.",
        "en": "Name matches the temp-file pattern “{pattern}” and it has not changed for {age}.",
    },
    "office_lock": {
        "ru": "Файл-блокировка Microsoft Office (~$…). Остаётся после аварийного закрытия "
              "документа; не изменялся {age}.",
        "en": "Microsoft Office owner/lock file (~$…). Left behind when a document was not closed "
              "cleanly; unchanged for {age}.",
    },
    "partial_download": {
        "ru": "Незавершённая загрузка браузера ({pattern}), не изменялась {age} — загрузка давно "
              "прервана.",
        "en": "Unfinished browser download ({pattern}), unchanged for {age} — it was abandoned "
              "long ago.",
    },
    "app_cache": {
        "ru": "Кэш приложения «{app}». Программа заново скачает или пересоздаст эти данные.",
        "en": "Cache of “{app}”. The app will re-download or rebuild this data.",
    },
    "electron_cache": {
        "ru": "Папка «{name}» внутри «{app}» — кэш движка Chromium/Electron (скрипты, шейдеры, "
              "картинки). Восстанавливается автоматически.",
        "en": "“{name}” inside “{app}” is a Chromium/Electron engine cache (scripts, shaders, "
              "images). Rebuilt automatically.",
    },
    "browser_cache": {
        "ru": "Кэш браузера {app}: копии страниц и картинок. Сайты просто загрузятся заново.",
        "en": "{app} browser cache: copies of pages and images. Sites will simply load again.",
    },
    "thumb_cache": {
        "ru": "Кэш миниатюр/иконок ({app}). Система пересоздаст превью при следующем открытии папок.",
        "en": "Thumbnail/icon cache ({app}). The system rebuilds previews next time folders open.",
    },
    "pkg_cache": {
        "ru": "Кэш {app}: ранее скачанные пакеты. При необходимости они скачаются снова.",
        "en": "{app} cache: previously downloaded packages. They will be fetched again if needed.",
    },
    "cookies": {
        "ru": "Хранилище cookies браузера {app}. После удаления вы выйдете из аккаунтов на сайтах. "
              "Закройте браузер перед очисткой.",
        "en": "{app} cookie store. Removing it signs you out of websites. Close the browser "
              "before cleaning.",
    },
    "old_log": {
        "ru": "Журнал программы, не изменялся {age}. Нужен только для разбора старых ошибок.",
        "en": "Program log, unchanged for {age}. Only useful for investigating old errors.",
    },
    "crash_dump": {
        "ru": "Аварийный дамп или отчёт о сбое, созданный {age} назад. Нужен только разработчикам.",
        "en": "Crash dump or failure report from {age} ago. Only useful to developers.",
    },
    "update_leftover": {
        "ru": "Скачанные файлы обновлений ({app}). Обновления уже установлены; при необходимости "
              "система скачает их снова.",
        "en": "Downloaded update files ({app}). The updates are installed; the system re-downloads "
              "them if ever needed.",
    },
    "orphan_dir": {
        "ru": "Папка данных «{name}», но среди установленных программ ничего похожего не найдено, "
              "и она не менялась {age}. Похоже на остаток удалённого приложения.",
        "en": "Data folder “{name}”, but no installed program matches it and it has not changed "
              "for {age}. Looks like a leftover of a removed app.",
    },
    "orphan_bundle": {
        "ru": "Настройки приложения «{name}», но приложение с таким идентификатором не установлено. "
              "Не изменялось {age}.",
        "en": "Settings for “{name}”, but no app with that identifier is installed. Unchanged "
              "for {age}.",
    },
    "orphan_flatpak": {
        "ru": "Данные Flatpak-приложения «{name}», которое больше не установлено.",
        "en": "Data of the Flatpak app “{name}”, which is no longer installed.",
    },
    "broken_lnk": {
        "ru": "Ярлык ведёт на «{target}», но этого файла больше нет на компьютере.",
        "en": "Shortcut points to “{target}”, which no longer exists on this computer.",
    },
    "broken_desktop": {
        "ru": "Ярлык запуска ссылается на программу «{target}», которой больше нет.",
        "en": "Launcher refers to the program “{target}”, which is gone.",
    },
    "broken_symlink": {
        "ru": "Символическая ссылка указывает на «{target}», которого не существует.",
        "en": "Symbolic link points to “{target}”, which does not exist.",
    },
    "os_junk": {
        "ru": "Служебный файл {os} «{name}» — кэш эскизов или настроек вида папки. Ваших данных "
              "в нём нет, система пересоздаст его при необходимости.",
        "en": "{os} housekeeping file “{name}” — a thumbnail or folder-view cache. Contains none "
              "of your data; recreated if needed.",
    },
    "appledouble": {
        "ru": "Служебный файл macOS «{name}» — «тень» файла «{target}», которого рядом уже нет.",
        "en": "macOS AppleDouble file “{name}” — the shadow of “{target}”, which is no longer there.",
    },
    "old_installer": {
        "ru": "Установщик «{name}» лежит в Загрузках уже {age}. Программа, скорее всего, давно "
              "установлена — сам файл установки больше не нужен.",
        "en": "Installer “{name}” has been in Downloads for {age}. The app is most likely "
              "installed — the setup file itself is no longer needed.",
    },
}


def _ru_plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def format_age(days: float, lang: str) -> str:
    d = int(days)
    if lang == "ru":
        if d < 1:
            return "меньше суток"
        if d >= 730:
            y = d // 365
            return f"{y} {_ru_plural(y, 'год', 'года', 'лет')}"
        if d >= 365:
            return "больше года"
        return f"{d} {_ru_plural(d, 'день', 'дня', 'дней')}"
    if d < 1:
        return "less than a day"
    if d >= 730:
        return f"{d // 365} years"
    if d >= 365:
        return "over a year"
    return f"{d} day" + ("" if d == 1 else "s")


def render_reason(key: str, params: dict, lang: str) -> str:
    template = REASONS[key][lang]
    values = dict(params)
    if "age_days" in values:
        values["age"] = format_age(values["age_days"], lang)
    try:
        return template.format(**values)
    except KeyError:  # a missing parameter must never crash the UI
        return template
