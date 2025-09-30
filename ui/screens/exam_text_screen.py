# ui/screens/exam_text_screen.py
import os
import fitz
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

class ExamTextScreen(QWidget):
    """
    司法試験問題画面
    - PDF問題文の表示
    - 注釈機能（ペン、マーカー、テキスト、図形）
    - ページナビゲーション
    - ズーム機能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定値（ハードコーディング - 変更しやすい）
        self.PDF_ZOOM_MIN = 0.3
        self.PDF_ZOOM_MAX = 4.0
        self.PDF_DEFAULT_ZOOM = 1.0
        self.PEN_DEFAULT_WIDTH = 2
        self.MARKER_DEFAULT_WIDTH = 10
        self.TEXT_DEFAULT_SIZE = 16
        
        # PDF関連の状態
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = self.PDF_DEFAULT_ZOOM
        self.current_tool = "select"
        
        # 注釈データ
        self.annotations = {}
        self.text_annotations = {}
        self.shape_annotations = {}
        self.selected_annotation = None
        
        # 色設定
        self.pen_color = QColor("black")
        self.marker_color = QColor("#fff176")
        self.text_color = QColor("black")
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UIの構築 - 全てベタ書き"""
        layout = QVBoxLayout(self)
        
        # ツールバー
        toolbar = self.create_exam_toolbar()
        layout.addWidget(toolbar)
        
        # PDF表示エリア
        self.pdf_scroll_area = QScrollArea()
        self.pdf_scroll_area.setWidgetResizable(False)
        self.pdf_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_scroll_area.setStyleSheet("QScrollArea { background: #ffffff; border: none; }")
        
        # PDF表示ラベル
        self.pdf_display_label = QLabel()
        self.pdf_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_display_label.setText("「問題PDFを開く」ボタンをクリックしてPDFを読み込んでください")
        self.pdf_display_label.setStyleSheet("QLabel { background: white; border: 1px solid #ccc; }")
        
        self.pdf_scroll_area.setWidget(self.pdf_display_label)
        layout.addWidget(self.pdf_scroll_area)
        
        # ページナビゲーション
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("前のページ")
        self.next_button = QPushButton("次のページ")
        self.page_label = QLabel("0 / 0")
        self.page_input = QLineEdit()
        self.page_input.setFixedWidth(50)
        self.page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(QLabel("ページ:"))
        nav_layout.addWidget(self.page_input)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
    
    def create_exam_toolbar(self):
        """司法試験用ツールバーの作成 - 冗長でも明確に"""
        toolbar = QToolBar()
        
        # ファイル操作
        self.open_pdf_button = QPushButton("問題PDFを開く")
        self.save_button = QPushButton("注釈を保存")
        toolbar.addWidget(self.open_pdf_button)
        toolbar.addWidget(self.save_button)
        toolbar.addSeparator()
        
        # ツール選択
        self.select_button = QPushButton("選択")
        self.pen_button = QPushButton("ペン")
        self.marker_button = QPushButton("マーカー")
        self.text_button = QPushButton("テキスト")
        self.hand_button = QPushButton("ハンド")
        
        # ツールボタンをグループ化
        self.tool_group = QButtonGroup(self)
        self.tool_group.addButton(self.select_button)
        self.tool_group.addButton(self.pen_button)
        self.tool_group.addButton(self.marker_button)
        self.tool_group.addButton(self.text_button)
        self.tool_group.addButton(self.hand_button)
        self.select_button.setChecked(True)
        
        toolbar.addWidget(self.select_button)
        toolbar.addWidget(self.pen_button)
        toolbar.addWidget(self.marker_button)
        toolbar.addWidget(self.text_button)
        toolbar.addWidget(self.hand_button)
        toolbar.addSeparator()
        
        # 図形ツール
        self.circle_button = QPushButton("円")
        self.triangle_button = QPushButton("三角")
        self.cross_button = QPushButton("×")
        toolbar.addWidget(self.circle_button)
        toolbar.addWidget(self.triangle_button)
        toolbar.addWidget(self.cross_button)
        toolbar.addSeparator()
        
        # ズーム機能
        self.zoom_in_button = QPushButton("拡大")
        self.zoom_out_button = QPushButton("縮小")
        self.zoom_reset_button = QPushButton("リセット")
        toolbar.addWidget(self.zoom_in_button)
        toolbar.addWidget(self.zoom_out_button)
        toolbar.addWidget(self.zoom_reset_button)
        toolbar.addSeparator()
        
        # 表示モード
        self.spread_button = QPushButton("見開き")
        self.spread_button.setCheckable(True)
        toolbar.addWidget(self.spread_button)
        
        return toolbar
    
    def setup_connections(self):
        """接続設定 - 機能ごとに明確に分離"""
        # ファイル操作
        self.open_pdf_button.clicked.connect(self.open_pdf_file)
        self.save_button.clicked.connect(self.save_annotations)
        
        # ツール選択
        self.select_button.clicked.connect(self.select_tool)
        self.pen_button.clicked.connect(self.select_pen_tool)
        self.marker_button.clicked.connect(self.select_marker_tool)
        self.text_button.clicked.connect(self.select_text_tool)
        self.hand_button.clicked.connect(self.select_hand_tool)
        
        # 図形ツール
        self.circle_button.clicked.connect(self.add_circle_shape)
        self.triangle_button.clicked.connect(self.add_triangle_shape)
        self.cross_button.clicked.connect(self.add_cross_shape)
        
        # ズーム機能
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_reset_button.clicked.connect(self.zoom_reset)
        
        # ページナビゲーション
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)
        self.page_input.returnPressed.connect(self.go_to_page_from_input)
        
        # 表示モード
        self.spread_button.toggled.connect(self.toggle_spread_mode)
    
    # ツール選択メソッド - 冗長でも明確に
    def select_tool(self):
        """選択ツールを選択"""
        self.current_tool = "select"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.ArrowCursor)
    
    def select_pen_tool(self):
        """ペンツールを選択"""
        self.current_tool = "pen"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.CrossCursor)
    
    def select_marker_tool(self):
        """マーカーツールを選択"""
        self.current_tool = "marker"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.CrossCursor)
    
    def select_text_tool(self):
        """テキストツールを選択"""
        self.current_tool = "text"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.IBeamCursor)
    
    def select_hand_tool(self):
        """ハンドツールを選択"""
        self.current_tool = "hand"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def update_tool_buttons(self):
        """ツールボタンの状態を更新"""
        self.select_button.setChecked(self.current_tool == "select")
        self.pen_button.setChecked(self.current_tool == "pen")
        self.marker_button.setChecked(self.current_tool == "marker")
        self.text_button.setChecked(self.current_tool == "text")
        self.hand_button.setChecked(self.current_tool == "hand")
    
    # ページナビゲーションメソッド - 冗長でも明確に
    def go_to_previous_page(self):
        """前のページに移動"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()
            self.update_page_controls()
    
    def go_to_next_page(self):
        """次のページに移動"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_current_page()
            self.update_page_controls()
    
    def go_to_page_from_input(self):
        """入力されたページ番号に移動"""
        try:
            page_num = int(self.page_input.text()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.display_current_page()
                self.update_page_controls()
        except ValueError:
            pass
    
    def update_page_controls(self):
        """ページコントロールの状態を更新"""
        self.page_label.setText(f"{self.current_page + 1} / {self.total_pages}")
        self.page_input.setText(str(self.current_page + 1))
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
    
    # ズーム機能メソッド - 冗長でも明確に
    def zoom_in(self):
        """ズームイン"""
        new_zoom = self.zoom_factor * 1.25
        if new_zoom <= self.PDF_ZOOM_MAX:
            self.zoom_factor = new_zoom
            self.display_current_page()
    
    def zoom_out(self):
        """ズームアウト"""
        new_zoom = self.zoom_factor / 1.25
        if new_zoom >= self.PDF_ZOOM_MIN:
            self.zoom_factor = new_zoom
            self.display_current_page()
    
    def zoom_reset(self):
        """ズームをリセット"""
        self.zoom_factor = self.PDF_DEFAULT_ZOOM
        self.display_current_page()
    
    # PDF操作メソッド - 冗長でも明確に
    def open_pdf_file(self):
        """PDFファイルを開く"""
        file_path, _ = QFileDialog.getOpenFileName(self, "PDFファイルを選択", "", "PDF Files (*.pdf)")
        if file_path:
            self.load_pdf_file(file_path)
    
    def load_pdf_file(self, file_path):
        """PDFファイルを読み込み"""
        try:
            self.pdf_document = fitz.open(file_path)
            self.total_pages = len(self.pdf_document)
            self.current_page = 0
            self.display_current_page()
            self.update_page_controls()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"PDFファイルの読み込みに失敗しました: {e}")
    
    def display_current_page(self):
        """現在のページを表示"""
        if not self.pdf_document:
            return
        
        page = self.pdf_document.load_page(self.current_page)
        page_rect = page.rect
        
        # ズームを適用
        scale = self.zoom_factor
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        
        # QImageに変換
        img_data = pix.tobytes("png")
        image = QImage.fromData(img_data)
        pixmap = QPixmap.fromImage(image)
        
        self.pdf_display_label.setPixmap(pixmap)
        self.pdf_display_label.adjustSize()
    
    # 注釈機能メソッド - 冗長でも明確に
    def add_circle_shape(self):
        """円形の図形を追加"""
        if not self.pdf_document:
            QMessageBox.warning(self, "警告", "PDFファイルが開かれていません")
            return
        # 図形追加の実装
        pass
    
    def add_triangle_shape(self):
        """三角形の図形を追加"""
        if not self.pdf_document:
            QMessageBox.warning(self, "警告", "PDFファイルが開かれていません")
            return
        # 図形追加の実装
        pass
    
    def add_cross_shape(self):
        """×印の図形を追加"""
        if not self.pdf_document:
            QMessageBox.warning(self, "警告", "PDFファイルが開かれていません")
            return
        # 図形追加の実装
        pass
    
    def save_annotations(self):
        """注釈を保存"""
        if not self.pdf_document:
            QMessageBox.warning(self, "警告", "PDFファイルが開かれていません")
            return
        # 注釈保存の実装
        pass
    
    def toggle_spread_mode(self, enabled):
        """見開きモードの切り替え"""
        if enabled:
            # 見開きモードの実装
            pass
        else:
            # 通常モードの実装
            pass
