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
        
        # 設定値
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
        """UIの構築"""
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
        page_widget = AnswerPageWidget()
        
        # 文字数制限の設定
        page_widget.editor.textChanged.connect(lambda: self.enforce_character_limit(page_widget.editor))
        
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

class AnswerPageWidget(QWidget):
    """原稿用紙風の答案ページウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 固定幅での正確なmm単位設定
        # 1mm = 3.7795275590551ピクセル (96 DPI)
        mm_to_px = 3.7795275590551
        
        # 固定の測定値（mm単位）
        text_height_mm = 5      # 文字の高さ: 5mm
        line_spacing_mm = 2     # 改行のスペース: 2mm
        top_margin_mm = 1       # 上余白: 1mm
        bottom_margin_mm = 1    # 下余白: 1mm
        
        # ピクセルに変換（固定値）
        text_height_px = int(text_height_mm * mm_to_px)      # 約19px
        line_spacing_px = int(line_spacing_mm * mm_to_px)     # 約8px
        top_margin_px = int(top_margin_mm * mm_to_px)         # 約4px
        bottom_margin_px = int(bottom_margin_mm * mm_to_px)   # 約4px
        
        # インスタンス変数に保存
        self._text_height_px = text_height_px
        self._line_spacing_px = line_spacing_px
        self._top_margin_px = top_margin_px
        self._bottom_margin_px = bottom_margin_px
        
        # 行の高さ = 文字の高さ + 改行のスペース
        self._total_line_height_px = text_height_px + line_spacing_px  # 約27px
        
        # 文字サイズを30pxに設定
        target_font_size = 30
        
        # 完全等幅フォントを優先
        base_font = QFont("Courier New", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Monaco", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Consolas", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Hiragino Mincho ProN", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("MS Mincho", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Arial Unicode MS", target_font_size)
        
        self._base_font = QFont(base_font)
        self._base_font.setFixedPitch(True)  # 等幅フォントに設定
        self._base_font.setStyleHint(QFont.StyleHint.Monospace)  # モノスペースフォントを強制
        self._base_point_size = self._base_font.pointSizeF() or float(self._base_font.pointSize() or target_font_size)
        
        self.setup_ui()
    
    def setup_ui(self):
        """UIの構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # エディタを作成
        self.editor = AnswerGridEditor(self)
        layout.addWidget(self.editor)
        
        # 描画イベントを有効にする
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        # エディタの背景を透明にして、親の描画が見えるようにする
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: 2px solid #ddd;
                padding: {self._top_margin_px}px 20px {self._bottom_margin_px}px 120px;
                line-height: {self._total_line_height_px / self._text_height_px};
                font-family: 'Courier New', 'Monaco', 'Consolas', 'Hiragino Mincho ProN', 'MS Mincho', monospace;
                font-size: 30px;
                color: black;
                letter-spacing: 0.1em;
            }}
            QTextEdit:focus {{
                border: 2px solid #007acc;
            }}
        """)
        
        # 初期描画を強制
        self.update()
        
        # エディタのリサイズ時に再描画
        self.editor.resized.connect(self.update)
    
    def paintEvent(self, event):
        """背景と行番号を描画"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # 背景を白で塗りつぶし
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # エディタの位置を取得
        editor_rect = self.editor.geometry()
        
        # 行番号エリアの設定
        line_number_width = 100
        line_number_rect = QRect(0, 0, line_number_width, editor_rect.height())
        
        # 行番号エリアをグレーで塗りつぶし
        painter.fillRect(line_number_rect, QColor(240, 240, 240))
        
        # 行番号エリアとテキストエリアの境界線
        pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(pen)
        painter.drawLine(line_number_rect.right(), line_number_rect.top(), 
                        line_number_rect.right(), line_number_rect.bottom())
        
        # QTextEditの実際の行の位置を取得して描画
        document = self.editor.document()
        block_count = document.blockCount()
        
        # 行ごとの水平線を描画
        pen = QPen(QColor(220, 220, 220), 1)
        painter.setPen(pen)
        
        for i in range(block_count):
            block = document.findBlockByNumber(i)
            if block.isValid():
                # ブロックの位置を取得（正しいメソッド呼び出し）
                block_rect = self.editor.document().documentLayout().blockBoundingRect(block)
                # エディタ内での実際の位置を計算
                y = int(editor_rect.y() + 20 + block_rect.y() + self._text_height_px)
                
                # 水平線を描画
                painter.drawLine(line_number_rect.right() + 10, y, 
                               editor_rect.right() - 20, y)
                
                # 行番号を描画
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawText(line_number_rect.x() + 10, y, str(i + 1))
                painter.setPen(QPen(QColor(220, 220, 220), 1))

