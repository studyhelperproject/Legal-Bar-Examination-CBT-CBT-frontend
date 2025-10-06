from typing import Optional, Tuple

from PyQt6.QtCore import Qt, QEvent, QTimer, QObject
from PyQt6.QtGui import QFont, QHideEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit


class MemoWindow(QWidget):
    """
    親ウィンドウ上にオーバーレイ表示される、フレームレスのメモ用ウィンドウ。

    左半分、右半分、全画面の3つの表示モードを持ち、親ウィンドウの移動やリサイズに追従します。
    """
    MODES: Tuple[str, str, str] = ("left", "right", "full")

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        MemoWindowのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親となるウィジェット。通常はMainWindow。
        """
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("メモ")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "MemoWindow { background-color: rgba(255, 255, 255, 0.95); border: 1px solid #666; }"
        )

        # --- 属性の型定義 ---
        self._parent_window: Optional[QWidget] = parent
        self.mode: str = "left"
        self.left_button: QPushButton
        self.full_button: QPushButton
        self.right_button: QPushButton
        self.memo_edit: QTextEdit
        self._base_font: QFont

        if self._parent_window:
            self._parent_window.installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ツールバーの作成
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        self.left_button = QPushButton("左配置")
        self.full_button = QPushButton("全画面")
        self.right_button = QPushButton("右配置")
        for btn in [self.left_button, self.full_button, self.right_button]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toolbar_layout.addWidget(btn)
        toolbar_layout.addStretch()

        close_button = QPushButton("閉じる")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.hide)
        toolbar_layout.addWidget(close_button)

        # テキスト編集エリアの作成
        self.memo_edit = QTextEdit()
        font = self.memo_edit.font()
        font.setPointSize(14)
        self.memo_edit.setFont(font)
        self._base_font = QFont(self.memo_edit.font())

        layout.addLayout(toolbar_layout)
        layout.addWidget(self.memo_edit)

        # 接続
        self.left_button.clicked.connect(lambda: self.show_overlay("left"))
        self.right_button.clicked.connect(lambda: self.show_overlay("right"))
        self.full_button.clicked.connect(lambda: self.show_overlay("full"))

    def apply_font_scale(self, scale: float) -> None:
        """
        UI全体のフォントスケール変更をこのウィジェットのフォントに適用する。
        """
        if not hasattr(self, '_base_font') or self._base_font is None:
            self._base_font = QFont(self.memo_edit.font())

        font = QFont(self._base_font)
        base_size = font.pointSizeF() if font.pointSizeF() > 0 else float(font.pointSize())
        if base_size > 0:
            font.setPointSizeF(base_size * scale)
        self.memo_edit.setFont(font)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        親ウィンドウのイベントを監視し、リサイズや移動があれば追従して位置を更新する。
        """
        if obj is self._parent_window and event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
            if self.isVisible():
                QTimer.singleShot(0, self._apply_geometry)
        return super().eventFilter(obj, event)

    def show_overlay(self, mode: str = "left") -> None:
        """
        指定されたモードでメモウィンドウをオーバーレイ表示する。

        Args:
            mode (str): "left", "right", "full" のいずれかの表示モード。
        """
        if mode not in self.MODES:
            mode = "left"
        self.mode = mode
        self._apply_geometry()
        self.show()
        self.raise_()
        self.activateWindow()
        self.memo_edit.setFocus()

    def _apply_geometry(self) -> None:
        """親ウィンドウの現在のジオメトリに基づいて、自身の位置とサイズを調整する。"""
        parent = self._parent_window
        if not parent:
            return

        parent_rect = parent.rect()
        top_left = parent.mapToGlobal(parent_rect.topLeft())
        width, height = parent_rect.width(), parent_rect.height()

        if self.mode == "left":
            x, y, w, h = top_left.x(), top_left.y(), max(1, width // 2), height
        elif self.mode == "right":
            w = max(1, width // 2)
            x, y, h = top_left.x() + width - w, top_left.y(), height
        else:  # "full"
            x, y, w, h = top_left.x(), top_left.y(), width, height

        self.setGeometry(x, y, w, h)

    def hideEvent(self, event: QHideEvent) -> None:
        """ウィンドウが非表示になるときに呼ばれるイベントハンドラ。"""
        super().hideEvent(event)
        self.mode = self.mode or "left"