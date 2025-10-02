# This file will contain the AnswerSearchBar widget.
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel

class AnswerSearchBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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