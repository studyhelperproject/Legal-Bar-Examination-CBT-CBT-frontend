from typing import Optional

from PyQt6.QtGui import QPainter, QFontMetrics, QPen, QPaintEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from .answer_editor import AnswerGridEditor
from .text_editor_config import TextEditorConfig


class AnswerSheetPageWidget(QWidget):
    """
    司法試験の答案用紙の1ページを表現するウィジェット。

    内部に AnswerGridEditor を持ち、その背景に罫線や行番号を描画する責務を負います。
    エディタ自体の背景は透明にし、このウィジェットの paintEvent で描画された内容が
    透けて見えるように設計されています。
    """

    def __init__(self, config: TextEditorConfig, parent: Optional[QWidget] = None) -> None:
        """
        AnswerSheetPageWidgetのコンストラクタ。

        Args:
            config (TextEditorConfig): エディタのUI設定。
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)
        self.config = config
        self.editor: AnswerGridEditor = AnswerGridEditor(config=config, parent=self)

        # エディタの背景を透明にして、このウィジェットのpaintEventで描画した罫線が見えるようにする
        editor_bg_color = self.config.editor_background_color.name()
        self.editor.setStyleSheet(
            f"QTextEdit {{ background-color: {editor_bg_color}; border: none; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 20, 20, 20)  # left, top, right, bottom
        layout.addWidget(self.editor)

        self.setFocusProxy(self.editor)
        self.setAutoFillBackground(True)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        ウィジェットの背景を描画するイベントハンドラ。

        白い背景、行番号エリア、そしてエディタの行に対応する罫線を描画します。

        Args:
            event (QPaintEvent): Qtから渡されるペイントイベントオブジェクト。
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.config.background_color)

        font_metrics = QFontMetrics(self.editor.font())
        line_height = font_metrics.height()
        if line_height <= 0:
            return

        # 描画範囲と設定
        margins = self.layout().contentsMargins()
        top_margin, left_margin = margins.top(), margins.left()
        right = self.width() - margins.right()

        # 行番号エリアの描画
        line_number_area_width = 40
        painter.fillRect(
            0, 0, line_number_area_width, self.height(), self.config.line_number_bg_color
        )
        painter.setPen(self.config.line_number_border_color)
        painter.drawLine(line_number_area_width, 0, line_number_area_width, self.height())

        # 罫線の描画
        pen = QPen(self.config.line_color, 1)
        painter.setPen(pen)

        for i in range(self.editor.max_lines):
            y = top_margin + (i * line_height) + font_metrics.ascent()
            painter.drawLine(left_margin, y, right, y)

        # 行番号の描画
        painter.setPen(self.config.line_number_color)
        for i in range(self.editor.max_lines):
            y = top_margin + (i * line_height) + font_metrics.ascent()
            painter.drawText(5, y - font_metrics.descent(), f"{i+1:2}")

    def get_content(self) -> str:
        """内部エディタのテキスト内容を取得する。"""
        return self.editor.get_content()

    def set_content(self, text: str) -> None:
        """内部エディタにテキスト内容を設定する。"""
        self.editor.set_content(text)

    def undo(self) -> None:
        """内部エディタのUndo操作を実行する。"""
        self.editor.undo()

    def redo(self) -> None:
        """内部エディタのRedo操作を実行する。"""
        self.editor.redo()