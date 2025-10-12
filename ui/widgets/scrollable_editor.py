from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QMimeData
from PyQt6.QtGui import QPainter, QPaintEvent, QKeyEvent, QPen, QColor, QTextOption, QTextCursor, QTextBlockFormat
from PyQt6.QtWidgets import QWidget, QTextEdit
import jaconv
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


class ScrollableAnswerEditor(QTextEdit):
    """
    罫線と行番号が統合された、スクロール可能なテキストエディタウィジェット。
    """
    contentModified = pyqtSignal()

    def __init__(
        self,
        config: TextEditorConfig,
        parent: Optional[QWidget] = None,
        columns: int = 30,
        rows: int = 92,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.max_chars = columns
        self.max_lines = rows
        self._internal_change = False

        self.setFont(self.config.get_font())
        self.set_editor_width()
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)

        # --- Line Number Area ---
        self.line_number_widget = LineNumberWidget(self)
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.verticalScrollBar().valueChanged.connect(
            lambda value: self.line_number_widget.update()
        )
        self.update_line_number_area_width(0)
        
        self.set_line_spacing()

        # --- Connections ---
        self.textChanged.connect(self._on_text_changed)

        # --- Style ---
        bg_color = self.config.editor_background_color.name()
        self.setStyleSheet(f"background-color: {bg_color}; border: none;")

    def _on_text_changed(self) -> None:
        if self._internal_change:
            return

        self._internal_change = True
        try:
            # --- 行数制限 ---　必要になったらコメントアウトを解除する
            # visual_lines = self.get_visual_line_count()
            # if visual_lines > self.max_lines:
            #     # 92行目までのテキストを切り出す
            #     visual_line_count = 0
            #     position_to_cut = -1
            #     block = self.document().firstBlock()
            #     while block.isValid():
            #         layout = block.layout()
            #         lines_in_block = layout.lineCount() if layout else 1
                    
            #         if visual_line_count + lines_in_block >= self.max_lines:
            #             lines_to_keep = self.max_lines - visual_line_count
            #             line = layout.lineAt(lines_to_keep - 1)
            #             position_to_cut = block.position() + line.textStart() + line.textLength()
            #             break
                    
            #         visual_line_count += lines_in_block
            #         block = block.next()

            #     if position_to_cut != -1:
            #         current_text = self.toPlainText()
            #         new_text = current_text[:position_to_cut]
            #         self.setPlainText(new_text)
                    
            #         cursor = self.textCursor()
            #         cursor.movePosition(QTextCursor.MoveOperation.End)
            #         self.setTextCursor(cursor)

            # --- 全角変換 ---
            cursor = self.textCursor()
            original_position = cursor.position()
            
            text = self.toPlainText()
            full_width_text = jaconv.h2z(text, kana=True, ascii=True, digit=True)

            if text != full_width_text:
                # self.setPlainText(full_width_text)  # undoスタックがクリアされるため使用しない
                
                # テキストの差分を検出し、カーソル操作で置換する
                cursor.beginEditBlock()
                for i, (char_original, char_converted) in enumerate(zip(text, full_width_text)):
                    if char_original != char_converted:
                        temp_cursor = self.textCursor()
                        temp_cursor.setPosition(i)
                        temp_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
                        temp_cursor.insertText(char_converted)
                cursor.endEditBlock()

                # カーソル位置を復元
                cursor.setPosition(min(original_position, len(full_width_text)))
                self.setTextCursor(cursor)

            # テキスト変更後に必ず行高さを再設定する
            self.set_line_spacing()
        finally:
            self._internal_change = False

        self.contentModified.emit()

    def get_visual_line_count(self) -> int:
        """折り返しを考慮した総行数を計算する。"""
        total_lines = 0
        block = self.document().firstBlock()
        while block.isValid():
            layout = block.layout()
            total_lines += layout.lineCount() if layout else 1
            block = block.next()
        return total_lines

    def get_line_number_area_width(self) -> int:
        """行番号エリアの幅を計算して返す。"""
        return 60

    @property
    def calculated_line_height(self) -> float:
        """設定された行間のパーセンテージを考慮した実際の行の高さを計算して返す。"""
        # fontMetrics().height() ではなく lineSpacing() を使うことで、より正確な行高を得る
        return self.fontMetrics().lineSpacing() * (self.config.line_height / 100.0)

    def update_line_number_area_width(self, new_block_count: int) -> None:
        """行番号エリアの幅を更新し、マージンを設定する。"""
        self.setViewportMargins(
            self.get_line_number_area_width() + self.config.padding_left,
            self.config.padding_top,
            self.config.padding_right,
            self.config.padding_bottom
        )

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
        """行番号ウィジェットの描画イベント。折り返しを考慮し、常に全行表示する。"""
        painter = QPainter(self.line_number_widget)
        painter.fillRect(event.rect(), self.config.line_number_bg_color)
        painter.setPen(self.config.line_number_border_color)
        painter.drawLine(event.rect().width() - 1, 0, event.rect().width() - 1, self.height())
        painter.setPen(self.config.line_number_color)


        # ビューポートの左上の座標に対応するカーソルを取得
        first_visible_cursor = self.cursorForPosition(event.rect().topLeft())
        first_visible_block = first_visible_cursor.block()

        # 開始位置までの表示行番号を計算
        visual_line_number = 0
        block = self.document().firstBlock()
        while block.isValid() and block != first_visible_block:
            layout = block.layout()
            if layout:
                visual_line_number += layout.lineCount()
            else:
                visual_line_number += 1
            block = block.next()

        # 描画ループ
        block = first_visible_block
        doc_layout = self.document().documentLayout()
        offset_y = self.verticalScrollBar().value()
        
        # Check if block is valid before getting its bounding rect
        if not block.isValid():
            super().paintEvent(event)
            return
            
        top = doc_layout.blockBoundingRect(block).top() - offset_y
        
        while block.isValid() and top <= event.rect().bottom():
            block_rect = doc_layout.blockBoundingRect(block)
            layout = block.layout()
            line_count_in_block = layout.lineCount() if layout else 1
            
            for i in range(line_count_in_block):
                line_top = top + (i * self.calculated_line_height)

                if line_top >= event.rect().top() and line_top <= event.rect().bottom():
                    page_number = (visual_line_number // 23) + 1
                    line_in_page = (visual_line_number % 23) + 1
                    
                    if line_in_page == 1:
                        number = f"{page_number}頁   {line_in_page}"
                    else:
                        number = str(line_in_page)
                    
                    painter.drawText(0, int(line_top), self.line_number_widget.width() - 5, int(self.calculated_line_height), Qt.AlignmentFlag.AlignRight, number)

                visual_line_number += 1
            
            top += line_count_in_block * self.calculated_line_height
            block = block.next()

        # テキストがない部分の行番号を描画
        calculated_height = self.calculated_line_height
        if calculated_height <= 0:
            return

        while top < event.rect().bottom() and visual_line_number < self.max_lines:
            page_number = (visual_line_number // 23) + 1
            line_in_page = (visual_line_number % 23) + 1
            
            if line_in_page == 1:
                number = f"{page_number}頁   {line_in_page}"
            else:
                number = str(line_in_page)
            
            # Use calculated_height for drawing empty lines
            painter.drawText(0, int(top), self.line_number_widget.width() - 5, int(calculated_height), Qt.AlignmentFlag.AlignRight, number)
            
            top += calculated_height
            visual_line_number += 1

    def paintEvent(self, event: QPaintEvent) -> None:
        """エディタの背景に罫線を描画する。常にエディタ全体に描画する。"""
        # 先にデフォルトの描画を行い、その上に罫線を描画する
        super().paintEvent(event)
        
        painter = QPainter(self.viewport())
        painter.setPen(QPen(self.config.line_color, 1))

        # 描画開始位置の計算
        first_visible_cursor = self.cursorForPosition(event.rect().topLeft())
        block = first_visible_cursor.block()
        doc_layout = self.document().documentLayout()
        offset_y = self.verticalScrollBar().value()

        if not block.isValid():
            super().paintEvent(event)
            return

        top = doc_layout.blockBoundingRect(block).top() - offset_y

        # テキストがある部分の描画
        while block.isValid() and top <= event.rect().bottom():
            block_rect = doc_layout.blockBoundingRect(block)
            layout = block.layout()
            line_count_in_block = layout.lineCount() if layout else 1
            for i in range(line_count_in_block):
                baseline = top + ((i + 1) * self.calculated_line_height)
                painter.drawLine(0, int(baseline), self.viewport().width(), int(baseline))

            top += line_count_in_block * self.calculated_line_height
            block = block.next()

        # テキストがない部分の描画（エディタの高さまで罫線を引く）
        y = top
        calculated_height = self.calculated_line_height
        if calculated_height <= 0:
            super().paintEvent(event)
            return

        while y < self.viewport().height():
            baseline = y + calculated_height
            painter.drawLine(0, int(baseline), self.viewport().width(), int(baseline))
            y += calculated_height


    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Enterキーで改行を挿入する。"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.insertPlainText('\n')
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source: QMimeData) -> None:
        """プレーンテキストのみをペーストし、すべて全角に変換する。"""
        if source.hasText():
            text = source.text()
            converted_text = jaconv.h2z(text, kana=True, ascii=True, digit=True)
            self.insertPlainText(converted_text)

    def set_line_spacing(self) -> None:
        """フォントサイズと設定された行の高さに基づいて、固定の行高をすべての行に適用する。"""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        doc = self.document()
        block = doc.begin()

        # フォントメトリクスから計算した固定の高さを設定
        fixed_height = self.fontMetrics().lineSpacing() * (self.config.line_height / 100.0)

        while block.isValid():
            block_format = block.blockFormat()
            block_format.setLineHeight(fixed_height, QTextBlockFormat.LineHeightTypes.FixedHeight.value)
            temp_cursor = QTextCursor(block)
            temp_cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            temp_cursor.setBlockFormat(block_format)
            block = block.next()
        cursor.endEditBlock()
        self.update()

    def get_content(self) -> str:
        return self.toPlainText()

    def set_editor_width(self) -> None:
        """設定された1行あたりの文字数に基づいてエディタの幅を計算し、設定する。"""
        font_metrics = self.fontMetrics()
        # 'あ' を基準文字として使用
        char_width = font_metrics.horizontalAdvance('あ')
        
        # 行番号エリアの幅を取得
        line_number_area_width = self.get_line_number_area_width()
        
        # 総幅 = (文字幅 * 1行あたりの文字数) + 行番号エリアの幅 + 少しの余裕
        total_width = (char_width * self.config.chars_per_line) + line_number_area_width + 15  # 15pxのマージン
        
        self.setFixedWidth(total_width)

    def set_content(self, text: str) -> None:
        self._internal_change = True
        try:
            self.setPlainText(text)
            self.document().clearUndoRedoStacks()
            self.set_line_spacing()
        finally:
            self._internal_change = False
