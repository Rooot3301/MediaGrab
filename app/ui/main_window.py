from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.download_job import DownloadJob, DownloadStatus
from app.models.media_info import MediaInfo
from app.services.binary_service import BinaryService
from app.services.disk_service import DiskService
from app.services.download_service import DownloadManager
from app.services.history_service import HistoryService
from app.services.metadata_service import MetadataService
from app.services.settings_service import SettingsService
from app.ui.download_item_widget import DownloadItemWidget
from app.ui.history_widget import HistoryWidget
from app.ui.log_panel import LogPanel
from app.ui.settings_dialog import SettingsWidget
from app.utils.filename import sanitize_filename, validate_output_template


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MediaGrab")
        self.resize(1040, 880)
        self.setMinimumSize(820, 680)
        self.settings_service = SettingsService()
        self.settings = self.settings_service.load()
        self.history_service = HistoryService()
        self.binaries = BinaryService()
        self.metadata = MetadataService(self.binaries, self)
        self.manager = DownloadManager(self.binaries, self.settings.parallel_downloads, self)
        self.media: MediaInfo | None = None
        self.items: dict[str, DownloadItemWidget] = {}
        self.network = QNetworkAccessManager(self)
        self._build_ui()
        self._connect()
        self._shortcuts()
        self._binary_notice()
        self._update_actions()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        download_tab = QWidget()
        self.tabs.addTab(download_tab, "Télécharger")
        self.history = HistoryWidget(self.history_service)
        self.tabs.addTab(self.history, "Historique")
        self.settings_tab = SettingsWidget(self.settings)
        self.tabs.addTab(self.settings_tab, "Paramètres")

        root = QVBoxLayout(download_tab)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        title = QLabel("Nouveau téléchargement")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Collez un lien, vérifiez les informations puis choisissez votre format.")
        subtitle.setObjectName("mutedText")
        root.addWidget(title)
        root.addWidget(subtitle)

        url_row = QHBoxLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("Collez une URL HTTP ou HTTPS…")
        self.paste = QPushButton("Coller")
        self.analyze = QPushButton("Analyser")
        self.analyze.setObjectName("primaryButton")
        self.spinner = QLabel("")
        url_row.addWidget(self.url, 1)
        url_row.addWidget(self.paste)
        url_row.addWidget(self.analyze)
        url_row.addWidget(self.spinner)
        root.addLayout(url_row)

        media_card = QFrame()
        media_card.setObjectName("card")
        media_row = QHBoxLayout(media_card)
        media_row.setContentsMargins(16, 16, 16, 16)
        self.thumbnail = QLabel("Aperçu")
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setFixedSize(200, 112)
        self.thumbnail.setScaledContents(True)
        details = QVBoxLayout()
        self.media_title = QLabel("Aucun média analysé")
        self.media_title.setObjectName("mediaTitle")
        self.media_meta = QLabel("Les informations du média apparaîtront ici.")
        self.media_meta.setObjectName("mutedText")
        self.media_meta.setWordWrap(True)
        details.addWidget(self.media_title)
        details.addWidget(self.media_meta)
        details.addStretch()
        media_row.addWidget(self.thumbnail)
        media_row.addLayout(details, 1)
        root.addWidget(media_card)

        options_card = QFrame()
        options_card.setObjectName("card")
        options_layout = QVBoxLayout(options_card)
        options_layout.setContentsMargins(16, 14, 16, 14)
        options_title = QLabel("Options de sortie")
        options_title.setObjectName("sectionTitle")
        options_layout.addWidget(options_title)
        form = QFormLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Vidéo", "Audio uniquement"])
        self.quality = QComboBox()
        self.quality.addItems(["Automatique", "360p", "480p", "720p", "1080p", "1440p", "2160p", "Meilleure qualité"])
        self.quality.setCurrentText("1080p")
        self.format = QComboBox()
        self.format.addItems(["MP4", "MKV", "WebM"])
        self.codec = QComboBox()
        self.codec.addItems(["Automatique", "H.264", "VP9", "AV1"])
        self.bitrate = QComboBox()
        self.bitrate.addItems(["128 kb/s", "192 kb/s", "256 kb/s", "320 kb/s"])
        self.bitrate.setCurrentText("320 kb/s")
        self.bitrate.setVisible(False)
        form.addRow("Mode", self.mode)
        form.addRow("Qualité", self.quality)
        form.addRow("Format", self.format)
        form.addRow("Codec préféré", self.codec)
        form.addRow("Qualité audio", self.bitrate)
        options_layout.addLayout(form)
        root.addWidget(options_card)

        dest_row = QHBoxLayout()
        self.destination = QLineEdit(self.settings.last_download_directory)
        self.browse_button = QPushButton("Parcourir…")
        self.open_button = QPushButton("Ouvrir")
        self.reset_button = QPushButton("Par défaut")
        dest_row.addWidget(self.destination, 1)
        dest_row.addWidget(self.browse_button)
        dest_row.addWidget(self.open_button)
        dest_row.addWidget(self.reset_button)
        root.addWidget(QLabel("Destination"))
        root.addLayout(dest_row)
        checks = QHBoxLayout()
        self.subtitles = QCheckBox("Sous-titres")
        self.metadata_box = QCheckBox("Métadonnées")
        self.metadata_box.setChecked(True)
        self.thumbnail_box = QCheckBox("Intégrer la miniature")
        self.thumbnail_box.setChecked(True)
        self.playlist = QCheckBox("Playlist entière")
        for widget in (self.subtitles, self.metadata_box, self.thumbnail_box, self.playlist):
            checks.addWidget(widget)
        checks.addStretch()
        root.addLayout(checks)

        actions = QHBoxLayout()
        actions.addStretch()
        self.queue_button = QPushButton("Ajouter à la file")
        self.download_button = QPushButton("Télécharger maintenant")
        self.download_button.setObjectName("primaryButton")
        actions.addWidget(self.queue_button)
        actions.addWidget(self.download_button)
        root.addLayout(actions)
        queue_head = QHBoxLayout()
        queue_title = QLabel("File de téléchargements")
        queue_title.setObjectName("sectionTitle")
        self.queue_count = QLabel()
        self.queue_count.setObjectName("mutedText")
        self.start_queue_button = QPushButton("Démarrer la file")
        queue_head.addWidget(queue_title)
        queue_head.addWidget(self.queue_count)
        queue_head.addStretch()
        queue_head.addWidget(self.start_queue_button)
        root.addLayout(queue_head)
        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(10)
        self.queue_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.queue_container)
        root.addWidget(scroll, 1)
        self.logs = LogPanel()
        self.logs.setVisible(False)
        root.addWidget(self.logs)
        self.statusBar().showMessage("Prêt — téléchargez uniquement les contenus que vous êtes autorisé à utiliser.")

    def _connect(self) -> None:
        self.paste.clicked.connect(lambda: self.url.setText(QApplication.clipboard().text()))
        self.analyze.clicked.connect(self._analyze)
        self.url.returnPressed.connect(self._analyze)
        self.url.textChanged.connect(self._update_actions)
        self.mode.currentTextChanged.connect(self._mode_changed)
        self.browse_button.clicked.connect(self._browse)
        self.open_button.clicked.connect(lambda: self._open_folder(self.destination.text()))
        self.reset_button.clicked.connect(lambda: self.destination.setText(self.settings.default_download_directory))
        self.queue_button.clicked.connect(lambda: self._enqueue(False))
        self.download_button.clicked.connect(lambda: self._enqueue(True))
        self.start_queue_button.clicked.connect(self.manager.start_available)
        self.metadata.succeeded.connect(self._metadata_ready)
        self.metadata.failed.connect(self._error)
        self.metadata.busy_changed.connect(self._busy)
        self.manager.job_updated.connect(self._job_updated)
        self.manager.job_finished.connect(self._job_finished)
        self.settings_tab.saved.connect(self._settings_saved)

    def _shortcuts(self) -> None:
        settings = QAction(self)
        settings.setShortcut(QKeySequence("Ctrl+,"))
        settings.triggered.connect(lambda: self.tabs.setCurrentWidget(self.settings_tab))
        self.addAction(settings)
        choose = QAction(self)
        choose.setShortcut(QKeySequence("Ctrl+O"))
        choose.triggered.connect(self._browse)
        self.addAction(choose)
        start = QAction(self)
        start.setShortcut(QKeySequence("Ctrl+Return"))
        start.triggered.connect(lambda: self._enqueue(True))
        self.addAction(start)
        logs = QAction(self)
        logs.setShortcut(QKeySequence("Ctrl+L"))
        logs.triggered.connect(lambda: self.logs.setVisible(not self.logs.isVisible()))
        self.addAction(logs)

    def _analyze(self) -> None:
        self.metadata.analyze(self.url.text(), self.playlist.isChecked())

    def _busy(self, busy: bool) -> None:
        self.analyze.setEnabled(not busy)
        self.spinner.setText("Analyse…" if busy else "")

    def _metadata_ready(self, media: MediaInfo) -> None:
        self.media = media
        duration = f"{int(media.duration or 0)//60}:{int(media.duration or 0)%60:02d}"
        best = f"{media.best_height}p" if media.best_height else "inconnue"
        playlist = f" · Playlist ({media.playlist_count} éléments)" if media.is_playlist else ""
        self.media_title.setText(media.title)
        self.media_meta.setText(f"{media.author or 'Auteur inconnu'} · {duration} · {media.platform or 'Plateforme inconnue'} · max. {best}{playlist}")
        self._update_actions()
        if media.thumbnail_url:
            reply = self.network.get(QNetworkRequest(QUrl(media.thumbnail_url)))
            reply.finished.connect(lambda r=reply: self._thumbnail_ready(r))

    def _thumbnail_ready(self, reply: QNetworkReply) -> None:
        pixmap = QPixmap()
        if pixmap.loadFromData(reply.readAll()):
            self.thumbnail.setPixmap(pixmap)
        reply.deleteLater()

    def _mode_changed(self, text: str) -> None:
        audio = text.startswith("Audio")
        self.quality.setVisible(not audio)
        self.codec.setVisible(not audio)
        self.bitrate.setVisible(audio)
        self.format.clear()
        self.format.addItems(["MP3", "M4A", "FLAC", "WAV", "Opus"] if audio else ["MP4", "MKV", "WebM"])

    def _browse(self) -> None:
        value = QFileDialog.getExistingDirectory(self, "Choisir le dossier de destination", self.destination.text())
        if value:
            self.destination.setText(value)
            self.settings.last_download_directory = value
            self.settings_service.save(self.settings)

    def _enqueue(self, start: bool) -> None:
        if not self.media:
            self._error("Analysez d’abord une URL.")
            return
        try:
            validate_output_template(self.settings.filename_template)
            base = DiskService.validate_destination(self.destination.text(), self.media.estimated_size)
            playlist_name = sanitize_filename(self.media.title) if self.media.is_playlist else ""
            media_type = "audio" if self.mode.currentText().startswith("Audio") else "video"
            destination = str(DiskService.organized_destination(base, self.settings.organize_mode, media_type, playlist_name))
        except Exception as error:
            self._error(str(error))
            return
        audio = self.mode.currentText().startswith("Audio")
        codec = {"Automatique": "auto", "H.264": "h264", "VP9": "vp9", "AV1": "av1"}[self.codec.currentText()]
        quality = self.quality.currentText().replace("Automatique", "auto").replace("Meilleure qualité", "best")
        job = DownloadJob(
            url=self.media.original_url,
            title=self.media.title,
            mode="audio" if audio else "video",
            quality=quality,
            output_format=self.format.currentText().lower(),
            destination=destination,
            filename_template=self.settings.filename_template,
            video_codec=codec,
            audio_bitrate=self.bitrate.currentText().split()[0],
            subtitles=self.subtitles.isChecked(),
            embed_metadata=self.metadata_box.isChecked(),
            embed_thumbnail=self.thumbnail_box.isChecked(),
            playlist=self.playlist.isChecked(),
            use_archive=self.settings.use_download_archive,
        )
        self.manager.enqueue(job, start)

    def _job_updated(self, job: DownloadJob) -> None:
        item = self.items.get(job.id)
        if not item:
            item = DownloadItemWidget(job)
            item.cancel_requested.connect(self.manager.cancel)
            item.retry_requested.connect(self.manager.retry)
            item.open_requested.connect(lambda job_id: self._open_folder(self.manager.find(job_id).destination))
            self.items[job.id] = item
            self.queue_layout.insertWidget(self.queue_layout.count() - 1, item)
        item.update_job(job)
        self._update_actions()

    def _job_finished(self, job: DownloadJob) -> None:
        self.history_service.add(job.to_dict(), self.settings.history_limit)
        self.history.refresh()
        self.statusBar().showMessage(f"{job.title} : {job.status.value}", 8000)

    def _open_folder(self, value: str) -> None:
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(DiskService.validate_destination(value))))
        except Exception as error:
            self._error(str(error))

    def _settings_saved(self) -> None:
        try:
            validate_output_template(self.settings.filename_template)
        except ValueError as error:
            self._error(str(error))
            return
        self.settings_service.save(self.settings)
        self.manager.maximum = self.settings.parallel_downloads
        self.manager.start_available()
        self.statusBar().showMessage("Paramètres enregistrés.", 4000)

    def _update_actions(self, *_args) -> None:
        ready = self.media is not None
        self.queue_button.setEnabled(ready)
        self.download_button.setEnabled(ready)
        queued = sum(job.status == DownloadStatus.QUEUED for job in self.manager.jobs)
        active = len(self.manager.runners)
        total = len(self.manager.jobs)
        self.queue_count.setText("Aucun élément" if total == 0 else f"{total} élément{'s' if total != 1 else ''} · {active} actif{'s' if active != 1 else ''}")
        self.start_queue_button.setVisible(queued > 0)
        self.start_queue_button.setEnabled(active < self.manager.maximum)

    def _binary_notice(self) -> None:
        missing = [name for name, value in self.binaries.status().items() if value == "absent"]
        if missing:
            self.statusBar().showMessage("Binaires manquants : " + ", ".join(missing) + ". Consultez le README.")

    def _error(self, message: str) -> None:
        QMessageBox.warning(self, "MediaGrab", message)
        self.logs.write(message)

    def closeEvent(self, event) -> None:
        self.metadata.cancel()
        self.manager.shutdown()
        self.settings_service.save(self.settings)
        event.accept()
