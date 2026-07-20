from app.models.application_settings import ApplicationSettings
from app.services.disk_service import DiskService
from app.utils.atomic_json import read_json, write_json_atomic


def test_atomic_json(tmp_path):
    target = tmp_path / "data.json"; write_json_atomic(target, {"ok": True}); assert read_json(target, {}) == {"ok": True}

def test_destination_and_organization(tmp_path):
    base = DiskService.validate_destination(str(tmp_path / "downloads")); assert base.is_dir()
    assert DiskService.organized_destination(base, "separate", "audio").name == "Audio"
    assert DiskService.organized_destination(base, "separate", "video").name == "Videos"
    assert DiskService.organized_destination(base, "playlist", "video", "My List").parts[-2:] == ("Playlists", "My List")

def test_settings_clamps_parallelism(): assert ApplicationSettings(parallel_downloads=99).parallel_downloads == 4
