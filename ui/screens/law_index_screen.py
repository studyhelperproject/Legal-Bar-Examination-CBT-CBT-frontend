# ui/screens/law_index_screen.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

class LawIndexScreen(QWidget):
    """
    法律索引画面
    - 法令一覧の表示
    - 法令検索機能
    - 条文表示
    - 付箋機能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定値（ハードコーディング）
        self.LAW_TREE_WIDTH = 300
        self.LAW_CONTENT_WIDTH = 700
        self.SEARCH_TIMEOUT = 500  # ミリ秒
        
        # 法令データ
        self.current_law = None
        self.law_content = ""
        self.bookmarks = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_law_data()
    
    def setup_ui(self):
        """UIの構築 - 全てベタ書き"""
        layout = QVBoxLayout(self)
        
        # 検索バー
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("法令を検索...")
        self.search_button = QPushButton("検索")
        self.bookmark_button = QPushButton("付箋")
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.bookmark_button)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        
        # メインエリア（分割）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 法令一覧（左側）
        self.law_tree = QTreeWidget()
        self.law_tree.setHeaderHidden(True)
        self.law_tree.setMaximumWidth(self.LAW_TREE_WIDTH)
        
        # 法令内容（右側）
        self.law_content_area = QTextBrowser()
        self.law_content_area.setOpenExternalLinks(True)
        
        splitter.addWidget(self.law_tree)
        splitter.addWidget(self.law_content_area)
        splitter.setSizes([self.LAW_TREE_WIDTH, self.LAW_CONTENT_WIDTH])
        
        layout.addWidget(splitter)
    
    def setup_connections(self):
        """接続設定 - 機能ごとに明確に分離"""
        # 検索機能
        self.search_input.textChanged.connect(self.search_laws)
        self.search_button.clicked.connect(self.perform_search)
        
        # 法令選択
        self.law_tree.currentItemChanged.connect(self.on_law_selected)
        
        # 付箋機能
        self.bookmark_button.clicked.connect(self.manage_bookmarks)
    
    def load_law_data(self):
        """法令データを読み込み"""
        # 法令データの読み込み実装
        pass
    
    def search_laws(self, text):
        """法令を検索"""
        if not text:
            self.clear_search_results()
            return
        
        # 検索実装
        pass
    
    def perform_search(self):
        """検索を実行"""
        search_text = self.search_input.text()
        if search_text:
            self.search_laws(search_text)
    
    def on_law_selected(self, current, previous):
        """法令が選択された時の処理"""
        if current:
            law_name = current.text(0)
            self.load_law_content(law_name)
    
    def load_law_content(self, law_name):
        """法令内容を読み込み"""
        # 法令内容の読み込み実装
        pass
    
    def manage_bookmarks(self):
        """付箋を管理"""
        # 付箋管理の実装
        pass
    
    def clear_search_results(self):
        """検索結果をクリア"""
        # 検索結果クリアの実装
        pass
