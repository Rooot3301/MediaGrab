from __future__ import annotations

from app.constants import QUALITY_HEIGHTS


class FormatService:
    CODECS = {"h264": "avc", "vp9": "vp9", "av1": "av01"}

    def video_selector(self, quality: str, container: str = "mp4", codec: str = "auto") -> str:
        height = QUALITY_HEIGHTS.get(quality)
        height_filter = f"[height<={height}]" if height else ""
        extension = "[ext=mp4]" if container.lower() == "mp4" else ""
        codec_filter = f"[vcodec*={self.CODECS[codec]}]" if codec in self.CODECS else ""
        preferred = f"bestvideo{height_filter}{extension}{codec_filter}+bestaudio"
        compatible = f"bestvideo{height_filter}{extension}+bestaudio"
        bounded = f"bestvideo{height_filter}+bestaudio/best{height_filter}"
        return f"{preferred}/{compatible}/{bounded}/best"

    @staticmethod
    def merge_format(container: str) -> str:
        return container.lower() if container.lower() in {"mp4", "mkv", "webm"} else "mp4"

