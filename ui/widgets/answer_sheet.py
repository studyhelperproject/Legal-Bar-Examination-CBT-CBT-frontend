from PyQt6.QtCore import pyqtSignal, Qt, QSize, QRect, QTimer, QEvent
from PyQt6.QtGui import QFont, QFontInfo, QTextOption, QTextCursor, QPainter, QColor, QFontMetrics, QPen
from PyQt6.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QStackedWidget, QFrame,
    QScrollArea, QLabel, QLineEdit, QPushButton
)

try:
    from PyQt6.QtWidgets import QWIDGETSIZE_MAX
except ImportError:  # Fallback constant defined in Qt
    QWIDGETSIZE_MAX = 16777215


class AnswerGridEditor(QTextEdit):
    """司法試験用の答案入力テキストエディタ。"""

    cellMetricsChanged = pyqtSignal()
    resized = pyqtSignal()

    def __init__(self, parent=None, columns=30, rows=23):
        super().__init__(parent)
        self.max_chars = columns
        self.max_lines = rows
        self._internal_change = False
        self._scale = 1.0

        # 全角文字用のフォント設定（画像と同じサイズに調整）
        base_font = QFont("Hiragino Mincho ProN", 30)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("MS Mincho", 30)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Arial Unicode MS", 30)
        self._base_font = QFont(base_font)
        self._base_point_size = self._base_font.pointSizeF() or float(self._base_font.pointSize() or 30)
        self.setFont(self._base_font)

        # テキストエディタ設定
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setUndoRedoEnabled(True)

        # 適切なサイズ設定
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # スタイル設定
        self.setStyleSheet("""
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
            QTextEdit:focus {
                border: 2px solid #007acc;
            }
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

    def _convert_to_fullwidth(self, text):
        """半角アルファベットを全角に変換"""
        result = ""
        for char in text:
            if 'a' <= char <= 'z':
                result += chr(ord('ａ') + (ord(char) - ord('a')))
            elif 'A' <= char <= 'Z':
                result += chr(ord('Ａ') + (ord(char) - ord('A')))
            else:
                result += char
        return result

    def _convert_digits_to_fullwidth(self, text):
        """半角数字を全角に変換"""
        result = ""
        for char in text:
            if '0' <= char <= '9':
                result += chr(ord('０') + (ord(char) - ord('0')))
            else:
                result += char
        return result

    def base_size(self):
        return QSize(600, 400)

    def total_size(self):
        return self.size()

    def cell_size(self):
        return QSize(20, 20)

    def enforce_limits(self):
        if self._internal_change:
            return
        # 文字数制限のチェック
        text = self.toPlainText()
        if len(text) > self.max_chars * self.max_lines:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self.setTextCursor(cursor)

    def set_display_scale(self, scale):
        scale = max(scale, 0.25)
        if abs(scale - self._scale) < 1e-4:
            return
        self._scale = scale
        font = QFont(self._base_font)
        if self._base_point_size > 0:
            font.setPointSizeF(self._base_point_size * scale)
        self.setFont(font)

    def insertFromMimeData(self, source):
        text = source.text()
        if text:
            # 半角スペースのみ全角に変換、アルファベットと数字はそのまま
            normalized = text.replace(' ', '　')
            cursor = self.textCursor()
            cursor.insertText(normalized)
            return
        super().insertFromMimeData(source)

    def _normalize_text(self, text):
        """テキストを全角に正規化"""
        result = ""
        for char in text:
            if char == ' ':
                result += '　'
            elif 'a' <= char <= 'z':
                result += chr(ord('ａ') + (ord(char) - ord('a')))
            elif 'A' <= char <= 'Z':
                result += chr(ord('Ａ') + (ord(char) - ord('A')))
            elif '0' <= char <= '9':
                result += chr(ord('０') + (ord(char) - ord('0')))
            else:
                result += char
        return result

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()
        # 親ウィジェットの背景も更新
        if self.parent():
            self.parent().update()


class AnswerGridBackground(QWidget):
    """答案エディタの背後に原稿用紙風の罫線を描画するウィジェット。"""

    def __init__(self, editor: AnswerGridEditor, parent=None):
        super().__init__(parent)
        self._editor = editor
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._editor.cellMetricsChanged.connect(self._sync_with_editor)
        self._sync_with_editor()

    def _sync_with_editor(self):
        size = self._editor.total_size()
        self.setMinimumSize(size)
        self.setMaximumSize(size)
        self.resize(size)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        if not self._editor:
            return

        # 行の高さを計算（フォントメトリクスから）
        font_metrics = QFontMetrics(self._editor.font())
        line_height = font_metrics.height()
        ascent = font_metrics.ascent()

        if line_height <= 0:
            return

        rect = self.rect()
        x_start = rect.x() + 15  # パディングを考慮
        y_start = rect.y() + 15  # パディングを考慮
        x_end = rect.right() - 15
        y_end = rect.bottom() - 15

        # 行番号エリアの幅
        line_number_width = 50

        # 行番号エリアの背景を描画
        painter.fillRect(x_start, y_start, line_number_width, y_end - y_start, QColor(248, 248, 248))

        # 行番号エリアの右端に線を描画
        pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(pen)
        painter.drawLine(x_start + line_number_width, y_start, x_start + line_number_width, y_end)

        # 行ごとの水平線を描画
        pen = QPen(QColor(220, 220, 220), 1)
        painter.setPen(pen)

        y = y_start + line_height
        line_number = 1
        while y <= y_end:
            # 水平線を描画
            painter.drawLine(x_start + line_number_width + 5, y, x_end, y)

            # 行番号を描画
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawText(x_start + 5, y - ascent + line_height, f"頁1 {line_number}")

            # 次の行に移動
            y += line_height
            line_number += 1


class AnswerSheetPageWidget(QWidget):
    """司法試験用の答案入力ページ。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = AnswerGridEditor(self)

        # レイアウト設定
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.editor)

        # 描画を有効化するための属性設定
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)

        # エディタの背景を透明にして、親の描画が見えるようにする
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: 2px solid #ddd;
                padding: 20px 20px 20px 120px;
                line-height: 2.0;
                font-family: 'Hiragino Mincho ProN', 'MS Mincho', serif;
                font-size: 30pt;
                color: black;
                letter-spacing: 0.1em;
            }
            QTextEdit:focus {
                border: 2px solid #007acc;
            }
        """)

        self.setFocusProxy(self.editor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 初期描画を強制
        self.update()

        self._scale = 1.0

    def paintEvent(self, event):
        # 背景を描画
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # 全体の背景を白で塗りつぶし
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # エディタの位置とサイズを取得
        editor_rect = self.editor.geometry()

        # 行の高さを計算
        font_metrics = QFontMetrics(self.editor.font())
        line_height = font_metrics.height()
        ascent = font_metrics.ascent()

        if line_height <= 0:
            return

        # 行番号エリアの幅を大きくする
        line_number_width = 100

        # 行番号エリアの背景を描画
        line_number_rect = QRect(editor_rect.x() + 20, editor_rect.y() + 20,
                                line_number_width, editor_rect.height() - 40)
        painter.fillRect(line_number_rect, QColor(248, 248, 248))

        # 行番号エリアの右端に線を描画
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
                y = int(editor_rect.y() + 20 + block_rect.y() + ascent)

                # 水平線を描画
                painter.drawLine(line_number_rect.right() + 10, y,
                               editor_rect.right() - 20, y)

                # 行番号を描画
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawText(line_number_rect.x() + 10, y, str(i + 1))
                painter.setPen(QPen(QColor(220, 220, 220), 1))

    def base_size(self):
        return QSize(600, 400)

    def current_size(self):
        return self.size()

    def set_scale(self, scale):
        scale = max(scale, 0.25)
        if abs(scale - self._scale) < 1e-4:
            return
        self._scale = scale
        self.editor.set_display_scale(scale)

    def sync_editor_size(self):
        pass


class AnswerSheet(QWidget):
    contentChanged = pyqtSignal()
    TOTAL_PAGES = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)

        self.search_replace_bar = QWidget()
        search_layout = QHBoxLayout(self.search_replace_bar)
        self.answer_search_input = QLineEdit()
        self.answer_search_input.setPlaceholderText("検索")
        self.search_count_label = QLabel("0/0")
        self.search_prev_button = QPushButton("↑")
        self.search_next_button = QPushButton("↓")
        self.answer_replace_input = QLineEdit()
        self.answer_replace_input.setPlaceholderText("置換")
        self.answer_replace_button = QPushButton("置換")
        self.answer_replace_all_button = QPushButton("一括")
        search_layout.addWidget(self.answer_search_input)
        search_layout.addWidget(self.search_count_label)
        search_layout.addWidget(self.search_prev_button)
        search_layout.addWidget(self.search_next_button)
        search_layout.addWidget(self.answer_replace_input)
        search_layout.addWidget(self.answer_replace_button)
        search_layout.addWidget(self.answer_replace_all_button)
        self.search_replace_bar.setVisible(False)

        info_bar = QHBoxLayout()
        self.char_count_label = QLabel("0/184行 0/5,520文字 (空白含む)")
        self.toggle_search_button = QPushButton("検索")
        self.toggle_search_button.setCheckable(True)
        self.answer_undo_button = QPushButton("元に戻す")
        self.answer_redo_button = QPushButton("やり直し")
        info_bar.addWidget(self.char_count_label)
        info_bar.addStretch()
        info_bar.addWidget(self.toggle_search_button)
        info_bar.addWidget(self.answer_undo_button)
        info_bar.addWidget(self.answer_redo_button)

        self.main_window = getattr(parent, 'main_window', None)

        self.page_stack = QStackedWidget()
        self.pages = []
        self.page_widgets = []
        for _ in range(self.TOTAL_PAGES):
            page_widget = AnswerSheetPageWidget(self)
            page_widget.main_window = None
            self.page_stack.addWidget(page_widget)
            self.pages.append(page_widget.editor)
            self.page_widgets.append(page_widget)
            page_widget.editor.textChanged.connect(self._handle_page_text_changed)

        self.page_scroll = QScrollArea()
        self.page_scroll.setWidgetResizable(False)
        self.page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.page_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.page_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.page_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.page_scroll.setWidget(self.page_stack)
        self.page_scroll.viewport().installEventFilter(self)

        self._scale = 1.0
        self._base_page_size = self.page_widgets[0].base_size() if self.page_widgets else QSize(1, 1)
        self._apply_scale(self._scale)

        nav_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("前の頁")
        self.next_page_button = QPushButton("次の頁")
        self.page_indicator = QLabel("1 / 8")
        nav_layout.addWidget(self.prev_page_button)
        nav_layout.addWidget(self.page_indicator)
        nav_layout.addWidget(self.next_page_button)
        nav_layout.addStretch()

        layout.addLayout(info_bar)
        layout.addWidget(self.search_replace_bar)
        layout.addWidget(self.page_scroll)
        layout.addLayout(nav_layout)

        self.prev_page_button.clicked.connect(self.go_prev_page)
        self.next_page_button.clicked.connect(self.go_next_page)
        self.current_page_index = 0
        self.update_page_controls()
        self.update_status_label()
        QTimer.singleShot(0, self._update_scale)

    def _handle_page_text_changed(self):
        editor = self.sender()
        if hasattr(editor, '_internal_change') and editor._internal_change:
            return
        self.update_status_label()
        self.contentChanged.emit()

    def _apply_scale(self, scale):
        if not self.page_widgets:
            return
        self._scale = scale
        for widget in self.page_widgets:
            widget.set_scale(scale)
        size = self.page_widgets[0].current_size()
        target_height = size.height()
        target_width = size.width()
        self.page_stack.setMinimumSize(QSize(0, 0))
        self.page_stack.setMaximumHeight(target_height)
        self.page_stack.setMaximumWidth(QWIDGETSIZE_MAX)
        self.page_stack.resize(target_width, target_height)
        self.page_stack.updateGeometry()

    def _update_scale(self):
        if not self.page_widgets:
            return
        viewport = self.page_scroll.viewport() if hasattr(self, 'page_scroll') else None
        if not viewport:
            return
        base_width = max(1, self._base_page_size.width())
        width = viewport.width()
        if width <= 0:
            return
        scale = max(1.0, width / base_width)
        if abs(scale - self._scale) > 1e-3:
            self._apply_scale(scale)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scale()

    def eventFilter(self, obj, event):
        if hasattr(self, 'page_scroll') and obj is self.page_scroll.viewport():
            if event.type() == QEvent.Type.Resize:
                self._update_scale()
        return super().eventFilter(obj, event)

    def set_main_window(self, main_window):
        self.main_window = main_window
        for widget in getattr(self, 'page_widgets', []):
            widget.main_window = main_window

    def current_editor(self):
        return self.pages[self.current_page_index]

    def go_prev_page(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.page_stack.setCurrentIndex(self.current_page_index)
            self.update_page_controls()
            self.contentChanged.emit()

    def go_next_page(self):
        if self.current_page_index < self.TOTAL_PAGES - 1:
            self.current_page_index += 1
            self.page_stack.setCurrentIndex(self.current_page_index)
            self.update_page_controls()
            self.contentChanged.emit()

    def update_page_controls(self):
        self.page_indicator.setText(f"{self.current_page_index + 1} / {self.TOTAL_PAGES}")
        self.prev_page_button.setEnabled(self.current_page_index > 0)
        self.next_page_button.setEnabled(self.current_page_index < self.TOTAL_PAGES - 1)

    def set_current_page(self, index):
        index = max(0, min(index, self.TOTAL_PAGES - 1))
        self.current_page_index = index
        self.page_stack.setCurrentIndex(index)
        self.update_page_controls()

    def undo_current(self):
        self.current_editor().undo()

    def redo_current(self):
        self.current_editor().redo()

    def total_character_count(self):
        limit = self.TOTAL_PAGES * self.pages[0].max_chars * self.pages[0].max_lines
        total_chars = 0
        for editor in self.pages:
            text = editor.toPlainText()
            lines = text.split('\n')
            if text.endswith('\n'):
                lines.append('')
            for line in lines[:editor.max_lines]:
                total_chars += len(line)
        return min(total_chars, limit)

    def total_line_count(self):
        total = 0
        for editor in self.pages:
            text = editor.toPlainText()
            if not text:
                continue
            lines = text.split('\n')
            if text.endswith('\n'):
                lines.append('')
            total += min(len(lines), editor.max_lines)
        return min(total, self.TOTAL_PAGES * self.pages[0].max_lines)

    def update_status_label(self):
        total_lines = self.total_line_count()
        total_chars = self.total_character_count()
        max_lines = self.TOTAL_PAGES * self.pages[0].max_lines
        max_chars = self.TOTAL_PAGES * self.pages[0].max_chars * self.pages[0].max_lines
        self.char_count_label.setText(f"{total_lines}/{max_lines}行 {total_chars}/{max_chars}文字 (空白含む)")

    def get_page_texts(self):
        return [editor.toPlainText() for editor in self.pages]

    def set_page_texts(self, texts):
        for index, editor in enumerate(self.pages):
            text = texts[index] if index < len(texts) else ""
            editor._internal_change = True
            editor.setPlainText(text)
            editor._internal_change = False
        self.update_status_label()
        self.update_page_controls()
        self.contentChanged.emit()

    def forward_overflow(self, source_editor, overflow_text):
        try:
            start_index = self.pages.index(source_editor)
        except ValueError:
            return
        next_index = start_index + 1
        overflow_text = overflow_text.lstrip('\n')
        while overflow_text and next_index < self.TOTAL_PAGES:
            editor = self.pages[next_index]
            existing = editor.toPlainText()
            if existing:
                combined_text = overflow_text.rstrip('\n')
                if combined_text and not combined_text.endswith('\n'):
                    combined_text += '\n'
                combined_text += existing
            else:
                combined_text = overflow_text

            lines = editor._split_lines(combined_text)
            retained_lines = lines[:editor.max_lines]
            overflow_lines = lines[editor.max_lines:]
            retained = '\n'.join(retained_lines)
            overflow_text = '\n'.join(overflow_lines)
            editor._internal_change = True
            editor.setPlainText(retained)
            editor._internal_change = False
            editor._check_overflow()
            next_index += 1
        self.update_status_label()
        self.contentChanged.emit()

    def pull_from_next(self, source_editor):
        try:
            start_index = self.pages.index(source_editor)
        except ValueError:
            return
        lines = source_editor._split_lines(source_editor.toPlainText())
        if len(lines) >= source_editor.max_lines:
            return
        needed = source_editor.max_lines - len(lines)
        next_index = start_index + 1
        while needed > 0 and next_index < self.TOTAL_PAGES:
            editor = self.pages[next_index]
            next_text = editor.toPlainText()
            if not next_text:
                next_index += 1
                continue
            next_lines = editor._split_lines(next_text)
            take_lines = next_lines[:needed]
            remaining_lines = next_lines[needed:]
            lines.extend(take_lines)
            editor._internal_change = True
            editor.setPlainText('\n'.join(remaining_lines))
            editor._internal_change = False
            editor._check_overflow()
            needed = source_editor.max_lines - len(lines)
            next_index += 1
        source_editor._internal_change = True
        source_editor.setPlainText('\n'.join(lines))
        source_editor._internal_change = False
        source_editor._check_overflow()
        self.update_status_label()
        self.contentChanged.emit()