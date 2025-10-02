# ui/components.py
from weakref import WeakKeyDictionary
from PyQt6.QtWidgets import QLabel, QTextEdit, QPlainTextEdit
from PyQt6.QtCore import Qt, QObject, QEvent, pyqtSignal
from utils.constants import VOWELS, ROMAJI_TO_HIRAGANA, KANA_DIRECT_SHIFT_MAP, KANA_DIRECT_MAP

class KanaInputFilter(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.mode = 'off'
        self.buffers = WeakKeyDictionary()

    def set_mode(self, mode):
        if mode not in ('roma', 'kana'):
            mode = 'off'
        if mode != self.mode:
            self.mode = mode
            self.buffers.clear()

    def eventFilter(self, obj, event):
        if self.mode == 'off' or event.type() != QEvent.Type.KeyPress:
            return False
        if not isinstance(obj, (QTextEdit, QPlainTextEdit)):
            return False
        if hasattr(obj, 'isReadOnly') and obj.isReadOnly():
            return False
        window = obj.window()
        if window not in (self.main_window, getattr(self.main_window, 'memo_window', None)):
            return False
        if self.mode == 'kana':
            return self._handle_direct_kana(obj, event)
        return self._handle_romaji(obj, event)

    def _handle_romaji(self, widget, event):
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

        if not text:
            return False

        if text in ('\r', '\n', '\t'):
            self._commit_pending_n(widget)
            return False

        if not text.isalpha():
            self._commit_pending_n(widget, force=True)
            return False

        char = text.lower()
        buf = self.buffers.get(widget, '') + char

        if char == 'n' and buf.endswith('nn'):
            self._insert_text(widget, 'ん')
            self.buffers[widget] = 'n'
            return True

        if len(buf) >= 2 and buf[-1] == buf[-2] and buf[-1] not in VOWELS and buf[-1] != 'n':
            self._insert_text(widget, 'っ')
            buf = buf[-1]

        for length in range(min(3, len(buf)), 0, -1):
            segment = buf[-length:]
            if segment in ROMAJI_TO_HIRAGANA:
                kana = ROMAJI_TO_HIRAGANA[segment]
                self._insert_text(widget, kana)
                remainder = buf[:-length]
                if remainder:
                    self.buffers[widget] = remainder
                else:
                    self.buffers.pop(widget, None)
                return True

        self.buffers[widget] = buf
        return True

    def _handle_direct_kana(self, widget, event):
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            self.buffers.pop(widget, None)
            return False
        if key == Qt.Key.Key_Backspace:
            return False
        text = event.text()
        if not text:
            return False

        self.buffers.pop(widget, None)

        modifiers = event.modifiers()
        char = None
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

    def _commit_pending_n(self, widget, force=False):
        buf = self.buffers.get(widget, '')
        if buf:
            if buf == 'n' or (force and 'n' in buf):
                self._insert_text(widget, 'ん')
        self.buffers.pop(widget, None)

    def _insert_text(self, widget, text):
        cursor = widget.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        cursor.insertText(text)
        widget.setTextCursor(cursor)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)