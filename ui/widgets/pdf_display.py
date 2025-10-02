from PyQt6.QtCore import Qt, QPointF, QEvent, QPoint, QSize, QRect, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QPainterPathStroker
from PyQt6.QtWidgets import QLabel, QMenu

from .text_annotation import TextAnnotationWidget
from .shape_annotation import ShapeAnnotationWidget


class PDFDisplayLabel(QLabel):
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
        if not self.main_window: return super().mousePressEvent(event)

        button = event.button()
        tool = self.main_window.annotation_handler.current_tool

        if button == Qt.MouseButton.LeftButton and tool == "hand":
            scroll_area = getattr(self.main_window, "pdf_scroll_area", None)
            if scroll_area:
                self._hand_drag_active = True
                self._hand_drag_start = event.position()
                self._hand_scroll_start = QPoint(scroll_area.horizontalScrollBar().value(), scroll_area.verticalScrollBar().value())
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return

        if button == Qt.MouseButton.LeftButton and tool == "text":
            if self.pixmap() and self.pixmap().rect().contains(event.pos()):
                self._create_text_annotation(event.pos())
                event.accept()
                return

        if self.pixmap() and self.pixmap().rect().contains(event.pos()):
            page = self.main_window.pdf_handler.current_page
            hit = self._find_annotation_at(page, QPointF(event.pos()))

            if hit is not None:
                index, item = hit
                if tool == "select" and button == Qt.MouseButton.LeftButton:
                    self.main_window.annotation_handler.select_stroke_annotation(page, index)
                    self._begin_stroke_drag(page, index, event.position())
                else:
                    self._show_annotation_menu(event.pos(), page, index, item)
                event.accept()
                return

            if button == Qt.MouseButton.LeftButton and tool in ["pen", "marker"]:
                self.drawing = True
                self.current_path = QPainterPath(event.position())
                event.accept()
                return

        if tool == "select" and button == Qt.MouseButton.LeftButton:
            self.main_window.annotation_handler.clear_selection()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.main_window: return super().mouseMoveEvent(event)
        tool = self.main_window.annotation_handler.current_tool

        if self._hand_drag_active and tool == "hand":
            scroll_area = getattr(self.main_window, "pdf_scroll_area", None)
            if scroll_area:
                delta = event.position() - self._hand_drag_start
                scroll_area.horizontalScrollBar().setValue(int(self._hand_scroll_start.x() - delta.x()))
                scroll_area.verticalScrollBar().setValue(int(self._hand_scroll_start.y() - delta.y()))
            event.accept()
            return

        if self._stroke_drag_active and tool == "select" and event.buttons() & Qt.MouseButton.LeftButton:
            self._update_stroke_drag(event.position())
            self.update()
            return

        if self.drawing and tool in ["pen", "marker"]:
            if self.pixmap() and self.pixmap().rect().contains(event.pos()):
                self.current_path.lineTo(event.position())
                self.update()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.main_window: return super().mouseReleaseEvent(event)
        button = event.button()
        tool = self.main_window.annotation_handler.current_tool

        if button == Qt.MouseButton.LeftButton and self._hand_drag_active:
            if self._hand_drag_start is not None:
                self._handle_hand_page_turn(event.position() - self._hand_drag_start)
            self.cancel_hand_drag()
            event.accept()
            return

        if button == Qt.MouseButton.LeftButton and self._stroke_drag_active:
            self._end_stroke_drag()
            event.accept()
            return

        if button == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if not self.current_path.isEmpty():
                page = self.main_window.pdf_handler.current_page
                annotations = self.main_window.annotation_handler.annotations.setdefault(page, [])

                color = self.main_window.annotation_handler.pen_color if tool == "pen" else self.main_window.annotation_handler.marker_color
                width = self.main_window.annotation_handler.pen_width if tool == "pen" else self.main_window.annotation_handler.marker_width

                annotations.append({"type": tool, "path": self.current_path, "color": color, "width": width})
                self.main_window.history_handler.register_snapshot()

            self.current_path = QPainterPath()
            self.update()
            return

        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap() or not self.main_window: return

        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        page = self.main_window.pdf_handler.current_page

        if page in self.main_window.annotation_handler.annotations:
            for index, item in enumerate(self.main_window.annotation_handler.annotations[page]):
                if self.main_window.annotation_handler.is_stroke_selected(page, index):
                    highlight_pen = QPen(QColor("#ff9800"), item["width"] + 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(highlight_pen); painter.drawPath(item["path"])

                pen_color = item["color"]
                if item["type"] == "marker":
                    pen_color = QColor(pen_color.red(), pen_color.green(), pen_color.blue(), 128)

                pen = QPen(pen_color, item["width"], Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen); painter.drawPath(item["path"])

        if self.drawing:
            tool = self.main_window.annotation_handler.current_tool
            color = self.main_window.annotation_handler.pen_color if tool == "pen" else self.main_window.annotation_handler.marker_color
            width = self.main_window.annotation_handler.pen_width if tool == "pen" else self.main_window.annotation_handler.marker_width
            if tool == "marker": color = QColor(color.red(), color.green(), color.blue(), 128)
            painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(self.current_path)

    def _find_annotation_at(self, page, point):
        annotations = self.main_window.annotation_handler.annotations.get(page, [])
        stroker = QPainterPathStroker(); stroker.setCapStyle(Qt.PenCapStyle.RoundCap); stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        for index, item in reversed(list(enumerate(annotations))):
            stroker.setWidth(max(item["width"], 10))
            if stroker.createStroke(item["path"]).contains(point):
                return index, item
        return None

    def _show_annotation_menu(self, pos, page, index, item):
        menu = QMenu(self)
        options = self.main_window.annotation_handler.marker_palette if item["type"] == "marker" else self.main_window.annotation_handler.pen_palette
        for label, color in options:
            action = menu.addAction(label); action.setData(color); action.setCheckable(True)
            if self._colors_match(item["color"], color): action.setChecked(True)

        menu.addSeparator(); delete_action = menu.addAction("削除"); delete_action.setData("delete")

        selected = menu.exec(self.mapToGlobal(pos))
        if not selected: return

        data = selected.data()
        handler = self.main_window.annotation_handler
        if isinstance(data, QColor):
            handler.annotations[page][index]["color"] = data
            if item["type"] == "marker": handler.marker_color = data
            else: handler.pen_color = data
        elif data == "delete":
            if handler.is_stroke_selected(page, index): handler.clear_selection()
            del handler.annotations[page][index]
            if not handler.annotations[page]: del handler.annotations[page]

        self.update()
        self.main_window.history_handler.register_snapshot()

    def _colors_match(self, c1, c2): return QColor(c1).rgba() == QColor(c2).rgba()

    def _create_text_annotation(self, pos):
        page = self.main_window.pdf_handler.current_page
        handler = self.main_window.annotation_handler
        widget = TextAnnotationWidget(self, handler.get_text_color(), handler.get_text_point_size())
        widget.delete_requested.connect(lambda w, p=page: handler.remove_text_annotation(p, w))
        widget.move(self._clamp_to_label(pos - QPoint(widget.width()//2, widget.height()//2), widget.size()))
        widget.show(); QTimer.singleShot(0, widget.setFocus)
        handler.text_annotations.setdefault(page, []).append(widget)
        handler.select_text_annotation(widget)
        self.main_window.history_handler.register_snapshot()

    def _clamp_to_label(self, pos, size):
        return QPoint(max(0, min(pos.x(), self.width() - size.width())), max(0, min(pos.y(), self.height() - size.height())))

    def add_shape_annotation(self, shape_type):
        if not self.pixmap(): return
        page = self.main_window.pdf_handler.current_page; handler = self.main_window.annotation_handler
        widget = ShapeAnnotationWidget(self, shape_type)
        widget.delete_requested.connect(lambda w, p=page: handler.remove_shape_annotation(p, w))
        center = self.rect().center() - QPoint(widget.width()//2, widget.height()//2)
        widget.move(self._clamp_to_label(center, widget.size())); widget.show(); widget.setFocus()
        handler.shape_annotations.setdefault(page, []).append(widget)
        handler.select_shape_annotation(widget)
        self.main_window.history_handler.register_snapshot()

    def resizeEvent(self, event):
        super().resizeEvent(event); self._clamp_all_annotations()

    def _clamp_all_annotations(self):
        if not hasattr(self.main_window, 'annotation_handler'): return
        handler = self.main_window.annotation_handler
        for widgets in list(handler.text_annotations.values()) + list(handler.shape_annotations.values()):
            for widget in widgets:
                widget.move(self._clamp_to_label(widget.pos(), widget.size()))

    def cancel_selection_drag(self):
        self._stroke_drag_active = False

    def cancel_hand_drag(self):
        self._hand_drag_active = False
        if self.main_window and self.main_window.annotation_handler.current_tool == "hand":
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def _handle_hand_page_turn(self, delta):
        if not self.main_window: return
        horizontal = self.main_window.scroll_toggle_action.isChecked()
        threshold = (self.width() if horizontal else self.height()) * 0.25
        scroll_bar = self.main_window.pdf_scroll_area.horizontalScrollBar() if horizontal else self.main_window.pdf_scroll_area.verticalScrollBar()

        if (delta.x() if horizontal else delta.y()) > threshold and scroll_bar.value() == scroll_bar.minimum():
            self.main_window.pdf_handler.show_prev_page()
        elif (delta.x() if horizontal else delta.y()) < -threshold and scroll_bar.value() == scroll_bar.maximum():
            self.main_window.pdf_handler.show_next_page()

    def _begin_stroke_drag(self, page, index, pos):
        item = self.main_window.annotation_handler.annotations.get(page, [])[index]
        self._stroke_drag_active = True; self._stroke_drag_page = page
        self._stroke_drag_index = index; self._stroke_drag_start = pos
        self._stroke_original_path = QPainterPath(item["path"])

    def _update_stroke_drag(self, pos):
        if not self._stroke_drag_active: return
        delta = pos - self._stroke_drag_start
        new_path = QPainterPath(self._stroke_original_path); new_path.translate(delta)
        self.main_window.annotation_handler.annotations[self._stroke_drag_page][self._stroke_drag_index]["path"] = new_path

    def _end_stroke_drag(self):
        if self._stroke_drag_active:
            self.cancel_selection_drag()
            self.main_window.history_handler.register_snapshot()