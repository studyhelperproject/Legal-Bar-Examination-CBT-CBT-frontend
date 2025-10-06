import sys, os
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QLabel, QPushButton,
    QSplitter, QToolBar, QLineEdit, QTreeWidgetItem, QTreeWidget,
    QTabWidget, QMessageBox, QButtonGroup, QSizePolicy, QComboBox,
    QScrollArea, QDialog
)
from PyQt6.QtGui import (
    QAction, QFont, QActionGroup, QIcon, QKeySequence, QShortcut
)
from PyQt6.QtCore import Qt, QTimer, QUrl

from ui.components import KanaInputFilter, ClickableLabel
from ui.dialogs import TimerSettingsDialog
from ui.widgets import PDFDisplayLabel, MemoWindow, AnswerSheet
from utils.constants import LAW_DATA

# Import handlers
from ui.handlers.pdf_handler import PDFHandler
from ui.handlers.annotation_handler import AnnotationHandler
from ui.handlers.export_handler import ExportHandler
from ui.handlers.history_handler import HistoryHandler
from ui.handlers.law_handler import LawHandler
from ui.handlers.clipboard_handler import ClipboardHandler

class MainWindow(QMainWindow):
    INITIAL_TIME = 120 * 60

    def __init__(self):
        super().__init__()
        self.setWindowTitle("司法試験等CBTシステム (シミュレーター版)")
        self.setGeometry(50, 50, 1600, 1000)

        # Initialize handlers
        self.pdf_handler = PDFHandler(self)
        self.annotation_handler = AnnotationHandler(self)
        self.export_handler = ExportHandler(self)
        self.history_handler = HistoryHandler(self)
        self.law_handler = LawHandler(self)
        self.clipboard_handler = ClipboardHandler(self)

        # Properties
        self.memo_window = None
        self.layout_state = 0
        self._closing_confirmed = False

        # UI Setup
        self.left_toolbar = self.create_left_toolbar()
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.left_toolbar)
        
        self.problem_widget = self.create_problem_area()
        self.law_widget = self.create_law_area()
        self.answer_widget = self.create_answer_area()

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self._configure_splitter(self.main_splitter)
        self._configure_splitter(self.right_splitter)
        
        self.setup_toolbar_and_menu()
        self.reassemble_layout()
        self.connect_signals()
        self.setup_shortcuts()

        # Input Mode
        self.input_mode = 'roma'
        self.input_mode_filter = KanaInputFilter(self)
        QApplication.instance().installEventFilter(self.input_mode_filter)
        self.set_input_mode('roma')

        # Font Scaling
        self.MIN_UI_FONT_SCALE, self.MAX_UI_FONT_SCALE = 0.5, 1.5
        self.ui_font_scale = 1.0
        self._base_ui_font = QFont(QApplication.instance().font())
        self._base_timer_font = None
        self._base_law_font = None

        # Timer
        self.remaining_time = self.INITIAL_TIME
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer_display)
        self.timer_paused = False
        self.update_timer_display(is_initial=True)
        self.timer.start()

    def createPopupMenu(self):
        return None

    def reassemble_layout(self):
        widgets = [self.problem_widget, self.law_widget, self.answer_widget]
        left_widget = widgets[self.layout_state % 3]
        top_right_widget = widgets[(self.layout_state + 1) % 3]
        bottom_right_widget = widgets[(self.layout_state + 2) % 3]

        left_widget.setParent(None); top_right_widget.setParent(None); bottom_right_widget.setParent(None)

        self.right_splitter.addWidget(top_right_widget)
        self.right_splitter.addWidget(bottom_right_widget)
        if not self.right_splitter.sizes() or self.right_splitter.sizes()[0] == 0: self.right_splitter.setSizes([400, 600])

        self.main_splitter.addWidget(left_widget)
        self.main_splitter.addWidget(self.right_splitter)
        if not self.main_splitter.sizes() or self.main_splitter.sizes()[0] == 0: self.main_splitter.setSizes([800, 800])

        self.setCentralWidget(self.main_splitter)
        self.pdf_handler.handle_resize_event()

    def swap_layout(self):
        self.layout_state = (self.layout_state + 1) % 3
        self.reassemble_layout()

    def setup_toolbar_and_menu(self):
        toolbar = QToolBar("メインツールバー")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self.exam_type_label = QLabel("問題ファイルを開いてください...")
        toolbar.addWidget(self.exam_type_label)
        toolbar.addSeparator()

        self.memo_button = QPushButton("メモ")
        toolbar.addWidget(self.memo_button)

        self.problem_button = QPushButton("問題"); self.problem_button.setCheckable(True); self.problem_button.setChecked(True)
        self.law_button = QPushButton("法文"); self.law_button.setCheckable(True); self.law_button.setChecked(True)
        self.answer_button = QPushButton("答案"); self.answer_button.setCheckable(True); self.answer_button.setChecked(True)
        self.display_group = QButtonGroup(self); self.display_group.setExclusive(False)
        self.display_group.addButton(self.problem_button); self.display_group.addButton(self.law_button); self.display_group.addButton(self.answer_button)
        toolbar.addWidget(self.problem_button); toolbar.addWidget(self.law_button); toolbar.addWidget(self.answer_button)

        self.swap_button = QPushButton("入替え")
        toolbar.addWidget(self.swap_button)
        toolbar.addSeparator()

        self.copy_button = QPushButton("コピー"); self.cut_button = QPushButton("切取り"); self.paste_button = QPushButton("貼付け")
        toolbar.addWidget(self.copy_button); toolbar.addWidget(self.cut_button); toolbar.addWidget(self.paste_button)
        toolbar.addSeparator()

        self.input_mode_roma_button = QPushButton("ローマ字入力"); self.input_mode_kana_button = QPushButton("かな入力")
        self.input_mode_roma_button.setCheckable(True); self.input_mode_kana_button.setCheckable(True)
        self.input_mode_group = QButtonGroup(self); self.input_mode_group.setExclusive(True)
        self.input_mode_group.addButton(self.input_mode_roma_button); self.input_mode_group.addButton(self.input_mode_kana_button)
        toolbar.addWidget(self.input_mode_roma_button); toolbar.addWidget(self.input_mode_kana_button)
        toolbar.addSeparator()

        self.zoom_in_button = QPushButton("拡大 (+)"); self.zoom_out_button = QPushButton("縮小 (-)")
        self.word_save_button = QPushButton("Word保存")
        toolbar.addWidget(self.zoom_in_button); toolbar.addWidget(self.zoom_out_button); toolbar.addWidget(self.word_save_button)
        
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        self.timer_label = ClickableLabel("00:00:00")
        self.timer_label.setStyleSheet("font-size: 16pt; color: red; font-weight: bold;")
        toolbar.addWidget(QLabel("残り時間：")); toolbar.addWidget(self.timer_label)
        self._base_timer_font = QFont(self.timer_label.font())

        self.finish_button = QPushButton("終了")
        toolbar.addWidget(self.finish_button)

    def create_left_toolbar(self):
        left_toolbar = QToolBar("PDFツール")
        left_toolbar.setOrientation(Qt.Orientation.Vertical); left_toolbar.setMovable(False)
        left_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        self.select_action = QAction("選択", self); self.hand_action = QAction("ハンド", self)
        self.marker_action = QAction("マーカー", self); self.pen_action = QAction("ペン", self)
        self.text_action = QAction("テキスト", self)
        self.tool_group = QActionGroup(self); self.tool_group.setExclusive(True)
        for act in [self.select_action, self.hand_action, self.marker_action, self.pen_action, self.text_action]:
            act.setCheckable(True); self.tool_group.addAction(act)
        self.select_action.setChecked(True)
        left_toolbar.addActions(self.tool_group.actions())

        self.circle_action = QAction("図形(〇)", self); self.triangle_action = QAction("図形(△)", self); self.cross_action = QAction("図形(✕)", self)
        self.toc_toolbar_action = QAction("目次", self)
        left_toolbar.addActions([self.circle_action, self.triangle_action, self.cross_action])
        left_toolbar.addSeparator(); left_toolbar.addAction(self.toc_toolbar_action); left_toolbar.addSeparator()

        self.zoom_in_action = QAction("拡大", self); self.zoom_out_action = QAction("縮小", self)
        self.fit_height_action = QAction("縦幅合わせ", self); self.fit_width_action = QAction("横幅合わせ", self)
        left_toolbar.addActions([self.zoom_in_action, self.zoom_out_action, self.fit_height_action, self.fit_width_action])
        
        page_widget = QWidget(); page_layout = QVBoxLayout(page_widget); page_layout.setContentsMargins(0,0,0,0)
        self.page_num_input = QLineEdit(); self.page_num_input.setFixedWidth(50); self.page_num_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label = QLabel("/ -"); self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(self.page_num_input); page_layout.addWidget(self.page_label)
        left_toolbar.addSeparator(); left_toolbar.addWidget(page_widget)
        
        self.goto_first_action = QAction("|<", self); self.prev_page_action = QAction("<", self)
        self.next_page_action = QAction(">", self); self.goto_last_action = QAction(">|", self)
        left_toolbar.addActions([self.goto_first_action, self.prev_page_action, self.next_page_action, self.goto_last_action])
        left_toolbar.addSeparator()
        
        self.scroll_toggle_action = QAction("スクロール", self); self.scroll_toggle_action.setCheckable(True)
        self.spread_toggle_action = QAction("見開き", self); self.spread_toggle_action.setCheckable(True)
        left_toolbar.addActions([self.scroll_toggle_action, self.spread_toggle_action]); left_toolbar.addSeparator()

        self.undo_toolbar_action = QAction("元に戻す", self); self.redo_toolbar_action = QAction("やり直し", self)
        self.undo_toolbar_action.setEnabled(False); self.redo_toolbar_action.setEnabled(False)
        left_toolbar.addActions([self.undo_toolbar_action, self.redo_toolbar_action])
        return left_toolbar

    def setup_shortcuts(self):
        QShortcut(QKeySequence.StandardKey.Undo, self).activated.connect(self.history_handler.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self).activated.connect(self.history_handler.redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(self.history_handler.redo)

    def create_problem_area(self):
        area = QWidget(); layout = QVBoxLayout(area)
        controls = QHBoxLayout()
        self.open_pdf_button = QPushButton("問題PDFを開く")
        self.save_annotations_button = QPushButton("セッション保存")
        controls.addWidget(self.open_pdf_button); controls.addWidget(self.save_annotations_button); controls.addStretch()

        self.pdf_display_label = PDFDisplayLabel(self)
        self.pdf_display_label.setText("「問題PDFを開く」")

        self.text_tool_panel = QWidget(); text_panel_layout = QHBoxLayout(self.text_tool_panel)
        text_panel_layout.addWidget(QLabel("テキストサイズ:")); self.text_size_combo = QComboBox()
        self.text_size_combo.addItems(["小", "中", "大"]); self.text_size_combo.setCurrentIndex(1)
        text_panel_layout.addWidget(self.text_size_combo)
        text_panel_layout.addWidget(QLabel("色:")); self.text_color_combo = QComboBox()
        for label, color in self.annotation_handler.text_palette: self.text_color_combo.addItem(label, color)
        text_panel_layout.addWidget(self.text_color_combo); text_panel_layout.addStretch()
        self.text_tool_panel.setVisible(False)

        self.pdf_scroll_area = QScrollArea(); self.pdf_scroll_area.setWidgetResizable(False)
        self.pdf_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_scroll_area.setWidget(self.pdf_display_label)

        layout.addLayout(controls); layout.addWidget(self.text_tool_panel); layout.addWidget(self.pdf_scroll_area, 1)
        return area

    def create_law_area(self):
        area = QWidget(); layout = QVBoxLayout(area); top_bar = QHBoxLayout()
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
        self.jump_button = QPushButton("移動"); jump_layout.addWidget(self.jump_button)
        self.bookmark_button = QPushButton("付箋"); self.law_search_toggle_button = QPushButton("検索"); self.law_search_toggle_button.setCheckable(True)
        top_bar.addWidget(self.toc_search_input); top_bar.addWidget(self.toggle_toc_view_button); top_bar.addWidget(self.toc_button)
        top_bar.addStretch(); top_bar.addLayout(jump_layout); top_bar.addWidget(self.bookmark_button); top_bar.addWidget(self.law_search_toggle_button)
        
        self.law_search_bar = QWidget(); law_search_layout = QHBoxLayout(self.law_search_bar)
        self.law_search_input = QLineEdit(); self.law_search_input.setPlaceholderText("法文内を検索...")
        law_search_layout.addWidget(self.law_search_input); self.law_search_bar.setVisible(False)

        splitter = QSplitter(Qt.Orientation.Horizontal); self._configure_splitter(splitter)
        self.law_toc_tree = QTreeWidget(); self.law_toc_tree.setHeaderHidden(True); self.law_handler.populate_law_tree()
        self.law_main_area = QTextBrowser(); self.law_main_area.setOpenExternalLinks(True)
        splitter.addWidget(self.law_toc_tree); splitter.addWidget(self.law_main_area); splitter.setSizes([300, 700])

        layout.addLayout(top_bar); layout.addWidget(self.law_search_bar); layout.addWidget(splitter)
        return area

    def create_answer_area(self):
        self.answer_tab_widget = QTabWidget()
        self.answer_sheets = [AnswerSheet(self), AnswerSheet(self)]
        self.answer_tab_widget.addTab(self.answer_sheets[0], "第1問")
        self.answer_tab_widget.addTab(self.answer_sheets[1], "第2問")
        return self.answer_tab_widget

    def connect_signals(self):
        # Top Toolbar
        self.memo_button.clicked.connect(self.toggle_memo_window)
        self.zoom_in_button.clicked.connect(lambda: self.adjust_ui_font_scale(1.1))
        self.zoom_out_button.clicked.connect(lambda: self.adjust_ui_font_scale(1/1.1))
        self.word_save_button.clicked.connect(self.export_handler.save_as_word)
        self.input_mode_roma_button.clicked.connect(lambda: self.set_input_mode('roma'))
        self.input_mode_kana_button.clicked.connect(lambda: self.set_input_mode('kana'))
        self.problem_button.toggled.connect(self.problem_widget.setVisible)
        self.law_button.toggled.connect(self.law_widget.setVisible)
        self.answer_button.toggled.connect(self.answer_widget.setVisible)
        self.swap_button.clicked.connect(self.swap_layout)
        self.copy_button.clicked.connect(self.clipboard_handler.handle_copy)
        self.cut_button.clicked.connect(self.clipboard_handler.handle_cut)
        self.paste_button.clicked.connect(self.clipboard_handler.handle_paste)
        self.finish_button.clicked.connect(self.close)
        self.timer_label.clicked.connect(self.open_timer_settings)

        # Left Toolbar (PDF Tools)
        self.tool_group.triggered.connect(self.annotation_handler.on_tool_selected)
        self.open_pdf_button.clicked.connect(self.pdf_handler.open_pdf_file)
        self.save_annotations_button.clicked.connect(self.export_handler.save_session_via_dialog)
        self.circle_action.triggered.connect(lambda: self.annotation_handler.add_shape_annotation("circle"))
        self.triangle_action.triggered.connect(lambda: self.annotation_handler.add_shape_annotation("triangle"))
        self.cross_action.triggered.connect(lambda: self.annotation_handler.add_shape_annotation("cross"))
        self.toc_toolbar_action.triggered.connect(self.pdf_handler.show_page_overview)
        self.prev_page_action.triggered.connect(self.pdf_handler.show_prev_page)
        self.next_page_action.triggered.connect(self.pdf_handler.show_next_page)
        self.goto_first_action.triggered.connect(lambda: self.pdf_handler.show_page(0))
        self.goto_last_action.triggered.connect(lambda: self.pdf_handler.show_page(self.pdf_handler.total_pages - 1))
        self.page_num_input.returnPressed.connect(self.pdf_handler.goto_page_from_input)
        self.zoom_in_action.triggered.connect(lambda: self.pdf_handler.adjust_zoom(1.25))
        self.zoom_out_action.triggered.connect(lambda: self.pdf_handler.adjust_zoom(0.8))
        self.fit_height_action.triggered.connect(self.pdf_handler.fit_to_height)
        self.fit_width_action.triggered.connect(self.pdf_handler.fit_to_width)
        self.scroll_toggle_action.toggled.connect(self.pdf_handler.toggle_scroll_mode)
        self.spread_toggle_action.toggled.connect(self.pdf_handler.toggle_spread_mode)
        self.undo_toolbar_action.triggered.connect(self.history_handler.undo)
        self.redo_toolbar_action.triggered.connect(self.history_handler.redo)
        self.text_size_combo.currentIndexChanged.connect(self.annotation_handler.update_text_style_from_controls)
        self.text_color_combo.currentIndexChanged.connect(self.annotation_handler.update_text_style_from_controls)

        # Law Area
        self.law_toc_tree.currentItemChanged.connect(self.law_handler.on_law_tree_selection_changed)
        self.toc_search_input.textChanged.connect(self.law_handler.filter_law_tree)
        self.toc_button.toggled.connect(self.law_handler.toggle_law_toc_visibility)
        self.toggle_toc_view_button.toggled.connect(self.law_handler.toggle_law_toc_visibility)
        self.jump_button.clicked.connect(self.law_handler.jump_to_article)
        self.law_search_toggle_button.toggled.connect(self.law_search_bar.setVisible)
        self.law_search_input.textChanged.connect(self.law_handler.search_in_law_text)
        self.bookmark_button.clicked.connect(self.law_handler.handle_law_bookmark_action)

        # Answer Area
        self.answer_tab_widget.currentChanged.connect(self.update_char_count)
        for sheet in self.answer_sheets:
            sheet.contentChanged.connect(self.update_char_count)
            sheet.contentChanged.connect(self.history_handler.register_snapshot)

    def _configure_splitter(self, splitter):
        splitter.setHandleWidth(8); splitter.setStyleSheet("QSplitter::handle { background-color: #d0d8ec; }")

    def update_char_count(self):
        for sheet in self.answer_sheets: sheet.update_status_label()

    def set_input_mode(self, mode):
        self.input_mode = mode; is_roma = (mode == 'roma')
        self.input_mode_roma_button.setChecked(is_roma); self.input_mode_kana_button.setChecked(not is_roma)
        self.input_mode_filter.set_mode(mode)

    def adjust_ui_font_scale(self, multiplier):
        new_scale = self.ui_font_scale * multiplier
        self.ui_font_scale = max(self.MIN_UI_FONT_SCALE, min(self.MAX_UI_FONT_SCALE, new_scale))
        self.apply_font_scale(self.ui_font_scale)

    def apply_font_scale(self, scale):
        app_font = QFont(self._base_ui_font); base_size = self._base_ui_font.pointSizeF()
        if base_size > 0: app_font.setPointSizeF(base_size * scale)
        QApplication.instance().setFont(app_font)
        # Apply to other specific widgets if needed...

    def closeEvent(self, event):
        if self._closing_confirmed or self.prompt_exit(): event.accept()
        else: event.ignore()

    def prompt_exit(self):
        reply = QMessageBox.question(self, "終了確認", "試験を終了しますか？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Save,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Save:
            return self.export_handler.save_session_via_dialog()
        return reply == QMessageBox.StandardButton.Yes

    def update_timer_display(self, is_initial=False):
        if not is_initial: self.remaining_time -= 1
        if self.remaining_time <= 0:
            self.remaining_time = 0; self.timer.stop()
            QMessageBox.information(self, "試験終了", "試験時間が終了しました。")
        h, rem = divmod(self.remaining_time, 3600); m, s = divmod(rem, 60)
        self.timer_label.setText(f"{h:02}:{m:02}:{s:02}")
        
    def open_timer_settings(self):
        dialog = TimerSettingsDialog(self, self.remaining_time, self.timer.isActive())
        if dialog.exec():
            self.remaining_time = max(0, dialog.total_seconds())
            self.update_timer_display(is_initial=True)
            if self.remaining_time == 0: self.timer.stop()

    def toggle_memo_window(self):
        if not self.memo_window: self.memo_window = MemoWindow(self)
        self.memo_window.setVisible(not self.memo_window.isVisible())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.pdf_handler.handle_resize_event()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())