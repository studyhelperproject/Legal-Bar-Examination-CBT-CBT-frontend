# ui/screens/answer_screen.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

class AnswerScreen(QWidget):
    """
    答案入力画面
    - 原稿用紙風の答案入力
    - 複数ページ対応
    - 文字数・行数制限
    - 検索・置換機能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定値（ハードコーディング）
        self.MAX_PAGES = 8
        self.MAX_LINES_PER_PAGE = 23
        self.MAX_CHARS_PER_LINE = 30
        self.FONT_SIZE = 30
        
        # 答案データ
        self.current_page = 0
        self.answer_pages = []
        
        self.setup_ui()
        self.setup_connections()
        self.initialize_answer_pages()
    
    def setup_ui(self):
        """UIの構築 - 全てベタ書き"""
        layout = QVBoxLayout(self)
        
        # 情報バー
        info_layout = QHBoxLayout()
        self.char_count_label = QLabel("0/184行 0/5,520文字 (空白含む)")
        self.search_button = QPushButton("検索")
        self.search_button.setCheckable(True)
        self.undo_button = QPushButton("元に戻す")
        self.redo_button = QPushButton("やり直し")
        
        info_layout.addWidget(self.char_count_label)
        info_layout.addStretch()
        info_layout.addWidget(self.search_button)
        info_layout.addWidget(self.undo_button)
        info_layout.addWidget(self.redo_button)
        
        layout.addLayout(info_layout)
        
        # 検索・置換バー
        self.search_bar = QWidget()
        search_layout = QHBoxLayout(self.search_bar)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索")
        self.search_count_label = QLabel("0/0")
        self.search_prev_button = QPushButton("↑")
        self.search_next_button = QPushButton("↓")
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("置換")
        self.replace_button = QPushButton("置換")
        self.replace_all_button = QPushButton("一括")
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_count_label)
        search_layout.addWidget(self.search_prev_button)
        search_layout.addWidget(self.search_next_button)
        search_layout.addWidget(self.replace_input)
        search_layout.addWidget(self.replace_button)
        search_layout.addWidget(self.replace_all_button)
        
        self.search_bar.setVisible(False)
        layout.addWidget(self.search_bar)
        
        # 答案入力エリア
        self.answer_tab_widget = QTabWidget()
        layout.addWidget(self.answer_tab_widget)
        
        # ページナビゲーション
        nav_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("前の頁")
        self.next_page_button = QPushButton("次の頁")
        self.page_indicator = QLabel("1 / 8")
        
        nav_layout.addWidget(self.prev_page_button)
        nav_layout.addWidget(self.page_indicator)
        nav_layout.addWidget(self.next_page_button)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
    
    def setup_connections(self):
        """接続設定 - 機能ごとに明確に分離"""
        # 検索機能
        self.search_button.toggled.connect(self.toggle_search_bar)
        self.search_input.textChanged.connect(self.search_text)
        self.search_prev_button.clicked.connect(self.search_previous)
        self.search_next_button.clicked.connect(self.search_next)
        
        # 置換機能
        self.replace_button.clicked.connect(self.replace_text)
        self.replace_all_button.clicked.connect(self.replace_all_text)
        
        # ページナビゲーション
        self.prev_page_button.clicked.connect(self.go_to_previous_page)
        self.next_page_button.clicked.connect(self.go_to_next_page)
        
        # タブ切り替え
        self.answer_tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def initialize_answer_pages(self):
        """答案ページを初期化"""
        for i in range(self.MAX_PAGES):
            page_widget = self.create_answer_page(i + 1)
            self.answer_tab_widget.addTab(page_widget, f"第{i + 1}問")
            self.answer_pages.append(page_widget)
    
    def create_answer_page(self, question_number):
        """答案ページを作成"""
        page_widget = QWidget()
        layout = QVBoxLayout(page_widget)
        
        # 原稿用紙風のエディタ
        editor = QTextEdit()
        editor.setFont(QFont("Hiragino Mincho ProN", self.FONT_SIZE))
        editor.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #ddd;
                padding: 20px 20px 20px 120px;
                line-height: 2.0;
                font-family: 'Hiragino Mincho ProN', 'MS Mincho', serif;
                font-size: 30pt;
                color: black;
                letter-spacing: 0.1em;
            }
        """)
        
        # 文字数制限の設定
        editor.textChanged.connect(lambda: self.enforce_character_limit(editor))
        
        layout.addWidget(editor)
        return page_widget
    
    # 各機能のメソッド（冗長でも明確に）
    def toggle_search_bar(self, visible):
        """検索バーの表示切り替え"""
        self.search_bar.setVisible(visible)
        if visible:
            self.search_input.setFocus()
    
    def search_text(self, text):
        """テキストを検索"""
        if not text:
            self.clear_highlights()
            return
        
        current_widget = self.answer_tab_widget.currentWidget()
        if not current_widget:
            return
        
        editor = current_widget.findChild(QTextEdit)
        if not editor:
            return
        
        self.highlight_text(editor, text)
        self.update_search_count(text)
    
    def search_previous(self):
        """前の検索結果に移動"""
        # 実装
        pass
    
    def search_next(self):
        """次の検索結果に移動"""
        # 実装
        pass
    
    def replace_text(self):
        """テキストを置換"""
        # 実装
        pass
    
    def replace_all_text(self):
        """すべてのテキストを置換"""
        # 実装
        pass
    
    def highlight_text(self, editor, text):
        """テキストをハイライト"""
        # 実装
        pass
    
    def clear_highlights(self):
        """ハイライトをクリア"""
        # 実装
        pass
    
    def update_search_count(self, text):
        """検索結果数を更新"""
        # 実装
        pass
    
    def go_to_previous_page(self):
        """前のページに移動"""
        if self.current_page > 0:
            self.current_page -= 1
            self.answer_tab_widget.setCurrentIndex(self.current_page)
            self.update_page_controls()
    
    def go_to_next_page(self):
        """次のページに移動"""
        if self.current_page < self.MAX_PAGES - 1:
            self.current_page += 1
            self.answer_tab_widget.setCurrentIndex(self.current_page)
            self.update_page_controls()
    
    def update_page_controls(self):
        """ページコントロールを更新"""
        self.page_indicator.setText(f"{self.current_page + 1} / {self.MAX_PAGES}")
        self.prev_page_button.setEnabled(self.current_page > 0)
        self.next_page_button.setEnabled(self.current_page < self.MAX_PAGES - 1)
    
    def on_tab_changed(self, index):
        """タブが変更された時の処理"""
        self.current_page = index
        self.update_page_controls()
        self.update_character_count()
    
    def enforce_character_limit(self, editor):
        """文字数制限を適用"""
        text = editor.toPlainText()
        max_chars = self.MAX_LINES_PER_PAGE * self.MAX_CHARS_PER_LINE
        
        if len(text) > max_chars:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            editor.setTextCursor(cursor)
        
        self.update_character_count()
    
    def update_character_count(self):
        """文字数を更新"""
        total_chars = 0
        total_lines = 0
        
        for page_widget in self.answer_pages:
            editor = page_widget.findChild(QTextEdit)
            if editor:
                text = editor.toPlainText()
                total_chars += len(text)
                total_lines += len(text.split('\n'))
        
        max_chars = self.MAX_PAGES * self.MAX_LINES_PER_PAGE * self.MAX_CHARS_PER_LINE
        max_lines = self.MAX_PAGES * self.MAX_LINES_PER_PAGE
        
        self.char_count_label.setText(f"{total_lines}/{max_lines}行 {total_chars}/{max_chars}文字 (空白含む)")
