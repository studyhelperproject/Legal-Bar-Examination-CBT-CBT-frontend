# ui/screens/memo_screen.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

class MemoScreen(QWidget):
    """
    メモ画面
    - メモの作成・編集
    - 複数メモの管理
    - 検索機能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定値
        self.MAX_MEMOS = 10
        self.DEFAULT_FONT_SIZE = 14
        
        # メモデータ
        self.memos = []
        self.current_memo = 0
        
        self.setup_ui()
        self.setup_connections()
        self.initialize_memos()
    
    def setup_ui(self):
        """UIの構築"""
        layout = QVBoxLayout(self)
        
        # メモ選択バー
        memo_layout = QHBoxLayout()
        self.memo_combo = QComboBox()
        self.new_memo_button = QPushButton("新規メモ")
        self.delete_memo_button = QPushButton("メモ削除")
        
        memo_layout.addWidget(QLabel("メモ:"))
        memo_layout.addWidget(self.memo_combo)
        memo_layout.addWidget(self.new_memo_button)
        memo_layout.addWidget(self.delete_memo_button)
        memo_layout.addStretch()
        
        layout.addLayout(memo_layout)
        
        # メモ編集エリア
        self.memo_edit = QTextEdit()
        self.memo_edit.setFont(QFont("Hiragino Mincho ProN", self.DEFAULT_FONT_SIZE))
        self.memo_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                padding: 10px;
                font-family: 'Hiragino Mincho ProN', 'MS Mincho', serif;
                font-size: 14pt;
                line-height: 1.5;
            }
        """)
        
        layout.addWidget(self.memo_edit)
    
    def setup_connections(self):
        """接続設定 - 機能ごとに明確に分離"""
        # メモ選択
        self.memo_combo.currentIndexChanged.connect(self.on_memo_selected)
        
        # メモ操作
        self.new_memo_button.clicked.connect(self.create_new_memo)
        self.delete_memo_button.clicked.connect(self.delete_current_memo)
        
        # メモ編集
        self.memo_edit.textChanged.connect(self.save_current_memo)
    
    def initialize_memos(self):
        """メモを初期化"""
        for i in range(self.MAX_MEMOS):
            self.memos.append("")
            self.memo_combo.addItem(f"メモ {i + 1}")
    
    def on_memo_selected(self, index):
        """メモが選択された時の処理"""
        self.current_memo = index
        self.memo_edit.setPlainText(self.memos[index])
    
    def create_new_memo(self):
        """新しいメモを作成"""
        # 実装
        pass
    
    def delete_current_memo(self):
        """現在のメモを削除"""
        # 実装
        pass
    
    def save_current_memo(self):
        """現在のメモを保存"""
        if 0 <= self.current_memo < len(self.memos):
            self.memos[self.current_memo] = self.memo_edit.toPlainText()
