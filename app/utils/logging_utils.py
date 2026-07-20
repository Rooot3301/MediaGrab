from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.utils.paths import local_appdata_dir

SECRET_KEYS = re.compile(r"(?i)(token|key|secret|password|passwd|cookie|authorization|signature)")


def redact_secrets(text: str) -> str:
    text = re.sub(r"(?i)(authorization|cookie|token|password)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", text)
    def clean_url(match: re.Match[str]) -> str:
        parts = urlsplit(match.group(0))
        query = [(key, "[REDACTED]" if SECRET_KEYS.search(key) else value) for key, value in parse_qsl(parts.query)]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
    return re.sub(r"https?://[^\s]+", clean_url, text)


def configure_logging() -> Path:
    folder = local_appdata_dir() / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"session-{datetime.now():%Y%m%d-%H%M%S}.log"
    logging.basicConfig(filename=target, level=logging.INFO, encoding="utf-8", format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return target

