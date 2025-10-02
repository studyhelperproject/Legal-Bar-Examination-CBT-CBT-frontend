"""
答案エディタ用の検索・置換バーウィジェットを提供します。
"""
from typing import Optional

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel

class AnswerSearchBar(QWidget):
    """
    答案エディタ内でテキストの検索と置換を行うためのUIコンポーネント。

    検索語入力、次/前へ移動、結果カウント表示、置換語入力、
    個別置換、一括置換の機能を持つウィジェットで構成されます。
    デフォルトでは非表示になっています。
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        AnswerSearchBarのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)

        # --- UI要素の型定義 ---
        self.search_input: QLineEdit
        self.count_label: QLabel
        self.prev_button: QPushButton
        self.next_button: QPushButton
        self.replace_input: QLineEdit
        self.replace_button: QPushButton
        self.replace_all_button: QPushButton

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索")

        self.count_label = QLabel("0/0")

        self.prev_button = QPushButton("↑")
        self.next_button = QPushButton("↓")

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("置換")

        self.replace_button = QPushButton("置換")
        self.replace_all_button = QPushButton("一括")

        layout.addWidget(self.search_input)
        layout.addWidget(self.count_label)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.replace_input)
        layout.addWidget(self.replace_button)
        layout.addWidget(self.replace_all_button)

        self.setVisible(False)