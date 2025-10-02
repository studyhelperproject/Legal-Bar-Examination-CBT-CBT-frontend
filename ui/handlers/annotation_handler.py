from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Tuple, Optional, Any

from PyQt6.QtGui import QColor, QPainterPath, QAction
from PyQt6.QtCore import QPointF, QSize, Qt
from ui.widgets.text_annotation import TextAnnotationWidget
from ui.widgets.shape_annotation import ShapeAnnotationWidget

if TYPE_CHECKING:
    from ..main_window import MainWindow

class AnnotationHandler:
    """
    PDFビューア上の注釈（ペン、マーカー、テキスト、図形）の管理を行うハンドラクラス。

    ツールの状態管理、注釈の作成・選択・削除、表示制御、シリアライズ/デシリアライズなど、
    注釈に関するすべてのロジックをカプセル化します。
    """
    def __init__(self, main_window: MainWindow) -> None:
        """
        AnnotationHandlerのコンストラクタ。

        Args:
            main_window (MainWindow): 親となるメインウィンドウインスタンス。
        """
        self.main: MainWindow = main_window

        # --- カラーパレットとスタイルの定義 ---
        self.marker_palette: List[Tuple[str, QColor]] = [
            ("黄", QColor("#fff176")), ("橙", QColor("#ffb74d")),
            ("緑", QColor("#aed581")), ("青", QColor("#64b5f6")),
            ("赤", QColor("#e57373")),
        ]
        self.pen_palette: List[Tuple[str, QColor]] = [
            ("黒", QColor("black")), ("赤", QColor("#d32f2f")), ("青", QColor("#1976d2")),
        ]
        self.text_palette: List[Tuple[str, QColor]] = [(label, QColor(color)) for label, color in self.marker_palette]
        self.text_sizes: Dict[str, int] = {"small": 12, "medium": 16, "large": 20}

        # --- 現在のツール状態 ---
        self.current_tool: str = "select"
        self.pen_color: QColor = QColor(self.pen_palette[0][1])
        self.pen_width: int = 2
        self.marker_color: QColor = QColor(self.marker_palette[0][1])
        self.marker_width: int = 10
        self.text_size_key: str = "medium"
        self.text_color: QColor = QColor(self.text_palette[0][1])

        # --- 注釈データストレージ ---
        self.annotations: Dict[int, List[Dict[str, Any]]] = {}  # Strokes (pen, marker)
        self.text_annotations: Dict[int, List[TextAnnotationWidget]] = {}
        self.shape_annotations: Dict[int, List[ShapeAnnotationWidget]] = {}
        self.selected_annotation: Optional[Dict[str, Any]] = None

    def on_tool_selected(self, action: QAction) -> None:
        """ツールバーで選択されたツールに応じて状態を更新する。"""
        tool_map = {
            self.main.pen_action: "pen",
            self.main.marker_action: "marker",
            self.main.text_action: "text",
            self.main.hand_action: "hand",
            self.main.select_action: "select",
        }
        self.current_tool = tool_map.get(action, "select")

        self.main.text_tool_panel.setVisible(self.current_tool == "text")

        cursor_map = {
            "text": Qt.CursorShape.IBeamCursor,
            "pen": Qt.CursorShape.CrossCursor,
            "marker": Qt.CursorShape.CrossCursor,
            "hand": Qt.CursorShape.OpenHandCursor,
        }
        cursor_shape = cursor_map.get(self.current_tool, Qt.CursorShape.ArrowCursor)
        self.main.pdf_display_label.setCursor(cursor_shape)

        if self.current_tool != "hand":
            self.main.pdf_display_label.cancel_hand_drag()

    def update_text_style_from_controls(self) -> None:
        """UIコントロールからテキストのスタイル（サイズ、色）を更新する。"""
        size_key = self.main.text_size_combo.currentData()
        if size_key in self.text_sizes:
            self.text_size_key = size_key

        color_data = self.main.text_color_combo.currentData()
        if isinstance(color_data, QColor):
            self.text_color = QColor(color_data)

        focus_widget = self.main.focusWidget()
        if isinstance(focus_widget, (TextAnnotationWidget, ShapeAnnotationWidget)):
            focus_widget.set_text_style(self.text_color, self.get_text_point_size())
            if not self.main.history_handler.is_restoring():
                self.main.history_handler.register_snapshot()

    def get_text_point_size(self) -> int:
        """現在のテキストサイズのポイント数を返す。"""
        return self.text_sizes.get(self.text_size_key, 16)

    def get_text_color(self) -> QColor:
        """現在のテキストカラーを返す。"""
        return QColor(self.text_color)

    def add_shape_annotation(self, shape_type: str) -> None:
        """図形注釈を追加する。"""
        if not self.main.pdf_handler.pdf_document:
            return
        self.main.pdf_display_label.add_shape_annotation(shape_type)

    def clear_selection(self) -> None:
        """現在選択されているすべての注釈の選択を解除する。"""
        if not self.selected_annotation:
            return

        selected = self.selected_annotation
        self.selected_annotation = None
        self.main.pdf_display_label.cancel_selection_drag()

        widget = selected.get('widget')
        if widget:
            try:
                widget.set_selected(False)
                if selected.get('type') == 'shape':
                    widget.clearFocus()
            except RuntimeError:
                pass # Widget might have been deleted

        self.main.pdf_display_label.update()

    def select_stroke_annotation(self, page: int, index: int) -> None:
        """ストローク注釈（ペン、マーカー）を選択する。"""
        self.clear_selection()
        self.selected_annotation = {'type': 'stroke', 'page': page, 'index': index}
        self.main.pdf_display_label.update()

    def select_text_annotation(self, widget: TextAnnotationWidget) -> None:
        """テキスト注釈を選択する。"""
        if not widget: return
        self.clear_selection()
        self.selected_annotation = {'type': 'text', 'page': self.main.pdf_handler.current_page, 'widget': widget}
        widget.set_selected(True)
        widget.raise_()

    def select_shape_annotation(self, widget: ShapeAnnotationWidget) -> None:
        """図形注釈を選択する。"""
        if not widget: return
        self.clear_selection()
        self.selected_annotation = {'type': 'shape', 'page': self.main.pdf_handler.current_page, 'widget': widget}
        widget.set_selected(True)
        widget.setFocus()
        widget.raise_()

    def is_stroke_selected(self, page: int, index: int) -> bool:
        """指定されたストロークが現在選択されているかどうかを返す。"""
        selected = self.selected_annotation
        return (selected is not None and selected.get('type') == 'stroke' and
                selected.get('page') == page and selected.get('index') == index)

    def remove_text_annotation(self, page: int, widget: TextAnnotationWidget) -> None:
        """指定されたテキスト注釈を削除する。"""
        if page in self.text_annotations and widget in self.text_annotations[page]:
            self.text_annotations[page].remove(widget)
            if self.selected_annotation and self.selected_annotation.get('widget') is widget:
                self.clear_selection()
            widget.deleteLater()
            if not self.text_annotations[page]:
                del self.text_annotations[page]
            self.main.pdf_display_label.update()
            if not self.main.history_handler.is_restoring():
                self.main.history_handler.register_snapshot()

    def remove_shape_annotation(self, page: int, widget: ShapeAnnotationWidget) -> None:
        """指定された図形注釈を削除する。"""
        if page in self.shape_annotations and widget in self.shape_annotations[page]:
            self.shape_annotations[page].remove(widget)
            if self.selected_annotation and self.selected_annotation.get('widget') is widget:
                self.clear_selection()
            widget.deleteLater()
            if not self.shape_annotations[page]:
                del self.shape_annotations[page]
            self.main.pdf_display_label.update()
            if not self.main.history_handler.is_restoring():
                self.main.history_handler.register_snapshot()

    def clear_all_annotations(self) -> None:
        """すべての注釈をクリアする。"""
        self.annotations.clear()
        self._clear_text_annotations()
        self._clear_shape_annotations()
        self.main.pdf_display_label.update()

    def _clear_text_annotations(self) -> None:
        """すべてのテキスト注釈ウィジェットを削除・クリアする。"""
        for widgets in self.text_annotations.values():
            for widget in widgets:
                widget.deleteLater()
        self.text_annotations.clear()
        if self.selected_annotation and self.selected_annotation.get('type') == 'text':
            self.clear_selection()

    def _clear_shape_annotations(self) -> None:
        """すべての図形注釈ウィジェットを削除・クリアする。"""
        for widgets in self.shape_annotations.values():
            for widget in widgets:
                widget.deleteLater()
        self.shape_annotations.clear()
        if self.selected_annotation and self.selected_annotation.get('type') == 'shape':
            self.clear_selection()

    def update_annotations_visibility(self) -> None:
        """現在のページに応じて、すべての注釈の可視性を更新する。"""
        self._update_text_annotations_visibility()
        self._update_shape_annotations_visibility()

    def _update_text_annotations_visibility(self) -> None:
        """テキスト注釈の可視性を現在のページに合わせて更新する。"""
        current_page = self.main.pdf_handler.current_page
        for page, widgets in self.text_annotations.items():
            visible = (page == current_page)
            for widget in widgets:
                if not visible and widget.text_edit.hasFocus():
                    widget.text_edit.clearFocus()
                if not visible and self.selected_annotation and self.selected_annotation.get('widget') is widget:
                    self.clear_selection()
                widget.setVisible(visible)
                if visible:
                    widget.raise_()

    def _update_shape_annotations_visibility(self) -> None:
        """図形注釈の可視性を現在のページに合わせて更新する。"""
        current_page = self.main.pdf_handler.current_page
        for page, widgets in self.shape_annotations.items():
            visible = (page == current_page)
            for widget in widgets:
                if not visible and widget.hasFocus():
                    widget.clearFocus()
                if not visible and self.selected_annotation and self.selected_annotation.get('widget') is widget:
                    self.clear_selection()
                widget.setVisible(visible)
                if visible:
                    widget.raise_()

    # --- Serialization ---
    def serialize_all(self) -> Dict[str, Any]:
        """すべての注釈データをシリアライズ可能な辞書形式に変換する。"""
        return {
            'strokes': self._serialize_strokes(),
            'texts': self._serialize_text_annotations(),
            'shapes': self._serialize_shape_annotations(),
        }

    def deserialize_all(self, data: Dict[str, Any]) -> None:
        """辞書データからすべての注釈を復元する。"""
        self._deserialize_strokes(data.get('strokes', {}))
        self._deserialize_text_annotations(data.get('texts', {}))
        self._deserialize_shape_annotations(data.get('shapes', {}))

    def _serialize_strokes(self) -> Dict[int, List[Dict[str, Any]]]:
        """ストローク注釈をシリアライズする。"""
        data = {}
        for page, items in self.annotations.items():
            data[page] = [{
                'type': item['type'],
                'color': item['color'].rgba(),
                'width': item['width'],
                'path': self._serialize_path(item['path'])
            } for item in items]
        return data

    def _deserialize_strokes(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """データからストローク注釈を復元する。"""
        self.annotations.clear()
        for page_str, items in data.items():
            page_int = int(page_str)
            self.annotations[page_int] = [{
                'type': item.get('type', 'pen'),
                'path': self._deserialize_path(item.get('path', [])),
                'color': QColor.fromRgba(item.get('color', QColor('black').rgba())),
                'width': item.get('width', 2)
            } for item in items]

    def _serialize_path(self, path: QPainterPath) -> List[Dict[str, Any]]:
        """QPainterPathをJSONシリアライズ可能な形式に変換する。"""
        elements = []
        for i in range(path.elementCount()):
            el = path.elementAt(i)
            elements.append({'x': el.x, 'y': el.y, 'type': int(el.type)})
        return elements

    def _deserialize_path(self, elements: List[Dict[str, Any]]) -> QPainterPath:
        """JSON形式からQPainterPathを復元する。"""
        path = QPainterPath()
        for i, elem in enumerate(elements):
            point = QPointF(elem.get('x', 0.0), elem.get('y', 0.0))
            # ElementType: MoveToElement = 0, LineToElement = 1
            if i == 0 or elem.get('type') == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        return path

    def _serialize_text_annotations(self) -> Dict[int, List[Dict[str, Any]]]:
        """テキスト注釈をシリアライズする。"""
        data = {}
        for page, widgets in self.text_annotations.items():
            data[page] = [{
                'text': w.text_edit.toPlainText(),
                'x': w.x(), 'y': w.y(), 'width': w.width(), 'height': w.height(),
                'color': w._color.rgba(),
                'font_point': w._font_point
            } for w in widgets]
        return data

    def _deserialize_text_annotations(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """データからテキスト注釈ウィジェットを復元する。"""
        self._clear_text_annotations()
        for page_str, items in data.items():
            page_int = int(page_str)
            restored = []
            for item in items:
                widget = TextAnnotationWidget(
                    self.main.pdf_display_label,
                    QColor.fromRgba(item.get('color')),
                    item.get('font_point')
                )
                widget.delete_requested.connect(lambda w, p=page_int: self.main.pdf_display_label._handle_text_delete(p, w))
                widget.setGeometry(item['x'], item['y'], item['width'], item['height'])
                widget.text_edit.setPlainText(item['text'])
                restored.append(widget)
            if restored:
                self.text_annotations[page_int] = restored

    def _serialize_shape_annotations(self) -> Dict[int, List[Dict[str, Any]]]:
        """図形注釈をシリアライズする。"""
        data = {}
        for page, widgets in self.shape_annotations.items():
            data[page] = [{
                'shape': w.shape_type,
                'x': w.x(), 'y': w.y(), 'width': w.width(), 'height': w.height(),
            } for w in widgets]
        return data

    def _deserialize_shape_annotations(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """データから図形注釈ウィジェットを復元する。"""
        self._clear_shape_annotations()
        for page_str, items in data.items():
            page_int = int(page_str)
            restored = []
            for item in items:
                widget = ShapeAnnotationWidget(
                    self.main.pdf_display_label,
                    item.get('shape'),
                    QSize(item.get('width'), item.get('height'))
                )
                widget.delete_requested.connect(lambda w, p=page_int: self.main.pdf_display_label._handle_shape_delete(p, w))
                widget.move(item['x'], item['y'])
                restored.append(widget)
            if restored:
                self.shape_annotations[page_int] = restored