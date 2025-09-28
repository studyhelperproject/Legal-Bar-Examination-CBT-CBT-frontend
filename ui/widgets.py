# ui/widgets.py
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath
from PyQt6.QtCore import Qt, QPointF, QPoint

class PDFDisplayLabel(QLabel):
    # (PDFDisplayLabel class is the same as the last working version)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.drawing = False
        self.last_point = QPointF()
        self.current_path = QPainterPath()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.main_window.current_tool in ["pen", "marker"]:
            if self.pixmap() and self.pixmap().rect().contains(event.pos()):
                self.drawing = True
                self.last_point = QPointF(event.pos())
                self.current_path.moveTo(self.last_point)

    def mouseMoveEvent(self, event):
        if self.drawing and self.main_window.current_tool in ["pen", "marker"]:
            if self.pixmap() and self.pixmap().rect().contains(event.pos()):
                self.current_path.lineTo(QPointF(event.pos()))
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            page = self.main_window.current_page
            if page not in self.main_window.annotations:
                self.main_window.annotations[page] = []
            
            tool_type = self.main_window.current_tool
            color = self.main_window.pen_color if tool_type == "pen" else self.main_window.marker_color
            width = self.main_window.pen_width if tool_type == "pen" else self.main_window.marker_width
            
            self.main_window.annotations[page].append({
                "type": tool_type,
                "path": QPainterPath(self.current_path),
                "color": color,
                "width": width
            })
            self.current_path = QPainterPath()
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap():
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        page = self.main_window.current_page
        if page in self.main_window.annotations:
            for item in self.main_window.annotations[page]:
                pen = QPen()
                pen.setColor(item["color"])
                pen.setWidth(item["width"])
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                if item["type"] == "marker":
                    pen.setColor(QColor(item["color"].red(), item["color"].green(), item["color"].blue(), 128))
                
                painter.setPen(pen)
                painter.drawPath(item["path"])

        if self.drawing:
            tool_type = self.main_window.current_tool
            color = self.main_window.pen_color if tool_type == "pen" else self.main_window.marker_color
            width = self.main_window.pen_width if tool_type == "pen" else self.main_window.marker_width
            pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            if tool_type == "marker":
                 pen.setColor(QColor(color.red(), color.green(), color.blue(), 128))
            painter.setPen(pen)
            painter.drawPath(self.current_path)


class MemoWindow(QWidget):
    # (MemoWindow class is the same)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("メモ")
        self.setGeometry(200, 200, 500, 700)
        layout = QVBoxLayout(self)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(QPushButton("左配置"))
        toolbar_layout.addWidget(QPushButton("全画面"))
        toolbar_layout.addWidget(QPushButton("右配置"))
        toolbar_layout.addStretch()
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.hide)
        toolbar_layout.addWidget(close_button)
        self.memo_edit = QTextEdit()
        font = self.memo_edit.font()
        font.setPointSize(14)
        self.memo_edit.setFont(font)
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.memo_edit)
        self.setLayout(layout)

class AnswerSheet(QWidget):
    # (AnswerSheet class is the same)
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        self.search_replace_bar = QWidget()
        search_layout = QHBoxLayout(self.search_replace_bar)
        
        self.answer_search_input = QLineEdit()
        self.answer_search_input.setPlaceholderText("検索")
        self.search_count_label = QLabel("0/0")
        self.search_prev_button = QPushButton("↑")
        self.search_next_button = QPushButton("↓")
        self.answer_replace_input = QLineEdit()
        self.answer_replace_input.setPlaceholderText("置換")
        self.answer_replace_button = QPushButton("置換")
        self.answer_replace_all_button = QPushButton("一括")
        
        search_layout.addWidget(self.answer_search_input)
        search_layout.addWidget(self.search_count_label)
        search_layout.addWidget(self.search_prev_button)
        search_layout.addWidget(self.search_next_button)
        search_layout.addWidget(self.answer_replace_input)
        search_layout.addWidget(self.answer_replace_button)
        search_layout.addWidget(self.answer_replace_all_button)
        self.search_replace_bar.setVisible(False)
        
        info_bar = QHBoxLayout()
        self.char_count_label = QLabel("0/184行 0/5,520文字 (空白含む)")
        self.toggle_search_button = QPushButton("検索")
        self.toggle_search_button.setCheckable(True)
        self.answer_undo_button = QPushButton("元に戻す")
        self.answer_redo_button = QPushButton("やり直し")
        info_bar.addWidget(self.char_count_label)
        info_bar.addStretch()
        info_bar.addWidget(self.toggle_search_button)
        info_bar.addWidget(self.answer_undo_button)
        info_bar.addWidget(self.answer_redo_button)
        
        self.answer_text_edit = QTextEdit()
        font = self.answer_text_edit.font()
        font.setPointSize(14)
        self.answer_text_edit.setFont(font)
        
        layout.addLayout(info_bar)
        layout.addWidget(self.search_replace_bar)
        layout.addWidget(self.answer_text_edit)