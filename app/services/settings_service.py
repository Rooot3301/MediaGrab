from app.models.application_settings import ApplicationSettings
from app.utils.atomic_json import read_json, write_json_atomic
from app.utils.paths import settings_path


class SettingsService:
    def load(self) -> ApplicationSettings:
        return ApplicationSettings.from_dict(read_json(settings_path(), {}))

    def save(self, settings: ApplicationSettings) -> None:
        write_json_atomic(settings_path(), settings.to_dict())

