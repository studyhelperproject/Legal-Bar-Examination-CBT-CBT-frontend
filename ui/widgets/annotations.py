from PyQt6.QtCore import pyqtSignal, Qt, QEvent, QPoint, QSize, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QToolButton


class TextAnnotationWidget(QWidget):
    delete_requested = pyqtSignal(QWidget)

    def __init__(self, parent=None, color=QColor("black"), font_point=16):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.85); border: 1px solid #666; border-radius: 4px;")
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._selected = False

        self._press_pos = None
        self._widget_start = None
        self._dragging = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.text_edit = QTextEdit(self)
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setPlaceholderText("テキストを入力...")
        self.text_edit.setStyleSheet("QTextEdit { background-color: transparent; border: none; }")
        layout.addWidget(self.text_edit)

        self.delete_button = QToolButton(self)
        self.delete_button.setText("削除")
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.setStyleSheet("QToolButton { background-color: rgba(0, 0, 0, 0.55); color: white; padding: 2px 8px; border-radius: 4px; }")
        self.delete_button.setAutoRaise(True)
        self.delete_button.hide()
        self.delete_button.clicked.connect(self._emit_delete)

        self.text_edit.installEventFilter(self)
        self.text_edit.textChanged.connect(self._ensure_button_position)

        self._color = QColor(color)
        self._font_point = font_point
        self.setMinimumSize(160, 60)
        self.resize(220, 80)
        self.set_text_style(color, font_point)
        self._apply_frame_style()

    def _main_window(self):
        widget = self.parentWidget()
        while widget is not None:
            if hasattr(widget, 'main_window'):
                return widget.main_window
            widget = widget.parentWidget()
        window = self.window()
        return window if hasattr(window, 'register_snapshot') else None

    def set_selected(self, selected):
        if self._selected == selected:
            return
        self._selected = selected
        self._apply_frame_style()
        if selected:
            self.delete_button.show()
            self._ensure_button_position()
        else:
            if not self.text_edit.hasFocus() and not self.underMouse() and not self._dragging:
                self.delete_button.hide()

    def _apply_frame_style(self):
        border_color = "#ff9800" if self._selected else "#666"
        border_width = 2 if self._selected else 1
        self.setStyleSheet(
            f"background-color: rgba(255, 255, 255, 0.85); border: {border_width}px solid {border_color}; border-radius: 4px;"
        )

    def set_text_style(self, color, font_point):
        self._color = QColor(color)
        self._font_point = font_point
        font = self.text_edit.font()
        font.setPointSizeF(float(font_point))
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet(
            "QTextEdit { background-color: transparent; border: none; color: %s; }" % self._color.name()
        )
        self._apply_frame_style()

    def focus_text(self):
        self.text_edit.selectAll()
        self.text_edit.setFocus()

    def _begin_drag(self, global_pos):
        self._press_pos = global_pos
        self._widget_start = self.pos()
        self._dragging = False

    def _apply_drag(self, global_pos):
        if self._press_pos is None:
            return False
        delta = global_pos - self._press_pos
        if not self._dragging and delta.manhattanLength() > 5:
            self._dragging = True
        if not self._dragging:
            return False
        parent_rect = self.parentWidget().rect() if self.parentWidget() else None
        new_pos = QPoint(self._widget_start.x() + delta.x(), self._widget_start.y() + delta.y())
        if parent_rect is not None:
            max_x = parent_rect.width() - self.width()
            max_y = parent_rect.height() - self.height()
            new_pos.setX(max(0, min(new_pos.x(), max_x)))
            new_pos.setY(max(0, min(new_pos.y(), max_y)))
        self.move(new_pos)
        return True

    def _end_drag(self):
        was_dragging = self._dragging
        self._press_pos = None
        self._widget_start = None
        self._dragging = False
        return was_dragging

    def eventFilter(self, obj, event):
        if obj is self.text_edit:
            if event.type() == QEvent.Type.FocusIn:
                self.delete_button.show()
                self._ensure_button_position()
            elif event.type() == QEvent.Type.FocusOut:
                if not self.underMouse() and not self._selected:
                    self.delete_button.hide()
            elif event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                main_window = self._main_window()
                if main_window:
                    main_window.select_text_annotation(self)
                allow_drag = (not main_window) or main_window.current_tool in ("select", "text")
                if allow_drag:
                    self._begin_drag(event.globalPosition().toPoint())
            elif event.type() == QEvent.Type.MouseMove and event.buttons() & Qt.MouseButton.LeftButton:
                if self._apply_drag(event.globalPosition().toPoint()):
                    event.accept()
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                if self._end_drag():
                    event.accept()
                    main_window = self._main_window()
                    if main_window:
                        main_window.register_snapshot()
                    return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.delete_button.geometry().contains(event.pos()):
                main_window = self._main_window()
                if main_window:
                    main_window.select_text_annotation(self)
                allow_drag = (not main_window) or main_window.current_tool in ("select", "text")
                if allow_drag:
                    self._begin_drag(event.globalPosition().toPoint())
                    self.text_edit.setFocus()
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._apply_drag(event.globalPosition().toPoint()):
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._end_drag():
                event.accept()
                main_window = self._main_window()
                if main_window:
                    main_window.register_snapshot()
                return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ensure_button_position()

    def enterEvent(self, event):
        if (self._selected or self.text_edit.hasFocus()) and not self.delete_button.isVisible():
            self.delete_button.show()
            self._ensure_button_position()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.text_edit.hasFocus() and not self._dragging and not self._selected:
            self.delete_button.hide()
        super().leaveEvent(event)

    def _ensure_button_position(self):
        if not self.delete_button:
            return
        size = self.delete_button.sizeHint()
        self.delete_button.resize(size)
        self.delete_button.move(max(4, self.width() - size.width() - 8), 6)
        self.delete_button.raise_()

    def _emit_delete(self):
        if self.text_edit.hasFocus():
            self.text_edit.clearFocus()
        self.delete_requested.emit(self)


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
        self.delete_button.setStyleSheet(
            "QToolButton { background-color: rgba(0, 0, 0, 0.55); color: white; padding: 2px 8px; border-radius: 4px; }"
        )
        self.delete_button.setAutoRaise(True)
        self.delete_button.hide()
        self.delete_button.clicked.connect(self._emit_delete)

        self._press_pos = None
        self._widget_start = None
        self._size_start = None
        self._interaction_mode = None
        self._dragging = False

        self.setMinimumSize(self.MIN_SIZE)
        self.resize(max(initial_size.width(), self.MIN_SIZE.width()),
                    max(initial_size.height(), self.MIN_SIZE.height()))
        self._ensure_delete_button_position()

    def _main_window(self):
        parent = self.parentWidget()
        return parent.main_window if parent else None

    def set_selected(self, selected):
        if self._selected == selected:
            return
        self._selected = selected
        if selected:
            self.delete_button.show()
            self._ensure_delete_button_position()
        else:
            self.delete_button.hide()
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
        else:  # cross
            painter.drawLine(rect.topLeft(), rect.bottomRight())
            painter.drawLine(rect.topRight(), rect.bottomLeft())

        handle_rect = self._resize_handle_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawRect(handle_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self._main_window()
            if main_window:
                main_window.select_shape_annotation(self)
            allow_interaction = (not main_window) or main_window.current_tool == "select"
            if allow_interaction:
                if self._resize_handle_rect().contains(event.pos()):
                    self._start_interaction(event.globalPosition().toPoint(), "resize")
                else:
                    self._start_interaction(event.globalPosition().toPoint(), "drag")
                self.setFocus()
                self.delete_button.show()
                self._ensure_delete_button_position()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._update_interaction(event.globalPosition().toPoint()):
                event.accept()
                return
        else:
            self._update_hover_cursor(event.pos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._end_interaction():
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        if (self._selected or self.hasFocus()) and not self.delete_button.isVisible():
            self.delete_button.show()
            self._ensure_delete_button_position()
        if self._interaction_mode is None:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.hasFocus() and not self._selected:
            self.delete_button.hide()
        if self._interaction_mode is None:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def focusInEvent(self, event):
        self.delete_button.show()
        self._ensure_delete_button_position()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        if not self.underMouse() and not self._selected:
            self.delete_button.hide()
        super().focusOutEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ensure_delete_button_position()

    def _start_interaction(self, global_pos, mode):
        self._interaction_mode = mode
        self._press_pos = global_pos
        self._widget_start = self.pos()
        self._size_start = self.size()
        self._dragging = False
        if mode == "drag":
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)

    def _update_interaction(self, global_pos):
        if self._interaction_mode is None or self._press_pos is None:
            return False
        delta = global_pos - self._press_pos
        if not self._dragging and delta.manhattanLength() > 5:
            self._dragging = True
        if not self._dragging:
            return False

        parent_rect = self.parentWidget().rect() if self.parentWidget() else None

        if self._interaction_mode == "drag":
            new_pos = QPoint(self._widget_start.x() + delta.x(), self._widget_start.y() + delta.y())
            if parent_rect is not None:
                max_x = parent_rect.width() - self.width()
                max_y = parent_rect.height() - self.height()
                new_pos.setX(max(0, min(new_pos.x(), max_x)))
                new_pos.setY(max(0, min(new_pos.y(), max_y)))
            self.move(new_pos)
        else:
            min_w = self.MIN_SIZE.width()
            min_h = self.MIN_SIZE.height()
            new_width = max(min_w, self._size_start.width() + delta.x())
            new_height = max(min_h, self._size_start.height() + delta.y())
            if parent_rect is not None:
                max_width = parent_rect.width() - self._widget_start.x()
                max_height = parent_rect.height() - self._widget_start.y()
                new_width = max(min_w, min(new_width, max_width))
                new_height = max(min_h, min(new_height, max_height))
            self.resize(new_width, new_height)
        self._ensure_delete_button_position()
        self.update()
        return True

    def _end_interaction(self):
        if self._interaction_mode is None:
            return False
        was_dragging = self._dragging
        self._interaction_mode = None
        self._press_pos = None
        self._widget_start = None
        self._size_start = None
        self._dragging = False
        if self.underMouse():
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        if was_dragging:
            main_window = self._main_window()
            if main_window:
                main_window.register_snapshot()
        return was_dragging

    def _update_hover_cursor(self, pos):
        if self._interaction_mode is not None:
            return
        if self._resize_handle_rect().contains(pos):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def _resize_handle_rect(self):
        return QRect(
            self.width() - self.HANDLE_SIZE - 2,
            self.height() - self.HANDLE_SIZE - 2,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE,
        )

    def _ensure_delete_button_position(self):
        size = self.delete_button.sizeHint()
        self.delete_button.resize(size)
        self.delete_button.move(max(4, self.width() - size.width() - 8), 6)
        self.delete_button.raise_()

    def _emit_delete(self):
        self.delete_requested.emit(self)