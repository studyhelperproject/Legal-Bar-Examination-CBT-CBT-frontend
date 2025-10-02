from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QMimeData
from PyQt6.QtGui import QPainter, QPaintEvent, QKeyEvent, QPen, QColor
from PyQt6.QtWidgets import QWidget, QTextEdit, QPlainTextEdit

if TYPE_CHECKING:
    from .text_editor_config import TextEditorConfig


class LineNumberWidget(QWidget):
    """行番号を表示するためのウィジェット。"""

    def __init__(self, editor: ScrollableAnswerEditor) -> None:
        super().__init__(editor)
        self.editor = editor
        self.config = editor.config

    def sizeHint(self) -> QSize:
        return QSize(self.editor.get_line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:
        self.editor.line_number_paint_event(event)


class ScrollableAnswerEditor(QPlainTextEdit):
    """
    罫線と行番号が統合された、スクロール可能なテキストエディタウィジェット。
    """
    contentModified = pyqtSignal()

    def __init__(
        self,
        config: TextEditorConfig,
        parent: Optional[QWidget] = None,
        columns: int = 30,
        rows: int = 23,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.max_chars = columns
        self.max_lines = rows
        self._internal_change = False

        self.setFont(self.config.get_font())
        self.setWordWrapMode(Qt.TextFormat.WrapAnywhere)

        # --- Line Number Area ---
        self.line_number_widget = LineNumberWidget(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

        # --- Connections ---
        self.textChanged.connect(self._on_text_changed)

        # --- Style ---
        bg_color = self.config.editor_background_color.name()
        self.setStyleSheet(f"background-color: {bg_color}; border: none;")

    def _on_text_changed(self) -> None:
        if self._internal_change:
            return
        self.contentModified.emit()

    def get_line_number_area_width(self) -> int:
        """行番号エリアの幅を計算して返す。"""
        return 40

    def update_line_number_area_width(self, new_block_count: int) -> None:
        """行番号エリアの幅を更新し、マージンを設定する。"""
        self.setViewportMargins(self.get_line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        """
        エディタのスクロールに応じて行番号エリアを更新（スクロール）する。
        """
        if dy:
            self.line_number_widget.scroll(0, dy)
        else:
            self.line_number_widget.update(0, rect.y(), self.line_number_widget.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event: QPaintEvent) -> None:
        """リサイズ時に行番号エリアの位置を調整する。"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_widget.setGeometry(QRect(cr.left(), cr.top(), self.get_line_number_area_width(), cr.height()))

    def line_number_paint_event(self, event: QPaintEvent) -> None:
        """行番号ウィジェットの描画イベント。"""
        painter = QPainter(self.line_number_widget)
        painter.fillRect(event.rect(), self.config.line_number_bg_color)
        painter.setPen(self.config.line_number_border_color)
        painter.drawLine(event.rect().width() - 1, 0, event.rect().width() - 1, self.height())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(self.config.line_number_color)
        font = self.font()
        font_height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(0, int(top), self.line_number_widget.width() - 5, font_height, Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def paintEvent(self, event: QPaintEvent) -> None:
        """エディタの背景に罫線を描画する。"""
        painter = QPainter(self.viewport())
        painter.setPen(QPen(self.config.line_color, 1))

        font_metrics = self.fontMetrics()
        line_height = font_metrics.height()
        if line_height <= 0: return

        first_block = self.firstVisibleBlock()
        first_block_num = first_block.blockNumber()
        offset = self.contentOffset()

        y = self.blockBoundingGeometry(first_block).translated(offset).top()

        for i in range(first_block_num, self.blockCount()):
            if y > self.viewport().height(): break
            # テキスト描画ベースラインに合わせて罫線を引く
            baseline = y + font_metrics.ascent()
            painter.drawLine(0, int(baseline), self.viewport().width(), int(baseline))
            block = self.document().findBlockByNumber(i)
            if not block.isValid(): break
            y += self.blockBoundingRect(block).height()

        super().paintEvent(event)


    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Enterキーで改行を挿入する。"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.insertPlainText('\n')
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source: QMimeData) -> None:
        """プレーンテキストのみをペーストする。"""
        if source.hasText():
            self.insertPlainText(source.text())

    def get_content(self) -> str:
        return self.toPlainText()

    def set_content(self, text: str) -> None:
        self._internal_change = True
        try:
            self.setPlainText(text)
            self.document().clearUndoRedoStacks()
        finally:
            self._internal_change = False