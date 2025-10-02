from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QScrollArea, QFrame, QMessageBox
)

from .answer_search_bar import AnswerSearchBar
from .answer_page import AnswerSheetPageWidget

class AnswerSheet(QWidget):
    """
    複数の答案ページ、ナビゲーション、検索機能を管理するコンテナウィジェット。
    """
    contentChanged = pyqtSignal()
    TOTAL_PAGES = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)

        # --- UI Components ---

        # 1. Info Bar (char count, undo/redo, etc.)
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

        # 2. Search Bar (initially hidden)
        self.search_bar = AnswerSearchBar(self)

        # 3. Page Stack in a Scroll Area
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

        # 4. Navigation Bar
        nav_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("前の頁")
        self.next_page_button = QPushButton("次の頁")
        self.page_indicator = QLabel("1 / 8")
        nav_layout.addWidget(self.prev_page_button)
        nav_layout.addWidget(self.page_indicator)
        nav_layout.addWidget(self.next_page_button)
        nav_layout.addStretch()

        # Add all components to the main layout
        layout.addLayout(info_bar)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.page_scroll)
        layout.addLayout(nav_layout)

        # --- Connections ---
        self.toggle_search_button.toggled.connect(self.search_bar.setVisible)
        self.prev_page_button.clicked.connect(self.go_prev_page)
        self.next_page_button.clicked.connect(self.go_next_page)
        self.answer_undo_button.clicked.connect(self.undo_current)
        self.answer_redo_button.clicked.connect(self.redo_current)

        # Search connections
        self.search_bar.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_bar.next_button.clicked.connect(lambda: self.find_in_answer(forward=True))
        self.search_bar.prev_button.clicked.connect(lambda: self.find_in_answer(forward=False))
        self.search_bar.replace_button.clicked.connect(self.replace_in_answer)
        self.search_bar.replace_all_button.clicked.connect(self.replace_all_in_answer)

        # --- Initial State ---
        self.current_page_index = 0
        self.update_page_controls()
        self.update_status_label()

    def _on_content_changed(self):
        """Emit signal when content changes."""
        self.update_status_label()
        self.contentChanged.emit()

    # --- Page Navigation and Access ---

    def current_page(self) -> AnswerSheetPageWidget:
        return self.pages[self.current_page_index]

    def current_editor(self):
        return self.current_page().editor

    def go_prev_page(self):
        if self.current_page_index > 0:
            self.set_current_page(self.current_page_index - 1)

    def go_next_page(self):
        if self.current_page_index < self.TOTAL_PAGES - 1:
            self.set_current_page(self.current_page_index + 1)

    def set_current_page(self, index):
        self.current_page_index = max(0, min(index, self.TOTAL_PAGES - 1))
        self.page_stack.setCurrentIndex(self.current_page_index)
        self.update_page_controls()
        self.contentChanged.emit()

    def update_page_controls(self):
        self.page_indicator.setText(f"{self.current_page_index + 1} / {self.TOTAL_PAGES}")
        self.prev_page_button.setEnabled(self.current_page_index > 0)
        self.next_page_button.setEnabled(self.current_page_index < self.TOTAL_PAGES - 1)

    def undo_current(self):
        self.current_editor().undo()

    def redo_current(self):
        self.current_editor().redo()

    # --- Content and Status ---

    def update_status_label(self):
        total_lines = sum(p.get_content().count('\n') + 1 for p in self.pages if p.get_content())
        total_chars = sum(len(p.get_content()) for p in self.pages)
        max_lines = self.TOTAL_PAGES * self.pages[0].editor.max_lines
        self.char_count_label.setText(f"{total_lines}/{max_lines}行 {total_chars}文字")

    def get_page_texts(self):
        return [p.get_content() for p in self.pages]

    def set_page_texts(self, texts):
        for i, page in enumerate(self.pages):
            page.set_content(texts[i] if i < len(texts) else "")
        self.update_status_label()
        self.contentChanged.emit()

    # --- Search and Replace Logic ---

    def _clear_all_highlights(self):
        for page in self.pages:
            cursor = page.editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.setCharFormat(QTextCharFormat())
            cursor.clearSelection()
            page.editor.setTextCursor(cursor)

    def _on_search_text_changed(self, keyword):
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
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(highlight_format)
                total_count += 1
        self.search_bar.count_label.setText(f"0/{total_count}")

    def find_in_answer(self, forward=True):
        keyword = self.search_bar.search_input.text()
        if not keyword: return

        editor = self.current_editor()
        flags = QTextDocument.FindFlag(0) if forward else QTextDocument.FindFlag.FindBackward

        found_cursor = editor.document().find(keyword, editor.textCursor(), flags)
        if not found_cursor.isNull():
            editor.setTextCursor(found_cursor)
        else:
            QMessageBox.information(self, "検索", "これ以上一致する項目はありません。")

    def replace_in_answer(self):
        keyword = self.search_bar.search_input.text()
        replace_text = self.search_bar.replace_input.text()
        editor = self.current_editor()

        if keyword and editor.textCursor().hasSelection() and editor.textCursor().selectedText() == keyword:
            editor.insertPlainText(replace_text)
        self.find_in_answer(forward=True)

    def replace_all_in_answer(self):
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
        self._on_search_text_changed(keyword) # Re-highlight
        self.contentChanged.emit()