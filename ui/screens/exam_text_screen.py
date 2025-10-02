# ui/screens/exam_text_screen.py
"""
司法試験問題画面のUIコンポーネントを提供します。

このモジュールには、PDF問題文の表示、注釈機能、ページナビゲーション、
ズーム機能などを自己完結的にカプセル化した ExamTextScreen クラスが含まれています。
"""
from typing import Optional, Dict, Any

import fitz
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QPushButton, QButtonGroup,
                             QScrollArea, QLabel, QHBoxLayout, QLineEdit, QMessageBox, QFileDialog)
from PyQt6.QtGui import QColor, QPixmap, QImage
from PyQt6.QtCore import Qt

class ExamTextScreen(QWidget):
    """
    司法試験問題画面のメインウィジェット。

    PDF問題文の表示、注釈機能（ペン、マーカー、テキスト、図形）、
    ページナビゲーション、ズーム機能などを提供します。
    このクラスは、アプリケーションの主要なUI要素を構築し、それらの接続を管理します。
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        ExamTextScreenのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)
        
        # --- 定数設定 ---
        self.PDF_ZOOM_MIN: float = 0.3
        self.PDF_ZOOM_MAX: float = 4.0
        self.PDF_DEFAULT_ZOOM: float = 1.0
        self.PEN_DEFAULT_WIDTH: int = 2
        self.MARKER_DEFAULT_WIDTH: int = 10
        self.TEXT_DEFAULT_SIZE: int = 16
        
        # --- PDF関連の状態 ---
        self.pdf_document: Optional[fitz.Document] = None
        self.current_page: int = 0
        self.total_pages: int = 0
        self.zoom_factor: float = self.PDF_DEFAULT_ZOOM
        self.current_tool: str = "select"
        
        # --- 注釈データ ---
        self.annotations: Dict[Any, Any] = {}
        self.text_annotations: Dict[Any, Any] = {}
        self.shape_annotations: Dict[Any, Any] = {}
        self.selected_annotation: Optional[Any] = None
        
        # --- 色設定 ---
        self.pen_color: QColor = QColor("black")
        self.marker_color: QColor = QColor("#fff176")
        self.text_color: QColor = QColor("black")

        # --- UI要素の型定義 ---
        self.pdf_scroll_area: QScrollArea
        self.pdf_display_label: QLabel
        self.prev_button: QPushButton
        self.next_button: QPushButton
        self.page_label: QLabel
        self.page_input: QLineEdit
        self.tool_group: QButtonGroup
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self) -> None:
        """UIの構築とレイアウト設定を行う。"""
        layout = QVBoxLayout(self)
        
        toolbar = self.create_exam_toolbar()
        layout.addWidget(toolbar)
        
        self.pdf_scroll_area = QScrollArea()
        self.pdf_scroll_area.setWidgetResizable(False)
        self.pdf_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_scroll_area.setStyleSheet("QScrollArea { background: #ffffff; border: none; }")
        
        self.pdf_display_label = QLabel()
        self.pdf_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_display_label.setText("「問題PDFを開く」ボタンをクリックしてPDFを読み込んでください")
        self.pdf_display_label.setStyleSheet("QLabel { background: white; border: 1px solid #ccc; }")
        
        self.pdf_scroll_area.setWidget(self.pdf_display_label)
        layout.addWidget(self.pdf_scroll_area)
        
        nav_layout = self._create_navigation_layout()
        layout.addLayout(nav_layout)

    def _create_navigation_layout(self) -> QHBoxLayout:
        """ページナビゲーション用のレイアウトを作成する。"""
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
        return nav_layout

    def create_exam_toolbar(self) -> QToolBar:
        """問題文表示画面用のツールバーを作成して返す。"""
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
        
        self.tool_group = QButtonGroup(self)
        for btn in [self.select_button, self.pen_button, self.marker_button, self.text_button, self.hand_button]:
            self.tool_group.addButton(btn)
            toolbar.addWidget(btn)
        self.select_button.setChecked(True)
        toolbar.addSeparator()
        
        # 図形ツール
        self.circle_button, self.triangle_button, self.cross_button = QPushButton("円"), QPushButton("三角"), QPushButton("×")
        for btn in [self.circle_button, self.triangle_button, self.cross_button]:
            toolbar.addWidget(btn)
        toolbar.addSeparator()
        
        # ズーム機能
        self.zoom_in_button, self.zoom_out_button, self.zoom_reset_button = QPushButton("拡大"), QPushButton("縮小"), QPushButton("リセット")
        for btn in [self.zoom_in_button, self.zoom_out_button, self.zoom_reset_button]:
            toolbar.addWidget(btn)
        toolbar.addSeparator()
        
        # 表示モード
        self.spread_button = QPushButton("見開き")
        self.spread_button.setCheckable(True)
        toolbar.addWidget(self.spread_button)
        
        return toolbar
    
    def setup_connections(self) -> None:
        """UI要素のシグナルとスロットを接続する。"""
        self.open_pdf_button.clicked.connect(self.open_pdf_file)
        self.save_button.clicked.connect(self.save_annotations)
        
        self.select_button.clicked.connect(self.select_tool)
        self.pen_button.clicked.connect(self.select_pen_tool)
        self.marker_button.clicked.connect(self.select_marker_tool)
        self.text_button.clicked.connect(self.select_text_tool)
        self.hand_button.clicked.connect(self.select_hand_tool)
        
        self.circle_button.clicked.connect(self.add_circle_shape)
        self.triangle_button.clicked.connect(self.add_triangle_shape)
        self.cross_button.clicked.connect(self.add_cross_shape)
        
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_reset_button.clicked.connect(self.zoom_reset)
        
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)
        self.page_input.returnPressed.connect(self.go_to_page_from_input)
        
        self.spread_button.toggled.connect(self.toggle_spread_mode)
    
    def select_tool(self) -> None:
        """選択ツールをアクティブにする。"""
        self.current_tool = "select"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.ArrowCursor)
    
    def select_pen_tool(self) -> None:
        """ペンツールをアクティブにする。"""
        self.current_tool = "pen"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.CrossCursor)
    
    def select_marker_tool(self) -> None:
        """マーカーツールをアクティブにする。"""
        self.current_tool = "marker"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.CrossCursor)
    
    def select_text_tool(self) -> None:
        """テキストツールをアクティブにする。"""
        self.current_tool = "text"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.IBeamCursor)
    
    def select_hand_tool(self) -> None:
        """ハンドツール（スクロール用）をアクティブにする。"""
        self.current_tool = "hand"
        self.update_tool_buttons()
        self.pdf_display_label.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def update_tool_buttons(self) -> None:
        """現在のツールに応じてツールボタンのチェック状態を更新する。"""
        button_map = {
            "select": self.select_button, "pen": self.pen_button,
            "marker": self.marker_button, "text": self.text_button,
            "hand": self.hand_button
        }
        for tool, button in button_map.items():
            button.setChecked(self.current_tool == tool)
    
    def go_to_previous_page(self) -> None:
        """前のページに移動する。"""
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()
            self.update_page_controls()
    
    def go_to_next_page(self) -> None:
        """次のページに移動する。"""
        if self.pdf_document and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_current_page()
            self.update_page_controls()
    
    def go_to_page_from_input(self) -> None:
        """入力フィールドで指定されたページ番号に移動する。"""
        if not self.pdf_document: return
        try:
            page_num = int(self.page_input.text()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.display_current_page()
                self.update_page_controls()
        except ValueError:
            self.page_input.setText(str(self.current_page + 1))
    
    def update_page_controls(self) -> None:
        """ページ番号表示とナビゲーションボタンの有効/無効状態を更新する。"""
        self.page_label.setText(f"{self.current_page + 1} / {self.total_pages}")
        self.page_input.setText(str(self.current_page + 1))
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
    
    def zoom_in(self) -> None:
        """表示を拡大する。"""
        self.zoom_factor = min(self.PDF_ZOOM_MAX, self.zoom_factor * 1.25)
        self.display_current_page()
    
    def zoom_out(self) -> None:
        """表示を縮小する。"""
        self.zoom_factor = max(self.PDF_ZOOM_MIN, self.zoom_factor / 1.25)
        self.display_current_page()
    
    def zoom_reset(self) -> None:
        """ズーム率をデフォルトに戻す。"""
        self.zoom_factor = self.PDF_DEFAULT_ZOOM
        self.display_current_page()
    
    def open_pdf_file(self) -> None:
        """ファイルダイアログを開き、PDFファイルを選択させる。"""
        file_path, _ = QFileDialog.getOpenFileName(self, "PDFファイルを選択", "", "PDF Files (*.pdf)")
        if file_path:
            self.load_pdf_file(file_path)
    
    def load_pdf_file(self, file_path: str) -> None:
        """指定されたパスのPDFファイルを読み込み、表示を初期化する。"""
        try:
            self.pdf_document = fitz.open(file_path)
            self.total_pages = len(self.pdf_document)
            self.current_page = 0
            self.display_current_page()
            self.update_page_controls()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"PDFファイルの読み込みに失敗しました: {e}")
            self.pdf_document = None
    
    def display_current_page(self) -> None:
        """現在のページをレンダリングして表示ラベルに設定する。"""
        if not self.pdf_document:
            return
        
        page = self.pdf_document.load_page(self.current_page)
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=mat)
        
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        
        self.pdf_display_label.setPixmap(pixmap)
        self.pdf_display_label.adjustSize()
    
    def add_circle_shape(self) -> None:
        """円形の図形を追加する。（プレースホルダー）"""
        if not self.pdf_document: QMessageBox.warning(self, "警告", "PDFファイルが開かれていません"); return
        print("円図形追加（未実装）")
    
    def add_triangle_shape(self) -> None:
        """三角形の図形を追加する。（プレースホルダー）"""
        if not self.pdf_document: QMessageBox.warning(self, "警告", "PDFファイルが開かれていません"); return
        print("三角図形追加（未実装）")
    
    def add_cross_shape(self) -> None:
        """×印の図形を追加する。（プレースホルダー）"""
        if not self.pdf_document: QMessageBox.warning(self, "警告", "PDFファイルが開かれていません"); return
        print("×印図形追加（未実装）")
    
    def save_annotations(self) -> None:
        """注釈を保存する。（プレースホルダー）"""
        if not self.pdf_document: QMessageBox.warning(self, "警告", "PDFファイルが開かれていません"); return
        print("注釈保存（未実装）")
    
    def toggle_spread_mode(self, enabled: bool) -> None:
        """見開きモードの切り替え。（プレースホルダー）"""
        print(f"見開きモード: {'有効' if enabled else '無効'}（未実装）")
