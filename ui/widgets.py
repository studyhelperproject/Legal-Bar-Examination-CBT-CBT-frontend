# ui/widgets.py
import os
import unicodedata

from PyQt6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLineEdit, QMenu, QToolButton, QPlainTextEdit, QSizePolicy, QStackedWidget,
    QStackedLayout, QFrame, QScrollArea
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPainterPath, QPainterPathStroker, QFont,
    QFontMetrics, QFontInfo, QTextOption, QTextFormat, QTextCursor,
    QTextBlockFormat
)
from PyQt6.QtCore import Qt, QPointF, QEvent, QPoint, QSize, QRect, pyqtSignal, QTimer

try:
    from PyQt6.QtWidgets import QWIDGETSIZE_MAX
except ImportError:  # Fallback constant defined in Qt
    QWIDGETSIZE_MAX = 16777215


ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
ANSWER_TEMPLATE_PATH = os.path.join(ASSETS_DIR, "answer_template.pdf")

class PDFDisplayLabel(QLabel):
    # (PDFDisplayLabel class is the same as the last working version)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.drawing = False
        self.current_path = QPainterPath()
        self._stroke_drag_active = False
        self._stroke_drag_start = QPointF()
        self._stroke_original_path = None
        self._stroke_drag_page = None
        self._stroke_drag_index = None
        self._hand_drag_active = False
        self._hand_drag_start = QPointF()
        self._hand_scroll_start = QPoint()

    def mousePressEvent(self, event):
        handled = False
        button = event.button()
        if button == Qt.MouseButton.LeftButton and self.main_window.current_tool == "hand":
            scroll_area = getattr(self.main_window, "pdf_scroll_area", None)
            if scroll_area:
                self._hand_drag_active = True
                self._hand_drag_start = event.position()
                self._hand_scroll_start = QPoint(
                    scroll_area.horizontalScrollBar().value(),
                    scroll_area.verticalScrollBar().value()
                )
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
        if button == Qt.MouseButton.LeftButton and self.main_window.current_tool == "text":
            if self.pixmap() and self.pixmap().rect().contains(event.pos()):
                self._create_text_annotation(event.pos())
                event.accept()
                return
        if button in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton) and self.pixmap() and self.pixmap().rect().contains(event.pos()):
            page = self.main_window.current_page
            hit = self._find_annotation_at(page, QPointF(event.pos()))
            if hit is not None:
                index, item = hit
                if self.main_window.current_tool == "select" and button == Qt.MouseButton.LeftButton:
                    if item.get("type") in ("pen", "marker"):
                        self.main_window.select_stroke_annotation(page, index)
                        self._begin_stroke_drag(page, index, event.position())
                    else:
                        self.main_window.clear_selection()
                else:
                    self._show_annotation_menu(event.pos(), page, index, item)
                handled = True
                event.accept()
            elif button == Qt.MouseButton.LeftButton and self.main_window.current_tool in ["pen", "marker"]:
                self.drawing = True
                self.current_path = QPainterPath()
                self.current_path.moveTo(QPointF(event.pos()))
                handled = True
                event.accept()
        if not handled and button == Qt.MouseButton.RightButton:
            event.accept()
            handled = True
        if not handled and self.main_window.current_tool == "select" and button == Qt.MouseButton.LeftButton:
            self.main_window.clear_selection()
            handled = True
            event.accept()
        if not handled:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._hand_drag_active and self.main_window.current_tool == "hand":
            scroll_area = getattr(self.main_window, "pdf_scroll_area", None)
            if scroll_area:
                delta = event.position() - self._hand_drag_start
                hbar = scroll_area.horizontalScrollBar()
                vbar = scroll_area.verticalScrollBar()
                hbar.setValue(int(self._hand_scroll_start.x() - delta.x()))
                vbar.setValue(int(self._hand_scroll_start.y() - delta.y()))
            event.accept()
            return
        if self._stroke_drag_active and self.main_window.current_tool == "select" and event.buttons() & Qt.MouseButton.LeftButton:
            self._update_stroke_drag(event.position())
            self.update()
            return
        if self.drawing and self.main_window.current_tool in ["pen", "marker"]:
            if self.pixmap() and self.pixmap().rect().contains(event.pos()):
                self.current_path.lineTo(QPointF(event.pos()))
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._hand_drag_active:
            if self._hand_drag_start is not None:
                self._handle_hand_page_turn(event.position() - self._hand_drag_start)
            self._hand_drag_active = False
            if self.main_window.current_tool == "hand":
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._stroke_drag_active:
            self._end_stroke_drag()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if not self.current_path.isEmpty():
                page = self.main_window.current_page
                if page not in self.main_window.annotations:
                    self.main_window.annotations[page] = []

                tool_type = self.main_window.current_tool
                color = self.main_window.pen_color if tool_type == "pen" else self.main_window.marker_color
                width = self.main_window.pen_width if tool_type == "pen" else self.main_window.marker_width

                self.main_window.annotations[page].append({
                    "type": tool_type,
                    "path": QPainterPath(self.current_path),
                    "color": QColor(color),
                    "width": width
                })
            self.current_path = QPainterPath()
            self.update()
            self.main_window.register_snapshot()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap():
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        page = self.main_window.current_page
        if page in self.main_window.annotations:
            for index, item in enumerate(self.main_window.annotations[page]):
                if self.main_window.is_stroke_selected(page, index):
                    highlight_pen = QPen(QColor("#ff9800"))
                    highlight_pen.setWidth(item["width"] + 6)
                    highlight_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    highlight_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                    highlight_pen.setStyle(Qt.PenStyle.SolidLine)
                    painter.setPen(highlight_pen)
                    painter.drawPath(item["path"])
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

    def _find_annotation_at(self, page, point):
        annotations = self.main_window.annotations.get(page, [])
        if not annotations:
            return None

        stroker = QPainterPathStroker()
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        for index in reversed(range(len(annotations))):
            item = annotations[index]
            stroker.setWidth(max(item["width"], 6))
            hit_path = stroker.createStroke(item["path"])
            if hit_path.contains(point):
                return index, item
        return None

    def _show_annotation_menu(self, pos, page, index, item):
        menu = QMenu(self)
        if item["type"] == "marker":
            options = self.main_window.marker_palette
        else:
            options = self.main_window.pen_palette

        current_color = item["color"]
        for label, color in options:
            action = menu.addAction(label)
            action.setData(QColor(color))
            action.setCheckable(True)
            if self._colors_match(current_color, color):
                action.setChecked(True)

        menu.addSeparator()
        delete_action = menu.addAction("削除")
        delete_action.setData("delete")

        selected_action = menu.exec(self.mapToGlobal(pos))
        if not selected_action:
            return

        data = selected_action.data()
        if isinstance(data, QColor):
            self.main_window.annotations[page][index]["color"] = QColor(data)
            if item["type"] == "marker":
                self.main_window.marker_color = QColor(data)
            else:
                self.main_window.pen_color = QColor(data)
            self.update()
            self.main_window.register_snapshot()
        elif data == "delete":
            if self.main_window.is_stroke_selected(page, index):
                self.main_window.clear_selection()
            del self.main_window.annotations[page][index]
            if not self.main_window.annotations[page]:
                del self.main_window.annotations[page]
            self.update()
            self.main_window.register_snapshot()

    @staticmethod
    def _colors_match(color_a, color_b):
        qa = QColor(color_a)
        qb = QColor(color_b)
        return qa.red() == qb.red() and qa.green() == qb.green() and qa.blue() == qb.blue()

    def _create_text_annotation(self, pos):
        page = self.main_window.current_page
        color = self.main_window.get_text_color()
        font_point = self.main_window.get_text_point_size()

        widget = TextAnnotationWidget(self, color, font_point)
        widget.delete_requested.connect(lambda w, p=page: self._handle_text_delete(p, w))
        widget.adjustSize()
        top_left = self._clamp_to_label(pos, widget.size())
        widget.move(top_left)
        widget.show()
        widget.raise_()
        QTimer.singleShot(0, widget.focus_text)

        annotations = self.main_window.text_annotations.setdefault(page, [])
        annotations.append(widget)
        self.main_window.select_text_annotation(widget)
        self.main_window.register_snapshot()

    def _handle_text_delete(self, page, widget):
        self.main_window.remove_text_annotation(page, widget)

    def _clamp_to_label(self, pos, size):
        x = pos.x()
        y = pos.y()
        width = size.width()
        height = size.height()

        max_x = max(0, self.width() - width)
        max_y = max(0, self.height() - height)
        clamped_x = max(0, min(x, max_x))
        clamped_y = max(0, min(y, max_y))
        return QPoint(clamped_x, clamped_y)

    def add_shape_annotation(self, shape_type):
        if not self.pixmap():
            return
        page = self.main_window.current_page
        default_size = QSize(160, 160)

        widget = ShapeAnnotationWidget(self, shape_type, default_size)
        widget.delete_requested.connect(lambda w, p=page: self._handle_shape_delete(p, w))

        center = self.rect().center()
        top_left = QPoint(int(center.x() - widget.width() / 2), int(center.y() - widget.height() / 2))
        top_left = self._clamp_to_label(top_left, widget.size())
        widget.move(top_left)
        widget.show()
        widget.raise_()
        widget.setFocus()

        annotations = self.main_window.shape_annotations.setdefault(page, [])
        annotations.append(widget)
        self.main_window.select_shape_annotation(widget)
        self.main_window.register_snapshot()

    def _handle_shape_delete(self, page, widget):
        self.main_window.remove_shape_annotation(page, widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._clamp_all_annotations()

    def _clamp_all_annotations(self):
        for widgets in self.main_window.text_annotations.values():
            for widget in widgets:
                new_pos = self._clamp_to_label(widget.pos(), widget.size())
                if widget.pos() != new_pos:
                    widget.move(new_pos)
        for widgets in self.main_window.shape_annotations.values():
            for widget in widgets:
                new_pos = self._clamp_to_label(widget.pos(), widget.size())
                if widget.pos() != new_pos:
                    widget.move(new_pos)

    def cancel_selection_drag(self):
        self._stroke_drag_active = False
        self._stroke_original_path = None
        self._stroke_drag_page = None
        self._stroke_drag_index = None

    def cancel_hand_drag(self):
        if self._hand_drag_active:
            self._hand_drag_active = False
        if self.main_window.current_tool == "hand":
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._hand_drag_start = QPointF()
        self._hand_scroll_start = QPoint()

    def _handle_hand_page_turn(self, delta):
        if not self.main_window or not self.main_window.pdf_scroll_area:
            return
        scroll_area = self.main_window.pdf_scroll_area
        horizontal_mode = self.main_window.scroll_toggle_action.isChecked()
        threshold = max(120, (self.width() if horizontal_mode else self.height()) * 0.25)

        if horizontal_mode:
            if abs(delta.x()) < threshold:
                return
            hbar = scroll_area.horizontalScrollBar()
            if delta.x() > 0 and hbar.value() <= hbar.minimum():
                self.main_window.show_prev_page()
            elif delta.x() < 0 and hbar.value() >= hbar.maximum():
                self.main_window.show_next_page()
        else:
            if abs(delta.y()) < threshold:
                return
            vbar = scroll_area.verticalScrollBar()
            if delta.y() > 0 and vbar.value() <= vbar.minimum():
                self.main_window.show_prev_page()
            elif delta.y() < 0 and vbar.value() >= vbar.maximum():
                self.main_window.show_next_page()

    def _begin_stroke_drag(self, page, index, pos):
        annotations = self.main_window.annotations.get(page)
        if not annotations or index >= len(annotations):
            return
        self._stroke_drag_active = True
        self._stroke_drag_page = page
        self._stroke_drag_index = index
        self._stroke_drag_start = QPointF(pos)
        self._stroke_original_path = QPainterPath(annotations[index]["path"])

    def _update_stroke_drag(self, pos):
        if not self._stroke_drag_active:
            return
        annotations = self.main_window.annotations.get(self._stroke_drag_page)
        if not annotations or self._stroke_drag_index >= len(annotations):
            self.cancel_selection_drag()
            return
        delta_x = pos.x() - self._stroke_drag_start.x()
        delta_y = pos.y() - self._stroke_drag_start.y()
        new_path = QPainterPath(self._stroke_original_path)
        new_path.translate(delta_x, delta_y)
        annotations[self._stroke_drag_index]["path"] = new_path

    def _end_stroke_drag(self):
        self.cancel_selection_drag()
        self.main_window.register_snapshot()


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


class AnswerGridEditor(QTextEdit):
    """司法試験用の答案入力テキストエディタ。"""

    cellMetricsChanged = pyqtSignal()
    resized = pyqtSignal()

    def __init__(self, parent=None, columns=30, rows=23):
        super().__init__(parent)
        self.max_chars = columns
        self.max_lines = rows
        self._internal_change = False
        self._scale = 1.0

        # 全角文字用のフォント設定（画像と同じサイズに調整）
        base_font = QFont("Hiragino Mincho ProN", 30)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("MS Mincho", 30)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("Arial Unicode MS", 30)
        self._base_font = QFont(base_font)
        self._base_point_size = self._base_font.pointSizeF() or float(self._base_font.pointSize() or 30)
        self.setFont(self._base_font)

        # テキストエディタ設定
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setUndoRedoEnabled(True)
        
        # 適切なサイズ設定
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # スタイル設定
        self.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #ddd;
                padding: 20px 20px 20px 120px;
                line-height: 2.0;
                font-family: 'Hiragino Mincho ProN', 'MS Mincho', serif;
                font-size: 30pt;
                color: black;
                letter-spacing: 0.1em;
            }
            QTextEdit:focus {
                border: 2px solid #007acc;
            }
        """)

        self.textChanged.connect(self.enforce_limits)

    def keyPressEvent(self, event):
        # エンターキーで改行
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            cursor = self.textCursor()
            cursor.insertText('\n')
            self.setTextCursor(cursor)
            return
        
        # 半角スペースを全角スペースに変換
        if event.text() == ' ':
            cursor = self.textCursor()
            cursor.insertText('　')
            self.setTextCursor(cursor)
            return
        
        # 英数入力モードの場合はアルファベットと数字をそのまま入力
        if event.text() and (event.text().isalnum() or event.text() in '.,!?;:'):
            super().keyPressEvent(event)
            return
        
        # 通常のキー入力はそのまま処理（日本語変換を妨げない）
        super().keyPressEvent(event)
    
    def _convert_to_fullwidth(self, text):
        """半角アルファベットを全角に変換"""
        result = ""
        for char in text:
            if 'a' <= char <= 'z':
                result += chr(ord('ａ') + (ord(char) - ord('a')))
            elif 'A' <= char <= 'Z':
                result += chr(ord('Ａ') + (ord(char) - ord('A')))
            else:
                result += char
        return result
    
    def _convert_digits_to_fullwidth(self, text):
        """半角数字を全角に変換"""
        result = ""
        for char in text:
            if '0' <= char <= '9':
                result += chr(ord('０') + (ord(char) - ord('0')))
            else:
                result += char
        return result

    def base_size(self):
        return QSize(600, 400)

    def total_size(self):
        return self.size()

    def cell_size(self):
        return QSize(20, 20)

    def enforce_limits(self):
        if self._internal_change:
            return
        # 文字数制限のチェック
        text = self.toPlainText()
        if len(text) > self.max_chars * self.max_lines:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self.setTextCursor(cursor)

    def set_display_scale(self, scale):
        scale = max(scale, 0.25)
        if abs(scale - self._scale) < 1e-4:
            return
        self._scale = scale
        font = QFont(self._base_font)
        if self._base_point_size > 0:
            font.setPointSizeF(self._base_point_size * scale)
        self.setFont(font)

    def insertFromMimeData(self, source):
        text = source.text()
        if text:
            # 半角スペースのみ全角に変換、アルファベットと数字はそのまま
            normalized = text.replace(' ', '　')
            cursor = self.textCursor()
            cursor.insertText(normalized)
            return
        super().insertFromMimeData(source)
    
    def _normalize_text(self, text):
        """テキストを全角に正規化"""
        result = ""
        for char in text:
            if char == ' ':
                result += '　'
            elif 'a' <= char <= 'z':
                result += chr(ord('ａ') + (ord(char) - ord('a')))
            elif 'A' <= char <= 'Z':
                result += chr(ord('Ａ') + (ord(char) - ord('A')))
            elif '0' <= char <= '9':
                result += chr(ord('０') + (ord(char) - ord('0')))
            else:
                result += char
        return result

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()
        # 親ウィジェットの背景も更新
        if self.parent():
            self.parent().update()


class AnswerGridBackground(QWidget):
    """答案エディタの背後に原稿用紙風の罫線を描画するウィジェット。"""

    def __init__(self, editor: AnswerGridEditor, parent=None):
        super().__init__(parent)
        self._editor = editor
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._editor.cellMetricsChanged.connect(self._sync_with_editor)
        self._sync_with_editor()

    def _sync_with_editor(self):
        size = self._editor.total_size()
        self.setMinimumSize(size)
        self.setMaximumSize(size)
        self.resize(size)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        if not self._editor:
            return

        # 行の高さを計算（フォントメトリクスから）
        font_metrics = QFontMetrics(self._editor.font())
        line_height = font_metrics.height()
        ascent = font_metrics.ascent()
        
        if line_height <= 0:
            return

        rect = self.rect()
        x_start = rect.x() + 15  # パディングを考慮
        y_start = rect.y() + 15  # パディングを考慮
        x_end = rect.right() - 15
        y_end = rect.bottom() - 15

        # 行番号エリアの幅
        line_number_width = 50

        # 行番号エリアの背景を描画
        painter.fillRect(x_start, y_start, line_number_width, y_end - y_start, QColor(248, 248, 248))
        
        # 行番号エリアの右端に線を描画
        pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(pen)
        painter.drawLine(x_start + line_number_width, y_start, x_start + line_number_width, y_end)

        # 行ごとの水平線を描画
        pen = QPen(QColor(220, 220, 220), 1)
        painter.setPen(pen)
        
        y = y_start + line_height
        line_number = 1
        while y <= y_end:
            # 水平線を描画
            painter.drawLine(x_start + line_number_width + 5, y, x_end, y)
            
            # 行番号を描画
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawText(x_start + 5, y - ascent + line_height, f"頁1 {line_number}")
            
            # 次の行に移動
            y += line_height
            line_number += 1




class AnswerSheetPageWidget(QWidget):
    """司法試験用の答案入力ページ。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = AnswerGridEditor(self)

        # レイアウト設定
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.editor)

        # 描画を有効化するための属性設定
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        # エディタの背景を透明にして、親の描画が見えるようにする
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: 2px solid #ddd;
                padding: 20px 20px 20px 120px;
                line-height: 2.0;
                font-family: 'Hiragino Mincho ProN', 'MS Mincho', serif;
                font-size: 30pt;
                color: black;
                letter-spacing: 0.1em;
            }
            QTextEdit:focus {
                border: 2px solid #007acc;
            }
        """)

        self.setFocusProxy(self.editor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 初期描画を強制
        self.update()

        self._scale = 1.0

    def paintEvent(self, event):
        # 背景を描画
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # 全体の背景を白で塗りつぶし
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # エディタの位置とサイズを取得
        editor_rect = self.editor.geometry()

        # 行の高さを計算
        font_metrics = QFontMetrics(self.editor.font())
        line_height = font_metrics.height()
        ascent = font_metrics.ascent()
        
        if line_height <= 0:
            return

        # 行番号エリアの幅を大きくする
        line_number_width = 100

        # 行番号エリアの背景を描画
        line_number_rect = QRect(editor_rect.x() + 20, editor_rect.y() + 20, 
                                line_number_width, editor_rect.height() - 40)
        painter.fillRect(line_number_rect, QColor(248, 248, 248))
        
        # 行番号エリアの右端に線を描画
        pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(pen)
        painter.drawLine(line_number_rect.right(), line_number_rect.top(), 
                        line_number_rect.right(), line_number_rect.bottom())

        # QTextEditの実際の行の位置を取得して描画
        document = self.editor.document()
        block_count = document.blockCount()
        
        # 行ごとの水平線を描画
        pen = QPen(QColor(220, 220, 220), 1)
        painter.setPen(pen)
        
        for i in range(block_count):
            block = document.findBlockByNumber(i)
            if block.isValid():
                # ブロックの位置を取得（正しいメソッド呼び出し）
                block_rect = self.editor.document().documentLayout().blockBoundingRect(block)
                # エディタ内での実際の位置を計算
                y = int(editor_rect.y() + 20 + block_rect.y() + ascent)
                
                # 水平線を描画
                painter.drawLine(line_number_rect.right() + 10, y, 
                               editor_rect.right() - 20, y)
                
                # 行番号を描画
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawText(line_number_rect.x() + 10, y, str(i + 1))
                painter.setPen(QPen(QColor(220, 220, 220), 1))

    def base_size(self):
        return QSize(600, 400)

    def current_size(self):
        return self.size()

    def set_scale(self, scale):
        scale = max(scale, 0.25)
        if abs(scale - self._scale) < 1e-4:
            return
        self._scale = scale
        self.editor.set_display_scale(scale)

    def sync_editor_size(self):
        pass

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

class AnswerSheet(QWidget):
    contentChanged = pyqtSignal()
    TOTAL_PAGES = 8

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

        self.main_window = getattr(parent, 'main_window', None)

        self.page_stack = QStackedWidget()
        self.pages = []
        self.page_widgets = []
        for _ in range(self.TOTAL_PAGES):
            page_widget = AnswerSheetPageWidget(self)
            page_widget.main_window = None
            self.page_stack.addWidget(page_widget)
            self.pages.append(page_widget.editor)
            self.page_widgets.append(page_widget)
            page_widget.editor.textChanged.connect(self._handle_page_text_changed)

        self.page_scroll = QScrollArea()
        self.page_scroll.setWidgetResizable(False)
        self.page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.page_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.page_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.page_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.page_scroll.setWidget(self.page_stack)
        self.page_scroll.viewport().installEventFilter(self)

        self._scale = 1.0
        self._base_page_size = self.page_widgets[0].base_size() if self.page_widgets else QSize(1, 1)
        self._apply_scale(self._scale)

        nav_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("前の頁")
        self.next_page_button = QPushButton("次の頁")
        self.page_indicator = QLabel("1 / 8")
        nav_layout.addWidget(self.prev_page_button)
        nav_layout.addWidget(self.page_indicator)
        nav_layout.addWidget(self.next_page_button)
        nav_layout.addStretch()

        layout.addLayout(info_bar)
        layout.addWidget(self.search_replace_bar)
        layout.addWidget(self.page_scroll)
        layout.addLayout(nav_layout)

        self.prev_page_button.clicked.connect(self.go_prev_page)
        self.next_page_button.clicked.connect(self.go_next_page)
        self.current_page_index = 0
        self.update_page_controls()
        self.update_status_label()
        QTimer.singleShot(0, self._update_scale)

    def _handle_page_text_changed(self):
        editor = self.sender()
        if hasattr(editor, '_internal_change') and editor._internal_change:
            return
        self.update_status_label()
        self.contentChanged.emit()

    def _apply_scale(self, scale):
        if not self.page_widgets:
            return
        self._scale = scale
        for widget in self.page_widgets:
            widget.set_scale(scale)
        size = self.page_widgets[0].current_size()
        target_height = size.height()
        target_width = size.width()
        self.page_stack.setMinimumSize(QSize(0, 0))
        self.page_stack.setMaximumHeight(target_height)
        self.page_stack.setMaximumWidth(QWIDGETSIZE_MAX)
        self.page_stack.resize(target_width, target_height)
        self.page_stack.updateGeometry()

    def _update_scale(self):
        if not self.page_widgets:
            return
        viewport = self.page_scroll.viewport() if hasattr(self, 'page_scroll') else None
        if not viewport:
            return
        base_width = max(1, self._base_page_size.width())
        width = viewport.width()
        if width <= 0:
            return
        scale = max(1.0, width / base_width)
        if abs(scale - self._scale) > 1e-3:
            self._apply_scale(scale)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scale()

    def eventFilter(self, obj, event):
        if hasattr(self, 'page_scroll') and obj is self.page_scroll.viewport():
            if event.type() == QEvent.Type.Resize:
                self._update_scale()
        return super().eventFilter(obj, event)

    def set_main_window(self, main_window):
        self.main_window = main_window
        for widget in getattr(self, 'page_widgets', []):
            widget.main_window = main_window

    def current_editor(self):
        return self.pages[self.current_page_index]

    def go_prev_page(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.page_stack.setCurrentIndex(self.current_page_index)
            self.update_page_controls()
            self.contentChanged.emit()

    def go_next_page(self):
        if self.current_page_index < self.TOTAL_PAGES - 1:
            self.current_page_index += 1
            self.page_stack.setCurrentIndex(self.current_page_index)
            self.update_page_controls()
            self.contentChanged.emit()

    def update_page_controls(self):
        self.page_indicator.setText(f"{self.current_page_index + 1} / {self.TOTAL_PAGES}")
        self.prev_page_button.setEnabled(self.current_page_index > 0)
        self.next_page_button.setEnabled(self.current_page_index < self.TOTAL_PAGES - 1)

    def set_current_page(self, index):
        index = max(0, min(index, self.TOTAL_PAGES - 1))
        self.current_page_index = index
        self.page_stack.setCurrentIndex(index)
        self.update_page_controls()

    def undo_current(self):
        self.current_editor().undo()

    def redo_current(self):
        self.current_editor().redo()

    def total_character_count(self):
        limit = self.TOTAL_PAGES * self.pages[0].max_chars * self.pages[0].max_lines
        total_chars = 0
        for editor in self.pages:
            text = editor.toPlainText()
            lines = text.split('\n')
            if text.endswith('\n'):
                lines.append('')
            for line in lines[:editor.max_lines]:
                total_chars += len(line)
        return min(total_chars, limit)

    def total_line_count(self):
        total = 0
        for editor in self.pages:
            text = editor.toPlainText()
            if not text:
                continue
            lines = text.split('\n')
            if text.endswith('\n'):
                lines.append('')
            total += min(len(lines), editor.max_lines)
        return min(total, self.TOTAL_PAGES * self.pages[0].max_lines)

    def update_status_label(self):
        total_lines = self.total_line_count()
        total_chars = self.total_character_count()
        max_lines = self.TOTAL_PAGES * self.pages[0].max_lines
        max_chars = self.TOTAL_PAGES * self.pages[0].max_chars * self.pages[0].max_lines
        self.char_count_label.setText(f"{total_lines}/{max_lines}行 {total_chars}/{max_chars}文字 (空白含む)")

    def get_page_texts(self):
        return [editor.toPlainText() for editor in self.pages]

    def set_page_texts(self, texts):
        for index, editor in enumerate(self.pages):
            text = texts[index] if index < len(texts) else ""
            editor._internal_change = True
            editor.setPlainText(text)
            editor._internal_change = False
        self.update_status_label()
        self.update_page_controls()
        self.contentChanged.emit()

    def forward_overflow(self, source_editor, overflow_text):
        try:
            start_index = self.pages.index(source_editor)
        except ValueError:
            return
        next_index = start_index + 1
        overflow_text = overflow_text.lstrip('\n')
        while overflow_text and next_index < self.TOTAL_PAGES:
            editor = self.pages[next_index]
            existing = editor.toPlainText()
            if existing:
                combined_text = overflow_text.rstrip('\n')
                if combined_text and not combined_text.endswith('\n'):
                    combined_text += '\n'
                combined_text += existing
            else:
                combined_text = overflow_text

            lines = editor._split_lines(combined_text)
            retained_lines = lines[:editor.max_lines]
            overflow_lines = lines[editor.max_lines:]
            retained = '\n'.join(retained_lines)
            overflow_text = '\n'.join(overflow_lines)
            editor._internal_change = True
            editor.setPlainText(retained)
            editor._internal_change = False
            editor._check_overflow()
            next_index += 1
        self.update_status_label()
        self.contentChanged.emit()

    def pull_from_next(self, source_editor):
        try:
            start_index = self.pages.index(source_editor)
        except ValueError:
            return
        lines = source_editor._split_lines(source_editor.toPlainText())
        if len(lines) >= source_editor.max_lines:
            return
        needed = source_editor.max_lines - len(lines)
        next_index = start_index + 1
        while needed > 0 and next_index < self.TOTAL_PAGES:
            editor = self.pages[next_index]
            next_text = editor.toPlainText()
            if not next_text:
                next_index += 1
                continue
            next_lines = editor._split_lines(next_text)
            take_lines = next_lines[:needed]
            remaining_lines = next_lines[needed:]
            lines.extend(take_lines)
            editor._internal_change = True
            editor.setPlainText('\n'.join(remaining_lines))
            editor._internal_change = False
            editor._check_overflow()
            needed = source_editor.max_lines - len(lines)
            next_index += 1
        source_editor._internal_change = True
        source_editor.setPlainText('\n'.join(lines))
        source_editor._internal_change = False
        source_editor._check_overflow()
        self.update_status_label()
        self.contentChanged.emit()
