from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QSize, QRect
from PyQt6.QtGui import (QColor, QPainter, QPen, QPainterPath, QPaintEvent,
                         QMouseEvent, QEnterEvent, QResizeEvent)
from PyQt6.QtWidgets import QWidget, QToolButton

if TYPE_CHECKING:
    from ..main_window import MainWindow

class ShapeAnnotationWidget(QWidget):
    """
    PDF上に配置される、移動・リサイズ可能な図形（円、三角、×）を描画するウィジェット。

    透明な背景を持ち、選択状態に応じて外観が変化します。
    ユーザーはウィジェットをドラッグして移動したり、右下のハンドルでリサイズできます。
    """
    delete_requested = pyqtSignal(QWidget)
    HANDLE_SIZE: int = 14
    MIN_SIZE: QSize = QSize(60, 60)

    def __init__(self, parent: Optional[QWidget] = None, shape_type: str = "circle", initial_size: QSize = QSize(160, 160)) -> None:
        """
        ShapeAnnotationWidgetのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。
            shape_type (str): 描画する図形の種類 ("circle", "triangle", "cross")。
            initial_size (QSize): ウィジェットの初期サイズ。
        """
        super().__init__(parent)
        self.shape_type: str = shape_type
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setMouseTracking(True)

        # --- 状態変数の型定義 ---
        self._selected: bool = False
        self._press_pos: Optional[QPoint] = None
        self._widget_start: Optional[QPoint] = None
        self._size_start: Optional[QSize] = None
        self._interaction_mode: Optional[str] = None  # "drag" or "resize"
        self._dragging: bool = False

        # --- UI要素の型定義 ---
        self.delete_button: QToolButton = QToolButton(self)
        self.delete_button.setText("削除")
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.setStyleSheet("QToolButton { background-color: rgba(0, 0, 0, 0.55); color: white; padding: 2px 8px; border-radius: 4px; }")
        self.delete_button.setAutoRaise(True)
        self.delete_button.hide()
        self.delete_button.clicked.connect(self.delete_requested.emit)

        self.setMinimumSize(self.MIN_SIZE)
        self.resize(max(initial_size.width(), self.MIN_SIZE.width()), max(initial_size.height(), self.MIN_SIZE.height()))
        self._ensure_delete_button_position()

    def _main_window(self) -> Optional[MainWindow]:
        """親をたどってMainWindowインスタンスを見つける。"""
        widget = self
        while widget is not None:
            if hasattr(widget, 'history_handler'):
                return widget
            widget = widget.parentWidget()
        return None

    def set_selected(self, selected: bool) -> None:
        """ウィジェットの選択状態を設定し、外観を更新する。"""
        if self._selected == selected: return
        self._selected = selected
        self.delete_button.setVisible(selected)
        if selected: self._ensure_delete_button_position()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        図形と選択ハンドルを描画する。
        `shape_type`と選択状態に応じて描画内容が変わります。
        """
        super().paintEvent(event)
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

        if self._selected:
            handle_rect = self._resize_handle_rect()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(accent)
            painter.drawRect(handle_rect)

    def _start_interaction(self, global_pos: QPoint, mode: str) -> None:
        """ドラッグまたはリサイズのインタラクションを開始する。"""
        self._interaction_mode = mode
        self._press_pos = global_pos
        self._widget_start = self.pos()
        self._size_start = self.size()
        self._dragging = False
        self.setCursor(Qt.CursorShape.ClosedHandCursor if mode == "drag" else Qt.CursorShape.SizeFDiagCursor)

    def _update_interaction(self, global_pos: QPoint) -> bool:
        """ドラッグまたはリサイズ中にウィジェットの位置やサイズを更新する。"""
        if self._interaction_mode is None or self._press_pos is None: return False
        delta = global_pos - self._press_pos
        if not self._dragging and delta.manhattanLength() > 5:
            self._dragging = True
        if not self._dragging: return False

        if self._interaction_mode == "drag" and self._widget_start is not None:
            new_pos = self._widget_start + delta
            if self.parentWidget():
                max_x = self.parentWidget().width() - self.width()
                max_y = self.parentWidget().height() - self.height()
                new_pos.setX(max(0, min(new_pos.x(), max_x)))
                new_pos.setY(max(0, min(new_pos.y(), max_y)))
            self.move(new_pos)
        elif self._interaction_mode == "resize" and self._size_start is not None:
            new_w = max(self.MIN_SIZE.width(), self._size_start.width() + delta.x())
            new_h = max(self.MIN_SIZE.height(), self._size_start.height() + delta.y())
            self.resize(new_w, new_h)

        self.update()
        return True

    def _end_interaction(self) -> bool:
        """インタラクションを終了し、必要であればUndo履歴に登録する。"""
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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウスプレスイベント。ドラッグまたはリサイズのインタラクションを開始する。"""
        if event.button() != Qt.MouseButton.LeftButton: return super().mousePressEvent(event)
        main_window = self._main_window()
        if main_window: main_window.annotation_handler.select_shape_annotation(self)

        if main_window and main_window.annotation_handler.current_tool == "select":
            mode = "resize" if self._resize_handle_rect().contains(event.pos()) else "drag"
            self._start_interaction(event.globalPosition().toPoint(), mode)
            self.setFocus()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウスムーブイベント。インタラクション中の更新やカーソル形状の変更を行う。"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._update_interaction(event.globalPosition().toPoint()):
                event.accept()
        elif self._interaction_mode is None:
            cursor_shape = Qt.CursorShape.SizeFDiagCursor if self._resize_handle_rect().contains(event.pos()) else Qt.CursorShape.OpenHandCursor
            self.setCursor(cursor_shape)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウスリリースイベント。インタラクションを終了する。"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._end_interaction():
                event.accept()

    def enterEvent(self, event: QEnterEvent) -> None:
        """マウスカーソルがウィジェットに入ったときのイベント。"""
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """マウスカーソルがウィジェットから出たときのイベント。"""
        if self._interaction_mode is None:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """ウィジェットのリサイズイベント。削除ボタンの位置を更新する。"""
        super().resizeEvent(event)
        self._ensure_delete_button_position()

    def _resize_handle_rect(self) -> QRect:
        """右下のりサイズ用ハンドルの矩形を返す。"""
        return QRect(self.width() - self.HANDLE_SIZE - 2, self.height() - self.HANDLE_SIZE - 2, self.HANDLE_SIZE, self.HANDLE_SIZE)

    def _ensure_delete_button_position(self) -> None:
        """削除ボタンをウィジェットの右上に配置する。"""
        size = self.delete_button.sizeHint()
        self.delete_button.resize(size)
        self.delete_button.move(self.width() - size.width() - 8, 6)
        self.delete_button.raise_()