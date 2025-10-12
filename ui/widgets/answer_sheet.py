from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QColor, QFontMetrics, QTextOption
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QScrollArea, QFrame, QMessageBox
)

from .answer_search_bar import AnswerSearchBar
from .scrollable_editor import ScrollableAnswerEditor
from .text_editor_config import TextEditorConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow

class AnswerSheet(QWidget):
    """
    複数の答案ページ、ナビゲーション、検索機能を管理するコンテナウィジェット。

    `AnswerSheetPageWidget`を複数ページ持ち、`QStackedWidget`で切り替えます。
    文字数カウンター、検索/置換バー、ページナビゲーションUIを提供します。
    """
    contentChanged = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        AnswerSheetのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)
        self.main_window: Optional[MainWindow] = parent

        # --- UI要素の型定義 ---
        self.char_count_label: QLabel
        self.toggle_search_button: QPushButton
        self.answer_undo_button: QPushButton
        self.answer_redo_button: QPushButton
        self.search_bar: AnswerSearchBar
        self.editor: ScrollableAnswerEditor

        # --- エディタ設定 ---
        editor_config = TextEditorConfig()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)

        # 1. 情報バー (文字数, Undo/Redoなど)
        info_bar = QHBoxLayout()
        self.char_count_label = QLabel("0/184行 0/5,520文字")
        self.toggle_search_button = QPushButton("検索")
        self.toggle_search_button.setCheckable(True)
        self.answer_undo_button = QPushButton("元に戻す")
        self.answer_redo_button = QPushButton("やり直し")
        info_bar.addWidget(self.char_count_label)
        info_bar.addStretch()
        info_bar.addWidget(self.toggle_search_button)
        info_bar.addWidget(self.answer_undo_button)
        info_bar.addWidget(self.answer_redo_button)

        # 2. 検索バー (初期状態は非表示)
        self.search_bar = AnswerSearchBar(self)

        # 3. エディタ
        self.editor = ScrollableAnswerEditor(config=editor_config, parent=self)
        self.editor.setWordWrapMode(QTextOption.WrapMode.WordWrap)

        # --- Width Calculation for 30 full-width characters ---
        font_metrics = QFontMetrics(self.editor.font())
        # Calculate the pixel width of 30 full-width characters.
        text_width = font_metrics.horizontalAdvance('あ' * self.editor.max_chars)
        
        # Get other layout metrics.
        line_number_width = self.editor.get_line_number_area_width()
        frame_width = self.editor.frameWidth() * 2
        document_margin = self.editor.document().documentMargin() * 2
        
        # The total width must accommodate all components.
        total_width = text_width + line_number_width + frame_width + document_margin
        
        self.editor.setFixedWidth(int(total_width))

        # すべてのコンポーネントをメインレイアウトに追加
        layout.addLayout(info_bar)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.editor)

        # --- 接続 ---
        self.toggle_search_button.toggled.connect(self.search_bar.setVisible)
        self.answer_undo_button.clicked.connect(self.undo)
        self.answer_redo_button.clicked.connect(self.redo)
        self.editor.contentModified.connect(self._on_content_changed)

        # 検索関連の接続
        self.search_bar.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_bar.next_button.clicked.connect(lambda: self.find_in_answer(forward=True))
        self.search_bar.prev_button.clicked.connect(lambda: self.find_in_answer(forward=False))
        self.search_bar.replace_button.clicked.connect(self.replace_in_answer)
        self.search_bar.replace_all_button.clicked.connect(self.replace_all_in_answer)

        # --- 初期状態 ---
        self.current_page_index: int = 0

        self.update_status_label()

    def _on_content_changed(self) -> None:
        """ページ内容が変更されたときに呼び出されるスロット。ステータスを更新し、シグナルを発行する。"""
        self.update_status_label()
        self.contentChanged.emit()

    def undo(self) -> None:
        """現在のページでUndo操作を実行する。"""
        self.editor.undo()

    def redo(self) -> None:
        """現在のページでRedo操作を実行する。"""
        self.editor.redo()

    # --- 内容とステータス ---

    def update_status_label(self) -> None:
        """全体の行数と文字数を計算し、ステータスラベルを更新する。"""
        content = self.editor.get_content()
        total_chars = len(content)
        max_lines = self.editor.max_lines

        # 折り返しを考慮した総行数を計算
        total_lines = self.editor.get_visual_line_count()

        # 最大文字数2760を直接指定
        self.char_count_label.setText(f"{total_lines}/{max_lines}行 {total_chars}/2760文字")

    # --- 検索と置換ロジック ---

    def _clear_all_highlights(self) -> None:
        """全ページの検索ハイライトをクリアする。"""
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()
        self.editor.setTextCursor(cursor)

    def _on_search_text_changed(self, keyword: str) -> None:
        """検索語が変更されたときに、全ページを対象にハイライトを更新する。"""
        self._clear_all_highlights()
        if not keyword:
            self.search_bar.count_label.setText("0/0")
            return

        total_count = 0
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("yellow"))


        doc = self.editor.document()
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(keyword, cursor)
            if cursor.isNull(): break
            cursor.mergeCharFormat(highlight_format)
            total_count += 1

        self.search_bar.count_label.setText(f"0/{total_count}")

    def find_in_answer(self, forward: bool = True) -> None:
        """現在のページで次または前の検索結果に移動する。"""
        keyword = self.search_bar.search_input.text()
        if not keyword: return

        editor = self.editor
        flags = QTextDocument.FindFlag(0) if forward else QTextDocument.FindFlag.FindBackward

        found_cursor = editor.document().find(keyword, editor.textCursor(), flags)
        if not found_cursor.isNull():
            editor.setTextCursor(found_cursor)
        else:
            QMessageBox.information(self, "検索", "これ以上一致する項目はありません。")

    def replace_in_answer(self) -> None:
        """現在選択されている検索結果を置換し、次の結果に移動する。"""
        keyword = self.search_bar.search_input.text()
        replace_text = self.search_bar.replace_input.text()
        editor = self.editor

        if keyword and editor.textCursor().hasSelection() and editor.textCursor().selectedText() == keyword:
            editor.insertPlainText(replace_text)
        self.find_in_answer(forward=True)

    def replace_all_in_answer(self) -> None:
        """全ページにわたって、すべての検索結果を一括で置換する。"""
        keyword = self.search_bar.search_input.text()
        replace_text = self.search_bar.replace_input.text()
        if not keyword: return

        count = 0
        original_text = self.editor.toPlainText()
        count = original_text.count(keyword)

        if count > 0:
            new_text = original_text.replace(keyword, replace_text)
            self.editor.setPlainText(new_text)
        

        QMessageBox.information(self, "一括置換", f"{count}件の項目を置換しました。")
        self._on_search_text_changed(keyword) # ハイライトを再適用
        self.contentChanged.emit()