from app.services.format_service import FormatService


def test_bounded_mp4_selector_has_fallbacks():
    value = FormatService().video_selector("1080p", "mp4", "h264")
    assert "height<=1080" in value and "vcodec*=avc" in value and value.endswith("/best")

def test_best_selector_is_unbounded(): assert "height<=" not in FormatService().video_selector("best")

