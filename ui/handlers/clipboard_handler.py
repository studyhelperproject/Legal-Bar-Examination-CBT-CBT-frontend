from PyQt6.QtWidgets import QTextEdit, QPlainTextEdit
from PyQt6.QtCore import Qt

class ClipboardHandler:
    def __init__(self, main_window):
        self.main = main_window

    def _selected_text_annotation_editor(self):
        selected = getattr(self.main.annotation_handler, 'selected_annotation', None)
        if selected and selected.get('type') == 'text':
            widget = selected.get('widget')
            text_edit = getattr(widget, 'text_edit', None)
            if isinstance(text_edit, QTextEdit):
                return text_edit
        return None

    def _is_editable_widget(self, widget):
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            return not widget.isReadOnly()
        # Fallback for other widget types
        if hasattr(widget, 'isReadOnly'):
            return not widget.isReadOnly()
        return False

    def _widget_has_selection(self, widget):
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            cursor = widget.textCursor()
            return cursor is not None and cursor.hasSelection()
        if hasattr(widget, 'selectedText'):
            return bool(widget.selectedText())
        return False

    def _text_widget_candidates(self):
        candidates = []

        # 1. Currently focused widget
        focus_widget = self.main.focusWidget()
        if isinstance(focus_widget, (QTextEdit, QPlainTextEdit)):
            candidates.append(focus_widget)

        # 2. Selected text annotation editor
        annotation_editor = self._selected_text_annotation_editor()
        if annotation_editor and annotation_editor not in candidates:
            candidates.append(annotation_editor)

        # 3. Current answer sheet editor
        if hasattr(self.main, 'answer_tab_widget'):
            current_sheet = self.main.answer_tab_widget.currentWidget()
            if current_sheet:
                editor = current_sheet.current_editor()
                if isinstance(editor, (QTextEdit, QPlainTextEdit)) and editor not in candidates:
                    candidates.append(editor)

        # 4. Visible memo window editor
        if hasattr(self.main, 'memo_window') and self.main.memo_window and self.main.memo_window.isVisible():
            memo_edit = getattr(self.main.memo_window, 'memo_edit', None)
            if isinstance(memo_edit, QTextEdit) and memo_edit not in candidates:
                candidates.append(memo_edit)

        return candidates

    def _resolve_clipboard_target(self, operation):
        candidates = self._text_widget_candidates()

        # For 'copy', we also consider the read-only law viewer
        if operation == 'copy' and hasattr(self.main, 'law_main_area'):
            if self.main.law_main_area not in candidates:
                candidates.append(self.main.law_main_area)

        for widget in candidates:
            if not widget or not widget.isEnabled():
                continue

            if operation == 'copy':
                if self._widget_has_selection(widget):
                    return widget
            elif operation == 'cut':
                if self._is_editable_widget(widget) and self._widget_has_selection(widget):
                    return widget
            elif operation == 'paste':
                if self._is_editable_widget(widget):
                    return widget

        return None

    def handle_copy(self):
        widget = self._resolve_clipboard_target('copy')
        if widget and hasattr(widget, 'copy'):
            widget.copy()

    def handle_cut(self):
        widget = self._resolve_clipboard_target('cut')
        if widget and hasattr(widget, 'cut'):
            widget.cut()

    def handle_paste(self):
        widget = self._resolve_clipboard_target('paste')
        if widget and hasattr(widget, 'paste'):
            widget.paste()