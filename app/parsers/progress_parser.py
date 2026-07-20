from __future__ import annotations

from app.constants import FINAL_PATH_PREFIX, PROGRESS_PREFIX
from app.models.download_progress import DownloadProgress


def parse_progress(line: str) -> DownloadProgress | None:
    line = line.strip()
    if line.startswith(FINAL_PATH_PREFIX):
        return DownloadProgress(percent=100.0, state="finished", final_path=line[len(FINAL_PATH_PREFIX):])
    if not line.startswith(PROGRESS_PREFIX): return None
    fields = line[len(PROGRESS_PREFIX):].split("|")
    if len(fields) < 5: return None
    try: percent = float(fields[0].replace("%", "").strip() or 0)
    except ValueError: percent = 0.0
    return DownloadProgress(percent=max(0.0, min(100.0, percent)), downloaded=fields[1], total=fields[2], speed=fields[3], eta=fields[4])

