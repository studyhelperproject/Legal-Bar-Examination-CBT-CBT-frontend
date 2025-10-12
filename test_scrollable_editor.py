import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from ui.widgets.scrollable_editor import ScrollableAnswerEditor
from ui.widgets.text_editor_config import TextEditorConfig

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test ScrollableAnswerEditor")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 設定オブジェクトを作成
        config = TextEditorConfig()
        config.line_height = 150  # 150%

        # ScrollableAnswerEditor をインスタンス化
        self.editor = ScrollableAnswerEditor(config=config)
        
        initial_text = (
            "This is the first paragraph.\\n\\n"
            "This is the second paragraph. You can adjust the line spacing "
            "for the entire document using the config.\\n\\n"
            "This is the third paragraph, demonstrating how the spacing applies "
            "to all blocks of text in the editor."
        )
        self.editor.set_content(initial_text)

        layout.addWidget(self.editor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())