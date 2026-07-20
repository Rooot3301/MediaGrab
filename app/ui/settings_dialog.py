from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models.application_settings import ApplicationSettings
from app.utils.filename import validate_output_template


class SettingsWidget(QWidget):
    saved = Signal()

    def __init__(self, settings: ApplicationSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings

        title = QLabel("Paramètres")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Personnalisez le comportement de MediaGrab. Les changements sont enregistrés localement.")
        subtitle.setObjectName("mutedText")

        general = QFrame()
        general.setObjectName("card")
        general_layout = QVBoxLayout(general)
        general_layout.addWidget(self._section_title("Général", "Destination, organisation et apparence"))
        general_form = QFormLayout()
        self.folder = QLineEdit(settings.default_download_directory)
        browse = QPushButton("Parcourir…")
        browse.clicked.connect(self._browse)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder, 1)
        folder_row.addWidget(browse)
        general_form.addRow("Dossier par défaut", folder_row)
        self.organize = QComboBox()
        self.organize.addItem("Tout dans le dossier choisi", "all")
        self.organize.addItem("Séparer Audio et Vidéos", "separate")
        self.organize.addItem("Créer un dossier par playlist", "playlist")
        self.organize.setCurrentIndex(max(0, self.organize.findData(settings.organize_mode)))
        general_form.addRow("Organisation", self.organize)
        self.theme = QComboBox()
        self.theme.addItem("Sombre", "dark")
        self.theme.addItem("Clair", "light")
        self.theme.addItem("Système", "system")
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.theme)))
        general_form.addRow("Thème", self.theme)
        general_layout.addLayout(general_form)

        downloads = QFrame()
        downloads.setObjectName("card")
        downloads_layout = QVBoxLayout(downloads)
        downloads_layout.addWidget(self._section_title("Téléchargements", "File d’attente, noms de fichiers et historique"))
        downloads_form = QFormLayout()
        self.parallel = QSpinBox()
        self.parallel.setRange(1, 4)
        self.parallel.setValue(settings.parallel_downloads)
        downloads_form.addRow("Téléchargements simultanés", self.parallel)
        self.template = QLineEdit(settings.filename_template)
        self.template.setPlaceholderText("%(title)s [%(id)s].%(ext)s")
        downloads_form.addRow("Modèle de nom", self.template)
        self.history_limit = QSpinBox()
        self.history_limit.setRange(10, 5000)
        self.history_limit.setSingleStep(50)
        self.history_limit.setValue(settings.history_limit)
        downloads_form.addRow("Éléments dans l’historique", self.history_limit)
        self.archive = QCheckBox("Éviter de télécharger deux fois le même média")
        self.archive.setChecked(settings.use_download_archive)
        downloads_form.addRow("Archive anti-doublons", self.archive)
        downloads_layout.addLayout(downloads_form)

        self.feedback = QLabel("")
        self.feedback.setObjectName("successText")
        save = QPushButton("Enregistrer les paramètres")
        save.setObjectName("primaryButton")
        save.clicked.connect(self.apply)
        actions = QHBoxLayout()
        actions.addWidget(self.feedback)
        actions.addStretch()
        actions.addWidget(save)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(general)
        layout.addWidget(downloads)
        layout.addStretch()
        layout.addLayout(actions)

    @staticmethod
    def _section_title(title: str, subtitle: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 8)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        description = QLabel(subtitle)
        description.setObjectName("mutedText")
        layout.addWidget(heading)
        layout.addWidget(description)
        return widget

    def _browse(self) -> None:
        value = QFileDialog.getExistingDirectory(self, "Dossier par défaut", self.folder.text())
        if value:
            self.folder.setText(value)

    def apply(self) -> None:
        try:
            template = validate_output_template(self.template.text().strip())
        except ValueError as error:
            self.feedback.setStyleSheet("color: #ff9b9b;")
            self.feedback.setText(str(error))
            return
        self.settings.default_download_directory = self.folder.text().strip()
        self.settings.theme = self.theme.currentData()
        self.settings.parallel_downloads = self.parallel.value()
        self.settings.organize_mode = self.organize.currentData()
        self.settings.filename_template = template
        self.settings.history_limit = self.history_limit.value()
        self.settings.use_download_archive = self.archive.isChecked()
        self.feedback.setStyleSheet("")
        self.feedback.setText("Paramètres enregistrés")
        self.saved.emit()
