# ui/components.py
"""
アプリケーション全体で再利用されるカスタムUIコンポーネントを提供します。

- KanaInputFilter: QTextEditウィジェットに日本語かな入力機能（ローマ字/かなダイレクト）を追加するイベントフィルタ。
- ClickableLabel: クリックイベントを送信する機能を持つラベル。
"""
from __future__ import annotations
from weakref import WeakKeyDictionary
from typing import TYPE_CHECKING, Union, Optional

from PyQt6.QtWidgets import QLabel, QTextEdit, QPlainTextEdit, QWidget
from PyQt6.QtCore import Qt, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent

from utils.constants import VOWELS, ROMAJI_TO_HIRAGANA, KANA_DIRECT_SHIFT_MAP, KANA_DIRECT_MAP

if TYPE_CHECKING:
    from .main_window import MainWindow


class KanaInputFilter(QObject):
    """
    QTextEditおよびQPlainTextEditウィジェットに日本語かな入力機能を追加するイベントフィルタ。

    ローマ字入力モード（'roma'）と直接かな入力モード（'kana'）をサポートします。
    入力モードはset_modeメソッドで切り替えることができます。
    """
    def __init__(self, main_window: MainWindow) -> None:
        """
        KanaInputFilterのコンストラクタ。

        Args:
            main_window (MainWindow): 親となるメインウィンドウ。
        """
        super().__init__(main_window)
        self.main_window: MainWindow = main_window
        self.mode: str = 'off'  # 'off', 'roma', 'kana'
        self.buffers: WeakKeyDictionary[QWidget, str] = WeakKeyDictionary()

    def set_mode(self, mode: str) -> None:
        """
        かな入力のモードを設定します。

        Args:
            mode (str): 'roma', 'kana', または 'off' のいずれか。
                        それ以外の値が指定された場合は 'off' になります。
        """
        if mode not in ('roma', 'kana'):
            mode = 'off'
        if mode != self.mode:
            self.mode = mode
            self.buffers.clear()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        インストールされたウィジェットのイベントをフィルタリングする。

        KeyPressイベントを捕捉し、現在の入力モードに応じてかな変換処理を呼び出します。

        Args:
            obj (QObject): イベントの対象オブジェクト。
            event (QEvent): 発生したイベント。

        Returns:
            bool: イベントが処理され、さらなる伝播を停止する場合はTrue。
                  それ以外の場合はFalse。
        """
        if self.mode == 'off' or not isinstance(event, QKeyEvent) or event.type() != QEvent.Type.KeyPress:
            return False
        if not isinstance(obj, (QTextEdit, QPlainTextEdit)):
            return False
        if hasattr(obj, 'isReadOnly') and obj.isReadOnly():
            return False

        # イベントが発生したウィジェットがメインウィンドウまたはメモウィンドウ内にあるかチェック
        window = obj.window()
        if window not in (self.main_window, getattr(self.main_window, 'memo_window', None)):
            return False

        if self.mode == 'kana':
            return self._handle_direct_kana(obj, event)

        return self._handle_romaji(obj, event)

    def _handle_romaji(self, widget: Union[QTextEdit, QPlainTextEdit], event: QKeyEvent) -> bool:
        """ローマ字入力モードでのキーイベントを処理する。"""
        key = event.key()
        text = event.text()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._commit_pending_n(widget)
            return False

        if key == Qt.Key.Key_Backspace:
            buf = self.buffers.get(widget, '')
            if buf:
                self.buffers[widget] = buf[:-1]
                return True
            return False

        if not text or text in ('\r', '\n', '\t') or not text.isalpha():
            self._commit_pending_n(widget, force=True)
            return False

        char = text.lower()
        buf = self.buffers.get(widget, '') + char

        # 'nn' -> 'ん' + 'n'
        if char == 'n' and buf.endswith('nn'):
            self._insert_text(widget, 'ん')
            self.buffers[widget] = 'n'
            return True

        # 子音の連続 -> 'っ'
        if len(buf) >= 2 and buf[-1] == buf[-2] and buf[-1] not in VOWELS and buf[-1] != 'n':
            self._insert_text(widget, 'っ')
            buf = buf[-1]

        # ローマ字->ひらがな変換
        for length in range(min(3, len(buf)), 0, -1):
            segment = buf[-length:]
            if segment in ROMAJI_TO_HIRAGANA:
                kana = ROMAJI_TO_HIRAGANA[segment]
                self._insert_text(widget, kana)
                self.buffers[widget] = buf[:-length]
                return True

        self.buffers[widget] = buf
        return True

    def _handle_direct_kana(self, widget: Union[QTextEdit, QPlainTextEdit], event: QKeyEvent) -> bool:
        """直接かな入力モードでのキーイベントを処理する。"""
        key = event.key()
        text = event.text()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab) or key == Qt.Key.Key_Backspace:
            self.buffers.pop(widget, None)
            return False

        if not text:
            return False

        self.buffers.pop(widget, None)

        modifiers = event.modifiers()
        char: Optional[str] = None

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            char = KANA_DIRECT_SHIFT_MAP.get(text)
            if char is None:
                char = KANA_DIRECT_SHIFT_MAP.get(text.lower())

        if char is None:
            char = KANA_DIRECT_MAP.get(text)
        if char is None:
            char = KANA_DIRECT_MAP.get(text.lower())

        if char:
            self._insert_text(widget, char)
            return True

        return False

    def _commit_pending_n(self, widget: Union[QTextEdit, QPlainTextEdit], force: bool = False) -> None:
        """バッファに残っている 'n' を 'ん' として確定する。"""
        buf = self.buffers.get(widget, '')
        if buf:
            if buf == 'n' or (force and 'n' in buf):
                self._insert_text(widget, 'ん')
        self.buffers.pop(widget, None)

    def _insert_text(self, widget: Union[QTextEdit, QPlainTextEdit], text: str) -> None:
        """ウィジェットのカーソル位置にテキストを挿入する。"""
        cursor = widget.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        cursor.insertText(text)
        widget.setTextCursor(cursor)


class ClickableLabel(QLabel):
    """
    クリックされると 'clicked' シグナルを発するカスタムQLabel。
    カーソルがポインティングハンドカーソルに変わります。
    """
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        """ClickableLabelのコンストラクタ。"""
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        マウスの左ボタンが離されたときに 'clicked' シグナルを発する。
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)