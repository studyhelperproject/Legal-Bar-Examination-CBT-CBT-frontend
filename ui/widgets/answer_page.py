from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFontMetrics, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from .answer_editor import AnswerGridEditor

class AnswerSheetPageWidget(QWidget):
    """司法試験用の答案入力ページ。エディタと背景の罫線描画を担当。"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.editor = AnswerGridEditor(self)

        # エディタの背景を透明にして、このウィジェットのpaintEventで描画した罫線が見えるようにする
        self.editor.setStyleSheet("QTextEdit { background-color: transparent; border: none; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 20, 20, 20) # left, top, right, bottom
        layout.addWidget(self.editor)

        self.setFocusProxy(self.editor)
        self.setAutoFillBackground(True) # paintEventを有効にするため

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        font_metrics = QFontMetrics(self.editor.font())
        line_height = font_metrics.height()
        if line_height <= 0:
            return

        # 描画範囲と設定
        top_margin = self.layout().contentsMargins().top()
        left_margin = self.layout().contentsMargins().left()
        right = self.width() - self.layout().contentsMargins().right()

        # 行番号エリアの描画
        line_number_area_width = 40
        painter.fillRect(0, 0, line_number_area_width, self.height(), QColor("#f0f0f0"))
        painter.setPen(QColor("#d0d0d0"))
        painter.drawLine(line_number_area_width, 0, line_number_area_width, self.height())

        # 罫線の描画
        pen = QPen(QColor(220, 220, 220), 1)
        painter.setPen(pen)

        # 23行分の罫線を引く
        for i in range(self.editor.max_lines):
            y = top_margin + (i * line_height) + font_metrics.ascent()
            painter.drawLine(left_margin, y, right, y)

        # 行番号の描画
        painter.setPen(QColor("#888888"))
        for i in range(self.editor.max_lines):
            y = top_margin + (i * line_height) + font_metrics.ascent()
            painter.drawText(5, y - font_metrics.descent(), f"{i+1:2}")

    def get_content(self):
        return self.editor.get_content()

    def set_content(self, text):
        self.editor.set_content(text)

    def undo(self):
        self.editor.undo()

    def redo(self):
        self.editor.redo()