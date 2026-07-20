from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from app.exceptions import InvalidUrlError


def validate_media_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise InvalidUrlError("Veuillez saisir une URL.")
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise InvalidUrlError("Seules les URL HTTP et HTTPS valides sont acceptées.")
    if parsed.username or parsed.password:
        raise InvalidUrlError("Les identifiants intégrés à une URL ne sont pas acceptés.")
    try:
        address = ipaddress.ip_address(parsed.hostname)
        if address.is_loopback or address.is_private or address.is_link_local:
            raise InvalidUrlError("Les adresses réseau locales ne sont pas acceptées.")
    except ValueError:
        pass
    return value

