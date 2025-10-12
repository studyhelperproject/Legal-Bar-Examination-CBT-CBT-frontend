import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QLabel,
    QTextEdit
)
from PyQt6.QtGui import QTextCursor, QTextBlockFormat
from PyQt6.QtCore import Qt

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QPlainTextEdit Line Spacing Test")
        self.setGeometry(100, 100, 600, 400)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Line spacing control
        spacing_label = QLabel("Line Spacing (%):")
        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setRange(100, 300)
        self.spacing_spinbox.setValue(100)
        self.spacing_spinbox.setSingleStep(10)
        self.spacing_spinbox.valueChanged.connect(self.set_line_spacing)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("Enter text here...")

        initial_text = (
            "This is the first paragraph.\n\n"
            "This is the second paragraph. You can adjust the line spacing "
            "for the entire document using the spin box above.\n\n"
            "This is the third paragraph, demonstrating how the spacing applies "
            "to all blocks of text in the editor."
        )
        self.text_edit.setPlainText(initial_text)

        # Add widgets to layout
        layout.addWidget(spacing_label)
        layout.addWidget(self.spacing_spinbox)
        layout.addWidget(self.text_edit)

        # Set initial line spacing
        self.set_line_spacing(self.spacing_spinbox.value())

    def set_line_spacing(self, value):
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        doc = self.text_edit.document()
        block = doc.begin()
        while block.isValid():
            block_format = block.blockFormat()
            block_format.setLineHeight(value, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            temp_cursor = QTextCursor(block)
            temp_cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            temp_cursor.setBlockFormat(block_format)
            block = block.next()
        cursor.endEditBlock()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec())