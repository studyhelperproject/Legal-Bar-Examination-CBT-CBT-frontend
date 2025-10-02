from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QFont, QFontInfo, QTextOption, QTextCursor
from PyQt6.QtWidgets import QTextEdit, QSizePolicy

class AnswerGridEditor(QTextEdit):
    """司法試験用の答案入力テキストエディタ。"""
    contentModified = pyqtSignal()

    def __init__(self, parent=None, columns=30, rows=23):
        super().__init__(parent)
        self.max_chars = columns
        self.max_lines = rows
        self._internal_change = False

        base_font = QFont("Hiragino Mincho ProN", 14)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("MS Mincho", 14)
        self.setFont(base_font)

        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        if self._internal_change:
            return
        self.contentModified.emit()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.insertPlainText('\n')
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())

    def get_content(self):
        return self.toPlainText()

    def set_content(self, text):
        self._internal_change = True
        self.setPlainText(text)
        self._internal_change = False

    def undo(self):
        super().undo()

    def redo(self):
        super().redo()