from PySide6.QtWidgets import QPlainTextEdit


class LogPanel(QPlainTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent); self.setReadOnly(True); self.setMaximumBlockCount(1000); self.setPlaceholderText("Les événements de la session apparaîtront ici.")

    def write(self, text: str) -> None: self.appendPlainText(text)