class AnswerGridEditor(QTextEdit):
    """原稿用紙風のテキストエディタ"""
    
    resized = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 固定幅での正確なmm単位設定
        # 1mm = 3.7795275590551ピクセル (96 DPI)
        mm_to_px = 3.7795275590551
        
        # 固定の測定値（mm単位）
        text_height_mm = 5      # 文字の高さ: 5mm
        line_spacing_mm = 2     # 改行のスペース: 2mm
        top_margin_mm = 1       # 上余白: 1mm
        bottom_margin_mm = 1    # 下余白: 1mm
        
        # ピクセルに変換（固定値）
        text_height_px = int(text_height_mm * mm_to_px)      # 約19px
        line_spacing_px = int(line_spacing_mm * mm_to_px)     # 約8px
        top_margin_px = int(top_margin_mm * mm_to_px)         # 約4px
        bottom_margin_px = int(bottom_margin_mm * mm_to_px)   # 約4px
        
        # インスタンス変数に保存
        self._text_height_px = text_height_px
        self._line_spacing_px = line_spacing_px
        self._top_margin_px = top_margin_px
        self._bottom_margin_px = bottom_margin_px
        
        # 行の高さ = 文字の高さ + 改行のスペース
        self._total_line_height_px = text_height_px + line_spacing_px  # 約27px
        
        # 文字サイズを30pxに設定
        target_font_size = 30
        
        # 完全等幅フォントを優先
        base_font = QFont("Courier New", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Monaco", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Consolas", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Hiragino Mincho ProN", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("MS Mincho", target_font_size)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Arial Unicode MS", target_font_size)
        
        self._base_font = QFont(base_font)
        self._base_font.setFixedPitch(True)  # 等幅フォントに設定
        self._base_font.setStyleHint(QFont.StyleHint.Monospace)  # モノスペースフォントを強制
        self._base_point_size = self._base_font.pointSizeF() or float(self._base_font.pointSize() or target_font_size)
        self.setFont(self._base_font)
        
        # テキストエディタ設定
        self.setAcceptRichText(False)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setUndoRedoEnabled(True)
        
        # 適切なサイズ設定
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # スタイル設定
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: white;
                border: 2px solid #ddd;
                padding: {self._top_margin_px}px 20px {self._bottom_margin_px}px 120px;
                line-height: {self._total_line_height_px / self._text_height_px};
                font-family: 'Courier New', 'Monaco', 'Consolas', 'Hiragino Mincho ProN', 'MS Mincho', monospace;
                font-size: 30px;
                color: black;
                letter-spacing: 0.1em;
            }}
            QTextEdit:focus {{
                border: 2px solid #007acc;
            }}
        """)
        
        self.textChanged.connect(self.enforce_limits)
    
    def keyPressEvent(self, event):
        # エンターキーで改行
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            cursor = self.textCursor()
            cursor.insertText('\n')
            self.setTextCursor(cursor)
            return
        
        # 半角スペースを全角スペースに変換
        if event.text() == ' ':
            cursor = self.textCursor()
            cursor.insertText('　')
            self.setTextCursor(cursor)
            return
        
        # 英数入力モードの場合はアルファベットと数字をそのまま入力
        if event.text() and (event.text().isalnum() or event.text() in '.,!?;:'):
            super().keyPressEvent(event)
            return
        
        # 通常のキー入力はそのまま処理（日本語変換を妨げない）
        super().keyPressEvent(event)
    
    def insertFromMimeData(self, mime_data):
        """ペースト時の処理"""
        if mime_data.hasText():
            text = mime_data.text()
            # 半角スペースを全角スペースに変換
            text = text.replace(' ', '　')
            cursor = self.textCursor()
            cursor.insertText(text)
            self.setTextCursor(cursor)
        else:
            super().insertFromMimeData(mime_data)
    
    def enforce_limits(self):
        """文字数制限を適用"""
        text = self.toPlainText()
        # 最大文字数制限（8ページ × 23行 × 30文字 = 5520文字）
        max_chars = 8 * 23 * 30
        if len(text) > max_chars:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
    
    def resizeEvent(self, event):
        """リサイズイベント"""
        super().resizeEvent(event)
        self.resized.emit()
