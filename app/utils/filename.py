from __future__ import annotations

import re
from pathlib import Path

INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
ALLOWED_FIELDS = {"title", "id", "ext", "uploader", "playlist_index"}


def sanitize_filename(name: str, max_length: int = 180) -> str:
    cleaned = INVALID.sub("_", name).strip().rstrip(". ")
    if not cleaned: cleaned = "media"
    stem = cleaned.split(".", 1)[0].upper()
    if stem in RESERVED: cleaned = f"_{cleaned}"
    return cleaned[:max_length].rstrip(". ") or "media"


def validate_output_template(template: str) -> str:
    if not template or "/" in template or "\\" in template or ".." in template:
        raise ValueError("Le modèle de nom ne doit contenir aucun chemin.")
    fields = set(re.findall(r"%\(([^)]+)\)", template))
    if not fields or not fields <= ALLOWED_FIELDS or "ext" not in fields:
        raise ValueError("Le modèle de nom contient un champ non autorisé.")
    return template


def is_within_directory(base: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False

