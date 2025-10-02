from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QScrollArea, QFrame, QMessageBox
)

from .answer_search_bar import AnswerSearchBar
from .answer_page import AnswerSheetPageWidget
from .answer_editor import AnswerGridEditor

if TYPE_CHECKING:
    from ..main_window import MainWindow

class AnswerSheet(QWidget):
    """
    複数の答案ページ、ナビゲーション、検索機能を管理するコンテナウィジェット。

    `AnswerSheetPageWidget`を複数ページ持ち、`QStackedWidget`で切り替えます。
    文字数カウンター、検索/置換バー、ページナビゲーションUIを提供します。
    """
    contentChanged = pyqtSignal()
    TOTAL_PAGES: int = 8

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
        self.page_stack: QStackedWidget
        self.pages: List[AnswerSheetPageWidget]
        self.page_scroll: QScrollArea
        self.prev_page_button: QPushButton
        self.next_page_button: QPushButton
        self.page_indicator: QLabel

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

        # 3. スクロールエリア内のページスタック
        self.page_stack = QStackedWidget()
        self.pages = [AnswerSheetPageWidget(self) for _ in range(self.TOTAL_PAGES)]
        for page in self.pages:
            self.page_stack.addWidget(page)
            page.editor.contentModified.connect(self._on_content_changed)

        self.page_scroll = QScrollArea()
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setWidget(self.page_stack)
        self.page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.page_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 4. ナビゲーションバー
        nav_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("前の頁")
        self.next_page_button = QPushButton("次の頁")
        self.page_indicator = QLabel("1 / 8")
        nav_layout.addWidget(self.prev_page_button)
        nav_layout.addWidget(self.page_indicator)
        nav_layout.addWidget(self.next_page_button)
        nav_layout.addStretch()

        # すべてのコンポーネントをメインレイアウトに追加
        layout.addLayout(info_bar)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.page_scroll)
        layout.addLayout(nav_layout)

        # --- 接続 ---
        self.toggle_search_button.toggled.connect(self.search_bar.setVisible)
        self.prev_page_button.clicked.connect(self.go_prev_page)
        self.next_page_button.clicked.connect(self.go_next_page)
        self.answer_undo_button.clicked.connect(self.undo_current)
        self.answer_redo_button.clicked.connect(self.redo_current)

        # 検索関連の接続
        self.search_bar.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_bar.next_button.clicked.connect(lambda: self.find_in_answer(forward=True))
        self.search_bar.prev_button.clicked.connect(lambda: self.find_in_answer(forward=False))
        self.search_bar.replace_button.clicked.connect(self.replace_in_answer)
        self.search_bar.replace_all_button.clicked.connect(self.replace_all_in_answer)

        # --- 初期状態 ---
        self.current_page_index: int = 0
        self.update_page_controls()
        self.update_status_label()

    def _on_content_changed(self) -> None:
        """ページ内容が変更されたときに呼び出されるスロット。ステータスを更新し、シグナルを発行する。"""
        self.update_status_label()
        self.contentChanged.emit()

    # --- ページナビゲーションとアクセス ---

    def current_page(self) -> AnswerSheetPageWidget:
        """現在表示されているページウィジェットを返す。"""
        return self.pages[self.current_page_index]

    def current_editor(self) -> AnswerGridEditor:
        """現在表示されているページのエディタウィジェットを返す。"""
        return self.current_page().editor

    def go_prev_page(self) -> None:
        """前のページに移動する。"""
        if self.current_page_index > 0:
            self.set_current_page(self.current_page_index - 1)

    def go_next_page(self) -> None:
        """次のページに移動する。"""
        if self.current_page_index < self.TOTAL_PAGES - 1:
            self.set_current_page(self.current_page_index + 1)

    def set_current_page(self, index: int) -> None:
        """指定されたインデックスのページを表示する。"""
        self.current_page_index = max(0, min(index, self.TOTAL_PAGES - 1))
        self.page_stack.setCurrentIndex(self.current_page_index)
        self.update_page_controls()
        self.contentChanged.emit()

    def update_page_controls(self) -> None:
        """ページインジケーターとナビゲーションボタンの状態を更新する。"""
        self.page_indicator.setText(f"{self.current_page_index + 1} / {self.TOTAL_PAGES}")
        self.prev_page_button.setEnabled(self.current_page_index > 0)
        self.next_page_button.setEnabled(self.current_page_index < self.TOTAL_PAGES - 1)

    def undo_current(self) -> None:
        """現在のページでUndo操作を実行する。"""
        self.current_editor().undo()

    def redo_current(self) -> None:
        """現在のページでRedo操作を実行する。"""
        self.current_editor().redo()

    # --- 内容とステータス ---

    def update_status_label(self) -> None:
        """全体の行数と文字数を計算し、ステータスラベルを更新する。"""
        total_lines = sum(p.get_content().count('\n') + 1 for p in self.pages if p.get_content())
        total_chars = sum(len(p.get_content()) for p in self.pages)
        max_lines = self.TOTAL_PAGES * self.pages[0].editor.max_lines
        self.char_count_label.setText(f"{total_lines}/{max_lines}行 {total_chars}文字")

    def get_page_texts(self) -> List[str]:
        """全ページのテキスト内容をリストとして取得する。"""
        return [p.get_content() for p in self.pages]

    def set_page_texts(self, texts: List[str]) -> None:
        """リストから全ページのテキスト内容を設定する。"""
        for i, page in enumerate(self.pages):
            page.set_content(texts[i] if i < len(texts) else "")
        self.update_status_label()
        self.contentChanged.emit()

    # --- 検索と置換ロジック ---

    def _clear_all_highlights(self) -> None:
        """全ページの検索ハイライトをクリアする。"""
        for page in self.pages:
            cursor = page.editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.setCharFormat(QTextCharFormat())
            cursor.clearSelection()
            page.editor.setTextCursor(cursor)

    def _on_search_text_changed(self, keyword: str) -> None:
        """検索語が変更されたときに、全ページを対象にハイライトを更新する。"""
        self._clear_all_highlights()
        if not keyword:
            self.search_bar.count_label.setText("0/0")
            return

        total_count = 0
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("yellow"))

        for page in self.pages:
            doc = page.editor.document()
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

        editor = self.current_editor()
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
        editor = self.current_editor()

        if keyword and editor.textCursor().hasSelection() and editor.textCursor().selectedText() == keyword:
            editor.insertPlainText(replace_text)
        self.find_in_answer(forward=True)

    def replace_all_in_answer(self) -> None:
        """全ページにわたって、すべての検索結果を一括で置換する。"""
        keyword = self.search_bar.search_input.text()
        replace_text = self.search_bar.replace_input.text()
        if not keyword: return

        count = 0
        for page in self.pages:
            original_text = page.get_content()
            if keyword in original_text:
                count += original_text.count(keyword)
                new_text = original_text.replace(keyword, replace_text)
                page.set_content(new_text)

        QMessageBox.information(self, "一括置換", f"{count}件の項目を置換しました。")
        self._on_search_text_changed(keyword) # ハイライトを再適用
        self.contentChanged.emit()