from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QSize, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import QWidget, QToolButton

class ShapeAnnotationWidget(QWidget):
    delete_requested = pyqtSignal(QWidget)
    HANDLE_SIZE = 14
    MIN_SIZE = QSize(60, 60)

    def __init__(self, parent=None, shape_type="circle", initial_size=QSize(160, 160)):
        super().__init__(parent)
        self.shape_type = shape_type
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setMouseTracking(True)
        self._selected = False

        self.delete_button = QToolButton(self)
        self.delete_button.setText("削除")
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.setStyleSheet("QToolButton { background-color: rgba(0, 0, 0, 0.55); color: white; padding: 2px 8px; border-radius: 4px; }")
        self.delete_button.setAutoRaise(True)
        self.delete_button.hide()
        self.delete_button.clicked.connect(self.delete_requested.emit)

        self._press_pos = None
        self._widget_start = None
        self._size_start = None
        self._interaction_mode = None
        self._dragging = False

        self.setMinimumSize(self.MIN_SIZE)
        self.resize(max(initial_size.width(), self.MIN_SIZE.width()), max(initial_size.height(), self.MIN_SIZE.height()))
        self._ensure_delete_button_position()

    def _main_window(self):
        widget = self
        while widget is not None:
            if hasattr(widget, 'history_handler'): return widget
            widget = widget.parentWidget()
        return None

    def set_selected(self, selected):
        if self._selected == selected: return
        self._selected = selected
        self.delete_button.setVisible(selected)
        if selected: self._ensure_delete_button_position()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(6, 6, -6, -6)

        accent = QColor("#ff9800") if self._selected else QColor("#1976d2")
        pen = QPen(accent, 4 if self._selected else 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self.shape_type == "circle":
            painter.drawEllipse(rect)
        elif self.shape_type == "triangle":
            path = QPainterPath()
            path.moveTo(rect.center().x(), rect.top())
            path.lineTo(rect.left(), rect.bottom())
            path.lineTo(rect.right(), rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)
        else: # cross
            painter.drawLine(rect.topLeft(), rect.bottomRight())
            painter.drawLine(rect.topRight(), rect.bottomLeft())

        if self._selected:
            handle_rect = self._resize_handle_rect()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(accent)
            painter.drawRect(handle_rect)

    def _start_interaction(self, global_pos, mode):
        self._interaction_mode = mode
        self._press_pos = global_pos
        self._widget_start = self.pos()
        self._size_start = self.size()
        self._dragging = False
        self.setCursor(Qt.CursorShape.ClosedHandCursor if mode == "drag" else Qt.CursorShape.SizeFDiagCursor)

    def _update_interaction(self, global_pos):
        if self._interaction_mode is None: return False
        delta = global_pos - self._press_pos
        if not self._dragging and delta.manhattanLength() > 5:
            self._dragging = True
        if not self._dragging: return False

        if self._interaction_mode == "drag":
            new_pos = self._widget_start + delta
            if self.parentWidget(): # Clamp to parent
                max_x = self.parentWidget().width() - self.width()
                max_y = self.parentWidget().height() - self.height()
                new_pos.setX(max(0, min(new_pos.x(), max_x)))
                new_pos.setY(max(0, min(new_pos.y(), max_y)))
            self.move(new_pos)
        else: # resize
            new_w = max(self.MIN_SIZE.width(), self._size_start.width() + delta.x())
            new_h = max(self.MIN_SIZE.height(), self._size_start.height() + delta.y())
            self.resize(new_w, new_h)

        self.update()
        return True

    def _end_interaction(self):
        if self._interaction_mode is None: return False
        was_dragging = self._dragging
        self._interaction_mode = None
        self._press_pos = None
        self._dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor if self.underMouse() else Qt.CursorShape.ArrowCursor)
        if was_dragging:
            main_window = self._main_window()
            if main_window and not main_window.history_handler.is_restoring():
                main_window.history_handler.register_snapshot()
        return was_dragging

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton: return super().mousePressEvent(event)
        main_window = self._main_window()
        if main_window: main_window.annotation_handler.select_shape_annotation(self)

        if main_window and main_window.annotation_handler.current_tool == "select":
            mode = "resize" if self._resize_handle_rect().contains(event.pos()) else "drag"
            self._start_interaction(event.globalPosition().toPoint(), mode)
            self.setFocus()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._update_interaction(event.globalPosition().toPoint()):
                event.accept()
        elif self._interaction_mode is None:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor if self._resize_handle_rect().contains(event.pos()) else Qt.CursorShape.OpenHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._end_interaction():
                event.accept()

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._interaction_mode is None:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ensure_delete_button_position()

    def _resize_handle_rect(self):
        return QRect(self.width() - self.HANDLE_SIZE - 2, self.height() - self.HANDLE_SIZE - 2, self.HANDLE_SIZE, self.HANDLE_SIZE)

    def _ensure_delete_button_position(self):
        size = self.delete_button.sizeHint()
        self.delete_button.resize(size)
        self.delete_button.move(self.width() - size.width() - 8, 6)
        self.delete_button.raise_()