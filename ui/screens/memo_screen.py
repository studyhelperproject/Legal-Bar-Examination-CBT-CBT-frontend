# ui/screens/memo_screen.py
"""
メモ画面のUIコンポーネントを提供します。

このモジュールには、ユーザーが複数のメモを作成・編集するためのUIを提供する
MemoScreen クラスが含まれています。
"""
from typing import Optional, List

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QPushButton, QLabel, QTextEdit)
from PyQt6.QtGui import QFont

class MemoScreen(QWidget):
    """
    メモ画面のメインウィジェット。

    複数のメモを切り替えて編集する機能を提供します。
    UIはメモ選択用のコンボボックス、新規作成・削除ボタン、
    およびテキスト編集エリアから構成されます。
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        MemoScreenのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)
        
        # --- 定数設定 ---
        self.MAX_MEMOS: int = 10
        self.DEFAULT_FONT_SIZE: int = 14

        # --- メモデータ ---
        self.memos: List[str] = []
        self.current_memo: int = 0
        
        # --- UI要素の型定義 ---
        self.memo_combo: QComboBox
        self.new_memo_button: QPushButton
        self.delete_memo_button: QPushButton
        self.memo_edit: QTextEdit
        
        self.setup_ui()
        self.setup_connections()
        self.initialize_memos()
    
    def setup_ui(self) -> None:
        """UIの構築とレイアウト設定を行う。"""
        layout = QVBoxLayout(self)
        
        memo_layout = self._create_memo_bar_layout()
        layout.addLayout(memo_layout)

        self.memo_edit = self._create_memo_edit_area()
        layout.addWidget(self.memo_edit)

    def _create_memo_bar_layout(self) -> QHBoxLayout:
        """メモ選択バーのレイアウトを作成する。"""
        memo_layout = QHBoxLayout()
        self.memo_combo = QComboBox()
        self.new_memo_button = QPushButton("新規メモ")
        self.delete_memo_button = QPushButton("メモ削除")
        
        memo_layout.addWidget(QLabel("メモ:"))
        memo_layout.addWidget(self.memo_combo)
        memo_layout.addWidget(self.new_memo_button)
        memo_layout.addWidget(self.delete_memo_button)
        memo_layout.addStretch()
        return memo_layout

    def _create_memo_edit_area(self) -> QTextEdit:
        """メモ編集エリアのウィジェットを作成し、スタイルを設定する。"""
        memo_edit = QTextEdit()
        memo_edit.setFont(QFont("Hiragino Mincho ProN", self.DEFAULT_FONT_SIZE))
        memo_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                padding: 10px;
                font-family: 'Hiragino Mincho ProN', 'MS Mincho', serif;
                font-size: 14pt;
                line-height: 1.5;
            }
        """)
        return memo_edit
    
    def setup_connections(self) -> None:
        """UI要素のシグナルとスロットを接続する。"""
        self.memo_combo.currentIndexChanged.connect(self.on_memo_selected)
        self.new_memo_button.clicked.connect(self.create_new_memo)
        self.delete_memo_button.clicked.connect(self.delete_current_memo)
        self.memo_edit.textChanged.connect(self.save_current_memo)
    
    def initialize_memos(self) -> None:
        """
        メモデータを初期化し、コンボボックスに項目を追加する。
        MAX_MEMOSで定義された数だけ空のメモを作成します。
        """
        for i in range(self.MAX_MEMOS):
            self.memos.append("")
            self.memo_combo.addItem(f"メモ {i + 1}")
    
    def on_memo_selected(self, index: int) -> None:
        """
        コンボボックスでメモが選択されたときに呼び出されるスロット。

        Args:
            index (int): 選択されたメモのインデックス。
        """
        self.current_memo = index
        self.memo_edit.setPlainText(self.memos[index])
    
    def create_new_memo(self) -> None:
        """新しいメモを作成する。（プレースホルダー）"""
        print("新規メモ作成（未実装）")
        pass
    
    def delete_current_memo(self) -> None:
        """現在選択されているメモを削除する。（プレースホルダー）"""
        print("現在のメモを削除（未実装）")
        pass
    
    def save_current_memo(self) -> None:
        """
        現在のメモ編集エリアの内容を対応するデータに保存する。
        テキストが変更されるたびに呼び出されます。
        """
        if 0 <= self.current_memo < len(self.memos):
            self.memos[self.current_memo] = self.memo_edit.toPlainText()
