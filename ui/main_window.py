# ui/main_window.py
import sys, os, fitz, re
from docx import Document
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QLabel, QPushButton, QFileDialog,
    QSplitter, QToolBar, QLineEdit, QTreeWidgetItem, QTreeWidget,
    QTabWidget, QMessageBox, QButtonGroup, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage, QAction, QColor, QTextCursor, QTextCharFormat, QDesktopServices, QFont, QActionGroup
from PyQt6.QtCore import Qt, QTimer, QUrl, QRect

# モジュール化したファイルをインポート
from ui.widgets import PDFDisplayLabel, MemoWindow, AnswerSheet
from utils.constants import LAW_DATA
from utils.law_fetcher import LawFetcherThread
from utils.xml_parser import parse_law_xml_to_html, kanji_to_number_string

class MainWindow(QMainWindow):
    # (MainWindowクラスのコードをここに移動し、インポート文を修正)
    INITIAL_TIME = 120 * 60
    def __init__(self):
        super().__init__()
        self.setWindowTitle("司法試験等CBTシステム (シミュレーター版)")
        self.setGeometry(50, 50, 1600, 1000)
        self.current_answer_path = None
        self.memo_window = None
        self.layout_state = 0
        
        self.current_tool = "select"
        self.pen_color = QColor("black")
        self.pen_width = 2
        self.marker_color = QColor("yellow")
        self.marker_width = 10
        self.annotations = {}

        self.left_toolbar = self.create_left_toolbar()
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.left_toolbar)
        
        self.problem_widget = self.create_problem_area()
        self.law_widget = self.create_law_area()
        self.answer_widget = self.create_answer_area()
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.setup_toolbar_and_menu()
        self.reassemble_layout()
        self.connect_signals()
        
        self.remaining_time = self.INITIAL_TIME
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer_display)
        self.update_timer_display(is_initial=True)
        self.timer.start()
        
        self.law_fetcher_thread = None
        
    def reassemble_layout(self):
        # (このメソッドは変更なし)
        widgets = [self.problem_widget, self.law_widget, self.answer_widget]
        left_widget = widgets[self.layout_state % 3]; top_right_widget = widgets[(self.layout_state + 1) % 3]; bottom_right_widget = widgets[(self.layout_state + 2) % 3]
        left_widget.setParent(None); top_right_widget.setParent(None); bottom_right_widget.setParent(None)
        while self.right_splitter.count() > 0:
            self.right_splitter.widget(0).setParent(None)
        self.right_splitter.addWidget(top_right_widget)
        self.right_splitter.addWidget(bottom_right_widget)
        self.right_splitter.setSizes([400, 600])
        while self.main_splitter.count() > 0:
            self.main_splitter.widget(0).setParent(None)
        self.main_splitter.addWidget(left_widget)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([800, 800])
        self.setCentralWidget(self.main_splitter)
        
    def swap_layout(self):
        self.layout_state = (self.layout_state + 1) % 3
        self.reassemble_layout()

    def setup_toolbar_and_menu(self):
        # ▼▼▼【バグ修正】ツールバーのエリアを明示的に指定 ▼▼▼
        toolbar = QToolBar("メインツールバー")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        toolbar.setStyleSheet("""
            QToolBar { spacing: 4px; }
            QPushButton, QToolButton { 
                background-color: #f0f0f0; 
                border: 1px solid #c0c0c0; 
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:checked, QToolButton:checked { 
                background-color: #cde;
                border: 1px solid #9ac;
            }
            QPushButton#FinishButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
            }
        """)

        self.exam_type_label = QLabel("問題ファイルを開いてください...")
        toolbar.addWidget(self.exam_type_label)
        toolbar.addSeparator()

        self.memo_button = QPushButton("メモ")
        toolbar.addWidget(self.memo_button)

        self.problem_button = QPushButton("問題")
        self.law_button = QPushButton("法文")
        self.answer_button = QPushButton("答案")
        self.problem_button.setCheckable(True); self.problem_button.setChecked(True)
        self.law_button.setCheckable(True); self.law_button.setChecked(True)
        self.answer_button.setCheckable(True); self.answer_button.setChecked(True)
        
        self.display_group = QButtonGroup(self)
        self.display_group.setExclusive(False)
        self.display_group.addButton(self.problem_button)
        self.display_group.addButton(self.law_button)
        self.display_group.addButton(self.answer_button)
        
        toolbar.addWidget(self.problem_button)
        toolbar.addWidget(self.law_button)
        toolbar.addWidget(self.answer_button)

        self.swap_button = QPushButton("入替え")
        toolbar.addWidget(self.swap_button)
        toolbar.addSeparator()

        self.copy_button = QPushButton("コピー")
        self.cut_button = QPushButton("切取り")
        self.paste_button = QPushButton("貼付け")
        toolbar.addWidget(self.copy_button); toolbar.addWidget(self.cut_button); toolbar.addWidget(self.paste_button)
        toolbar.addSeparator()

        self.input_mode_roma_button = QPushButton("ローマ字入力")
        self.input_mode_kana_button = QPushButton("かな入力")
        self.input_mode_roma_button.setCheckable(True); self.input_mode_kana_button.setCheckable(True)
        self.input_mode_roma_button.setChecked(True)
        self.input_mode_group = QButtonGroup(self)
        self.input_mode_group.addButton(self.input_mode_roma_button); self.input_mode_group.addButton(self.input_mode_kana_button)
        toolbar.addWidget(self.input_mode_roma_button); toolbar.addWidget(self.input_mode_kana_button)
        toolbar.addSeparator()

        self.zoom_in_button = QPushButton("拡大 (+)")
        self.zoom_out_button = QPushButton("縮小 (-)")
        self.filter_button = QPushButton("フィルタ")
        self.theme_button = QPushButton("配色")
        self.manual_button = QPushButton("使い方")
        toolbar.addWidget(self.zoom_in_button); toolbar.addWidget(self.zoom_out_button)
        toolbar.addWidget(self.filter_button); toolbar.addWidget(self.theme_button)
        toolbar.addWidget(self.manual_button)
        
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("font-size: 16pt; color: red; font-weight: bold;")
        toolbar.addWidget(QLabel("残り時間："))
        toolbar.addWidget(self.timer_label)

        self.finish_button = QPushButton("終了")
        self.finish_button.setObjectName("FinishButton")
        toolbar.addWidget(self.finish_button)

    def create_left_toolbar(self):
        # (このメソッドは変更なし)
        left_toolbar = QToolBar("PDFツール")
        left_toolbar.setOrientation(Qt.Orientation.Vertical)
        left_toolbar.setMovable(False)
        left_toolbar.setStyleSheet("QToolButton { padding: 8px 4px; font-size: 10pt; } QToolBar { spacing: 2px; }")
        left_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        self.select_action = QAction("選択", self); self.select_action.setCheckable(True)
        self.hand_action = QAction("ハンド", self); self.hand_action.setCheckable(True)
        self.marker_action = QAction("マーカー", self); self.marker_action.setCheckable(True)
        self.pen_action = QAction("ペン", self); self.pen_action.setCheckable(True)
        
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_group.addAction(self.select_action)
        self.tool_group.addAction(self.hand_action)
        self.tool_group.addAction(self.marker_action)
        self.tool_group.addAction(self.pen_action)
        self.select_action.setChecked(True)

        left_toolbar.addAction(self.select_action)
        left_toolbar.addAction(self.hand_action)
        left_toolbar.addAction(self.marker_action)
        left_toolbar.addAction(self.pen_action)
        
        left_toolbar.addAction(QAction("テキスト", self))
        left_toolbar.addAction(QAction("図形(〇)", self))
        left_toolbar.addAction(QAction("図形(△)", self))
        left_toolbar.addAction(QAction("図形(✕)", self))
        left_toolbar.addSeparator()
        left_toolbar.addAction(QAction("目次", self))
        left_toolbar.addSeparator()
        left_toolbar.addAction(QAction("拡大", self))
        left_toolbar.addAction(QAction("縮小", self))
        left_toolbar.addSeparator()
        left_toolbar.addAction(QAction("縦幅合わせ", self))
        left_toolbar.addAction(QAction("横幅合わせ", self))
        
        page_widget = QWidget()
        page_layout = QVBoxLayout(page_widget)
        page_layout.setContentsMargins(0,0,0,0); page_layout.setSpacing(0)
        self.page_num_input = QLineEdit(); self.page_num_input.setFixedWidth(50)
        self.page_num_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label = QLabel("/ -"); self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(self.page_num_input)
        page_layout.addWidget(self.page_label)

        left_toolbar.addSeparator()
        left_toolbar.addWidget(page_widget)
        
        self.goto_first_action = QAction("|<", self)
        self.prev_page_action = QAction("<", self)
        self.next_page_action = QAction(">", self)
        self.goto_last_action = QAction(">|", self)
        left_toolbar.addAction(self.goto_first_action)
        left_toolbar.addAction(self.prev_page_action)
        left_toolbar.addAction(self.next_page_action)
        left_toolbar.addAction(self.goto_last_action)
        left_toolbar.addSeparator()
        
        left_toolbar.addAction(QAction("スクロール", self))
        left_toolbar.addAction(QAction("見開き", self))
        left_toolbar.addSeparator()
        left_toolbar.addAction(QAction("元に戻す", self))
        left_toolbar.addAction(QAction("やり直し", self))

        return left_toolbar

    def create_problem_area(self):
        # (このメソッドは変更なし)
        pdf_area = QWidget()
        pdf_layout = QVBoxLayout(pdf_area)
        
        controls = QHBoxLayout()
        self.open_pdf_button = QPushButton("問題PDFを開く")
        self.save_pdf_button = QPushButton("書き込みを保存")
        
        controls.addWidget(self.open_pdf_button)
        controls.addWidget(self.save_pdf_button)
        controls.addStretch()

        self.pdf_display_label = PDFDisplayLabel(self)
        self.pdf_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_display_label.setText("「問題PDFを開く」")
        
        pdf_layout.addLayout(controls); pdf_layout.addWidget(self.pdf_display_label, 1)
        
        self.pdf_document = None; self.current_page = 0; self.total_pages = 0
        return pdf_area

    def create_law_area(self):
        # (このメソッドは変更なし)
        area = QWidget(); layout = QVBoxLayout(area)
        top_bar_layout = QHBoxLayout()
        self.toc_search_input = QLineEdit(); self.toc_search_input.setPlaceholderText("Q 目次検索...")
        self.toggle_toc_view_button = QPushButton("<"); self.toggle_toc_view_button.setCheckable(True); self.toggle_toc_view_button.setChecked(True); self.toggle_toc_view_button.setFixedWidth(30)
        self.toc_button = QPushButton("目次"); self.toc_button.setCheckable(True); self.toc_button.setChecked(True)
        jump_layout = QHBoxLayout(); jump_layout.addWidget(QLabel("第"))
        self.article_jump_input = QLineEdit(); self.article_jump_input.setFixedWidth(40)
        jump_layout.addWidget(self.article_jump_input); jump_layout.addWidget(QLabel("条"))
        self.paragraph_jump_input = QLineEdit(); self.paragraph_jump_input.setFixedWidth(30)
        jump_layout.addWidget(self.paragraph_jump_input); jump_layout.addWidget(QLabel("項"))
        self.item_jump_input = QLineEdit(); self.item_jump_input.setFixedWidth(30)
        jump_layout.addWidget(self.item_jump_input); jump_layout.addWidget(QLabel("号"))
        self.jump_button = QPushButton("移動")
        jump_layout.addWidget(self.jump_button)
        
        self.bookmark_button = QPushButton("付箋")
        self.law_search_toggle_button = QPushButton("検索"); self.law_search_toggle_button.setCheckable(True)
        top_bar_layout.addWidget(self.toc_search_input); top_bar_layout.addWidget(self.toggle_toc_view_button); top_bar_layout.addWidget(self.toc_button)
        top_bar_layout.addStretch(); top_bar_layout.addLayout(jump_layout); top_bar_layout.addWidget(self.bookmark_button); top_bar_layout.addWidget(self.law_search_toggle_button)
        
        self.law_search_bar = QWidget(); law_search_layout = QHBoxLayout(self.law_search_bar)
        self.law_search_input = QLineEdit(); self.law_search_input.setPlaceholderText("法文内を検索...")
        law_search_layout.addWidget(self.law_search_input)
        self.law_search_bar.setVisible(False)
        law_splitter = QSplitter(Qt.Orientation.Horizontal); self.law_toc_tree = QTreeWidget(); self.law_toc_tree.setHeaderHidden(True); self.populate_law_tree()
        self.law_main_area = QTextBrowser(); self.law_main_area.setOpenExternalLinks(True)
        law_splitter.addWidget(self.law_toc_tree); law_splitter.addWidget(self.law_main_area); law_splitter.setSizes([300, 700])
        layout.addLayout(top_bar_layout); layout.addWidget(self.law_search_bar); layout.addWidget(law_splitter)
        return area

    def populate_law_tree(self):
        # (このメソッドは変更なし)
        self.law_toc_tree.clear()
        for subject, laws in LAW_DATA.items():
            subject_item = QTreeWidgetItem(self.law_toc_tree); subject_item.setText(0, subject)
            for law_name, law_id in laws.items():
                law_item = QTreeWidgetItem(subject_item); law_item.setText(0, law_name); law_item.setData(0, Qt.ItemDataRole.UserRole, law_id)
        self.law_toc_tree.expandAll()

    def create_answer_area(self):
        # (このメソッドは変更なし)
        self.answer_tab_widget = QTabWidget(); sheet1 = AnswerSheet(); sheet2 = AnswerSheet()
        self.answer_tab_widget.addTab(sheet1, "第1問"); self.answer_tab_widget.addTab(sheet2, "第2問")
        return self.answer_tab_widget

    def connect_signals(self):
        # (このメソッドは変更なし)
        self.memo_button.clicked.connect(self.toggle_memo_window)
        self.problem_button.toggled.connect(self.problem_widget.setVisible)
        self.law_button.toggled.connect(self.law_widget.setVisible)
        self.answer_button.toggled.connect(self.answer_widget.setVisible)
        self.swap_button.clicked.connect(self.swap_layout)
        self.copy_button.clicked.connect(self.handle_copy)
        self.cut_button.clicked.connect(self.handle_cut)
        self.paste_button.clicked.connect(self.handle_paste)
        self.manual_button.clicked.connect(self.open_manual)
        self.finish_button.clicked.connect(self.close)

        self.tool_group.triggered.connect(self.on_tool_selected)

        self.open_pdf_button.clicked.connect(self.open_pdf_file)
        self.save_pdf_button.clicked.connect(self.save_annotations_to_pdf)
        
        self.prev_page_action.triggered.connect(self.show_prev_page)
        self.next_page_action.triggered.connect(self.show_next_page)
        self.goto_first_action.triggered.connect(lambda: self.show_page(0))
        self.goto_last_action.triggered.connect(lambda: self.show_page(self.total_pages - 1))
        self.page_num_input.returnPressed.connect(self.goto_page_from_input)

        self.law_toc_tree.currentItemChanged.connect(self.on_law_tree_selection_changed)
        self.toc_search_input.textChanged.connect(self.filter_law_tree)
        self.toc_button.toggled.connect(self.toggle_law_toc_visibility); self.toggle_toc_view_button.toggled.connect(self.toggle_law_toc_visibility)
        self.jump_button.clicked.connect(self.jump_to_article); self.article_jump_input.returnPressed.connect(self.jump_to_article)
        self.law_search_toggle_button.toggled.connect(self.law_search_bar.setVisible)
        self.law_search_input.textChanged.connect(self.search_in_law_text)
        for i in range(self.answer_tab_widget.count()):
            sheet = self.answer_tab_widget.widget(i)
            sheet.answer_text_edit.textChanged.connect(self.update_char_count)
            sheet.answer_undo_button.clicked.connect(sheet.answer_text_edit.undo)
            sheet.answer_redo_button.clicked.connect(sheet.answer_text_edit.redo)
            sheet.toggle_search_button.toggled.connect(sheet.search_replace_bar.setVisible)
            sheet.answer_search_input.textChanged.connect(lambda text, s=sheet: self.highlight_all_in_answer(s))
            sheet.answer_replace_button.clicked.connect(lambda _, s=sheet: self.replace_in_answer(s))
            sheet.answer_replace_all_button.clicked.connect(lambda _, s=sheet: self.replace_all_in_answer(s))

    def on_tool_selected(self, action):
        if action == self.pen_action:
            self.current_tool = "pen"
        elif action == self.marker_action:
            self.current_tool = "marker"
        else:
            self.current_tool = "select"
    
    def set_tool_color(self, color):
        if self.current_tool == "pen":
            self.pen_color = color
        elif self.current_tool == "marker":
            self.marker_color = color

    def set_tool_width(self, size_str):
        pen_sizes = {"small": 1, "medium": 2, "large": 4}
        marker_sizes = {"small": 8, "medium": 12, "large": 16}
        if self.current_tool == "pen":
            self.pen_width = pen_sizes.get(size_str, 2)
        elif self.current_tool == "marker":
            self.marker_width = marker_sizes.get(size_str, 12)

    def save_annotations_to_pdf(self):
        if not self.pdf_document:
            QMessageBox.warning(self, "保存エラー", "PDFファイルが開かれていません。")
            return
        QMessageBox.information(self, "情報", "書き込み保存機能は現在開発中です。")

    def goto_page_from_input(self):
        try:
            page_num = int(self.page_num_input.text()) - 1
            if 0 <= page_num < self.total_pages:
                self.show_page(page_num)
        except ValueError:
            pass 

    def search_in_law_text(self, text):
        self.law_main_area.find(text)

    def handle_copy(self):
        widget = self.focusWidget()
        if hasattr(widget, 'copy'):
            widget.copy()

    def handle_cut(self):
        widget = self.focusWidget()
        if hasattr(widget, 'cut'):
            widget.cut()

    def handle_paste(self):
        widget = self.focusWidget()
        if hasattr(widget, 'paste'):
            widget.paste()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '確認', '試験を終了しますか？',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def on_law_tree_selection_changed(self, current, previous):
        if current is None: return
        law_id = current.data(0, Qt.ItemDataRole.UserRole)
        if law_id: self.fetch_law_data(current.text(0), law_id)

    def filter_law_tree(self, text):
        for i in range(self.law_toc_tree.topLevelItemCount()):
            subject_item = self.law_toc_tree.topLevelItem(i); has_visible_child = False
            for j in range(subject_item.childCount()):
                law_item = subject_item.child(j); is_match = text.lower() in law_item.text(0).lower(); law_item.setHidden(not is_match)
                if is_match: has_visible_child = True
            subject_item.setHidden(not has_visible_child)
            if has_visible_child: subject_item.setExpanded(True)

    def on_law_data_ready(self, result_tuple):
        xml_string = result_tuple[0]
        _, main_html = parse_law_xml_to_html(xml_string)
        self.law_main_area.setHtml(main_html)

    def on_law_data_error(self, error_message): self.law_main_area.setText(error_message)

    def toggle_law_toc_visibility(self, checked):
        self.law_toc_tree.setVisible(checked); self.toc_search_input.setVisible(checked); self.toc_button.setChecked(checked); self.toggle_toc_view_button.setChecked(checked)
        self.toggle_toc_view_button.setText("<" if checked else ">")

    def jump_to_article(self):
        article_num = self.article_jump_input.text().strip()
        paragraph_num = self.paragraph_jump_input.text().strip()
        item_num = self.item_jump_input.text().strip()
        if not article_num: return
        
        anchor_name = f"article-{article_num}"
        if paragraph_num:
            anchor_name += f"-{paragraph_num}"
            if item_num:
                anchor_name += f"-{item_num}"
        self.law_main_area.scrollToAnchor(anchor_name)
    
    def fetch_law_data(self, law_name, law_id):
        if not law_id: self.law_main_area.setText("法令を選択してください。"); return
        self.law_main_area.setText(f"{law_name}のデータを取得中...");
        if self.law_fetcher_thread and self.law_fetcher_thread.isRunning(): self.law_fetcher_thread.terminate(); self.law_fetcher_thread.wait()
        self.law_fetcher_thread = LawFetcherThread(law_id, self)
        self.law_fetcher_thread.result_ready.connect(self.on_law_data_ready); self.law_fetcher_thread.error_occurred.connect(self.on_law_data_error); self.law_fetcher_thread.start()

    def save_as_answer(self):
        current_sheet = self.answer_tab_widget.currentWidget()
        if not current_sheet: return
        file_path, _ = QFileDialog.getSaveFileName(self, "保存", "", "Word Documents (*.docx);;Text Files (*.txt)")
        if not file_path: return
        if not file_path.endswith(('.docx', '.txt')): file_path += '.docx' if 'docx' in _ else '.txt'
        self.current_answer_path = file_path
        try:
            if self.current_answer_path.endswith('.docx'):
                doc = Document(); doc.add_paragraph(current_sheet.answer_text_edit.toPlainText()); doc.save(self.current_answer_path)
            else:
                with open(self.current_answer_path, 'w', encoding='utf-8') as f: f.write(current_sheet.answer_text_edit.toPlainText())
        except Exception as e:
            print(f"保存エラー: {e}")
        
    def update_timer_display(self, is_initial=False):
        if not is_initial: self.remaining_time -= 1
        if self.remaining_time < 0:
            self.remaining_time = 0
            self.timer.stop()
            QMessageBox.information(self, "試験終了", "試験時間が終了しました。")
        hours, rem = divmod(self.remaining_time, 3600); mins, secs = divmod(rem, 60)
        self.timer_label.setText(f"{hours:02}:{mins:02}:{secs:02}")
        
    def toggle_memo_window(self):
        if not self.memo_window: self.memo_window = MemoWindow()
        self.memo_window.setVisible(not self.memo_window.isVisible())
        if self.memo_window.isVisible(): self.memo_window.activateWindow()

    def clear_highlight(self, text_edit):
        cursor = text_edit.textCursor(); cursor.select(QTextCursor.SelectionType.Document)
        default_format = QTextCharFormat(); cursor.setCharFormat(default_format)
        cursor.clearSelection(); text_edit.setTextCursor(cursor)
        
    def highlight_all_in_answer(self, sheet):
        self.clear_highlight(sheet.answer_text_edit); keyword = sheet.answer_search_input.text()
        if not keyword: return
        highlight_format = QTextCharFormat(); highlight_format.setBackground(QColor("yellow"))
        doc = sheet.answer_text_edit.document(); search_cursor = QTextCursor(doc)
        while not (search_cursor := doc.find(keyword, search_cursor)).isNull(): search_cursor.mergeCharFormat(highlight_format)
        
    def replace_in_answer(self, sheet):
        cursor = sheet.answer_text_edit.textCursor(); keyword = sheet.answer_search_input.text(); replace_text = sheet.answer_replace_input.text()
        if keyword and cursor.hasSelection() and cursor.selectedText() == keyword: cursor.insertText(replace_text)
        sheet.answer_text_edit.find(keyword)
        
    def replace_all_in_answer(self, sheet):
        keyword = sheet.answer_search_input.text(); replace_text = sheet.answer_replace_input.text()
        if keyword:
            self.clear_highlight(sheet.answer_text_edit)
            text = sheet.answer_text_edit.toPlainText()
            new_text = text.replace(keyword, replace_text)
            sheet.answer_text_edit.setPlainText(new_text)
    
    def update_char_count(self):
        current_sheet = self.answer_tab_widget.currentWidget()
        if not current_sheet: return
        char_count = len(current_sheet.answer_text_edit.toPlainText())
        line_count = current_sheet.answer_text_edit.document().blockCount()
        current_sheet.char_count_label.setText(f"{line_count}/184行 {char_count}/5,520文字 (空白含む)")
        
    def open_manual(self): QDesktopServices.openUrl(QUrl.fromLocalFile("manual.pdf"))
    
    def open_pdf_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "PDF", "", "*.pdf")
        if file_path:
            file_name = os.path.basename(file_path)
            self.exam_type_label.setText(file_name)
            
            self.pdf_document = fitz.open(file_path); self.total_pages = len(self.pdf_document); self.current_page = 0; self.show_page(self.current_page)
        
    def show_page(self, page_number):
        if not self.pdf_document or not (0 <= page_number < self.total_pages): return
        self.current_page = page_number
        page = self.pdf_document.load_page(page_number)
        dpr = self.window().devicePixelRatio() or 2.0; zoom = dpr * 1.5
        mat = fitz.Matrix(zoom, zoom); pix = page.get_pixmap(matrix=mat, annots=True)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        
        self.pdf_display_label.setPixmap(pixmap)
        self.page_label.setText(f"/ {self.total_pages}")
        self.page_num_input.setText(str(self.current_page + 1))
        
    def show_prev_page(self): self.show_page(self.current_page - 1)
    
    def show_next_page(self): self.show_page(self.current_page + 1)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'pdf_document') and self.pdf_document: self.show_page(self.current_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())