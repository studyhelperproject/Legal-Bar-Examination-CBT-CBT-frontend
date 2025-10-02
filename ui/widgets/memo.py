from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit


class MemoWindow(QWidget):
    MODES = ("left", "right", "full")

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("メモ")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "MemoWindow { background-color: rgba(255, 255, 255, 0.95); border: 1px solid #666; }"
        )

        self._parent_window = parent
        if self._parent_window:
            self._parent_window.installEventFilter(self)

        self.mode = "left"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        self.left_button = QPushButton("左配置")
        self.full_button = QPushButton("全画面")
        self.right_button = QPushButton("右配置")
        self.left_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.full_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar_layout.addWidget(self.left_button)
        toolbar_layout.addWidget(self.full_button)
        toolbar_layout.addWidget(self.right_button)
        toolbar_layout.addStretch()

        close_button = QPushButton("閉じる")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.hide)
        toolbar_layout.addWidget(close_button)

        self.memo_edit = QTextEdit()
        font = self.memo_edit.font()
        font.setPointSize(14)
        self.memo_edit.setFont(font)
        self._base_font = QFont(self.memo_edit.font())

        layout.addLayout(toolbar_layout)
        layout.addWidget(self.memo_edit)

        self.left_button.clicked.connect(lambda: self.show_overlay("left"))
        self.right_button.clicked.connect(lambda: self.show_overlay("right"))
        self.full_button.clicked.connect(lambda: self.show_overlay("full"))

    def apply_font_scale(self, scale):
        if not hasattr(self, '_base_font') or self._base_font is None:
            self._base_font = QFont(self.memo_edit.font())
        base_font = self._base_font
        font = QFont(base_font)
        base_size = font.pointSizeF() if font.pointSizeF() > 0 else font.pointSize()
        if base_size > 0:
            font.setPointSizeF(base_size * scale)
        self.memo_edit.setFont(font)

    def eventFilter(self, obj, event):
        if obj is self._parent_window and event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
            if self.isVisible():
                QTimer.singleShot(0, self._apply_geometry)
        return super().eventFilter(obj, event)

    def show_overlay(self, mode="left"):
        if mode not in self.MODES:
            mode = "left"
        self.mode = mode
        self._apply_geometry()
        self.show()
        self.raise_()
        self.activateWindow()
        self.memo_edit.setFocus()

    def _apply_geometry(self):
        parent = self._parent_window
        if not parent:
            return
        rect = parent.rect()
        top_left = parent.mapToGlobal(rect.topLeft())
        width = rect.width()
        height = rect.height()

        if self.mode == "left":
            x = top_left.x()
            y = top_left.y()
            w = max(1, width // 2)
            h = height
        elif self.mode == "right":
            w = max(1, width // 2)
            h = height
            x = top_left.x() + width - w
            y = top_left.y()
        else:  # full
            x = top_left.x()
            y = top_left.y()
            w = width
            h = height

        self.setGeometry(x, y, w, h)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.mode = self.mode or "left"