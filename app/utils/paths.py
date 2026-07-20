from __future__ import annotations

import os
import sys
from pathlib import Path


def appdata_dir() -> Path:
    return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "MediaGrab"


def local_appdata_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "MediaGrab"


def default_download_dir() -> Path:
    return Path.home() / "Downloads" / "MediaGrab"


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


def binary_dir() -> Path:
    return resource_root() / "bin"


def ensure_app_directories() -> None:
    for path in (appdata_dir(), local_appdata_dir() / "logs", default_download_dir()):
        path.mkdir(parents=True, exist_ok=True)


def settings_path() -> Path: return appdata_dir() / "settings.json"
def history_path() -> Path: return appdata_dir() / "history.json"
def archive_path() -> Path: return appdata_dir() / "download_archive.txt"

