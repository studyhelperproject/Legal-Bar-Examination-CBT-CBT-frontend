from PyQt6.QtCore import Qt, QPointF, QEvent, QPoint, QSize, QRect, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QPainterPathStroker
from PyQt6.QtWidgets import QLabel, QMenu

from .annotations import TextAnnotationWidget, ShapeAnnotationWidget


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
