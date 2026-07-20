from dataclasses import dataclass


@dataclass(slots=True)
class DownloadProgress:
    percent: float = 0.0
    downloaded: str = ""
    total: str = ""
    speed: str = ""
    eta: str = ""
    state: str = "downloading"
    final_path: str = ""
