from PyQt6.QtCore import pyqtSignal, Qt, QEvent, QPoint
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QToolButton

class TextAnnotationWidget(QWidget):
    delete_requested = pyqtSignal(QWidget)

    def __init__(self, parent=None, color=QColor("black"), font_point=16):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._selected = False
        self._press_pos = None
        self._widget_start = None
        self._dragging = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
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
        # Traverse up to find the main window
        widget = self
        while widget is not None:
            if hasattr(widget, 'history_handler'): # A good indicator of MainWindow
                return widget
            widget = widget.parentWidget()
        return None

    def set_selected(self, selected):
        if self._selected == selected: return
        self._selected = selected
        self._apply_frame_style()
        if selected:
            self.delete_button.show()
            self._ensure_button_position()
        else:
            if not self.text_edit.hasFocus() and not self.underMouse():
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
        self.text_edit.setStyleSheet(f"QTextEdit {{ background-color: transparent; border: none; color: {self._color.name()}; }}")

    def _begin_drag(self, global_pos):
        self._press_pos = global_pos
        self._widget_start = self.pos()
        self._dragging = False

    def _apply_drag(self, global_pos):
        if self._press_pos is None: return False
        delta = global_pos - self.mapToGlobal(self._press_pos)
        if not self._dragging and delta.manhattanLength() > 5:
            self._dragging = True
        if not self._dragging: return False

        new_pos = self._widget_start + delta
        # Clamp position within parent
        if self.parentWidget():
            max_x = self.parentWidget().width() - self.width()
            max_y = self.parentWidget().height() - self.height()
            new_pos.setX(max(0, min(new_pos.x(), max_x)))
            new_pos.setY(max(0, min(new_pos.y(), max_y)))
        self.move(new_pos)
        return True

    def _end_drag(self):
        was_dragging = self._dragging
        self._press_pos = None; self._widget_start = None; self._dragging = False
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
                    main_window.annotation_handler.select_text_annotation(self)
                    if main_window.annotation_handler.current_tool in ("select", "text"):
                        self._press_pos = event.pos()
                        self._widget_start = self.pos()
            elif event.type() == QEvent.Type.MouseMove and event.buttons() & Qt.MouseButton.LeftButton:
                if self._apply_drag(event.pos()):
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                if self._end_drag():
                    main_window = self._main_window()
                    if main_window and not main_window.history_handler.is_restoring():
                         main_window.history_handler.register_snapshot()
                    return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.delete_button.geometry().contains(event.pos()):
            main_window = self._main_window()
            if main_window:
                main_window.annotation_handler.select_text_annotation(self)
                if main_window.annotation_handler.current_tool in ("select", "text"):
                    self._press_pos = event.pos()
                    self._widget_start = self.pos()
                    self.text_edit.setFocus()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._apply_drag(event.pos()):
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._end_drag():
                main_window = self._main_window()
                if main_window and not main_window.history_handler.is_restoring():
                    main_window.history_handler.register_snapshot()
                return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ensure_button_position()

    def enterEvent(self, event):
        if self._selected or self.text_edit.hasFocus():
            self.delete_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.text_edit.hasFocus() and not self._selected:
            self.delete_button.hide()
        super().leaveEvent(event)

    def _ensure_button_position(self):
        if not self.delete_button: return
        size = self.delete_button.sizeHint()
        self.delete_button.resize(size)
        self.delete_button.move(self.width() - size.width() - 8, 6)
        self.delete_button.raise_()

    def _emit_delete(self):
        if self.text_edit.hasFocus(): self.text_edit.clearFocus()
        self.delete_requested.emit(self)