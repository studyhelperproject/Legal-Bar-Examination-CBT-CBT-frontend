from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Union

from PyQt6.QtWidgets import QTextEdit, QPlainTextEdit, QWidget

if TYPE_CHECKING:
    from ..main_window import MainWindow

# Type alias for common text editor widgets
TextEditorWidget = Union[QTextEdit, QPlainTextEdit]

class ClipboardHandler:
    """
    アプリケーション内のクリップボード操作（コピー、カット、ペースト）をインテリジェントに処理するハンドラ。

    現在のフォーカス状態、ウィジェットの選択状態、可視性などに基づいて、
    クリップボード操作の対象となるべき最適なウィジェットを動的に解決します。
    """
    def __init__(self, main_window: MainWindow) -> None:
        """
        ClipboardHandlerのコンストラクタ。

        Args:
            main_window (MainWindow): 親となるメインウィンドウインスタンス。
        """
        self.main: MainWindow = main_window

    def _selected_text_annotation_editor(self) -> Optional[QTextEdit]:
        """現在選択されているテキスト注釈があれば、その内部のQTextEditを返す。"""
        selected = getattr(self.main.annotation_handler, 'selected_annotation', None)
        if selected and selected.get('type') == 'text':
            widget = selected.get('widget')
            text_edit = getattr(widget, 'text_edit', None)
            if isinstance(text_edit, QTextEdit):
                return text_edit
        return None

    def _is_editable_widget(self, widget: QWidget) -> bool:
        """指定されたウィジェットが編集可能（読み取り専用でない）かどうかを安全にチェックする。"""
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            return not widget.isReadOnly()
        if hasattr(widget, 'isReadOnly'):
            # hasattrでisReadOnlyメソッドの存在を確認してから呼び出す
            return not getattr(widget, 'isReadOnly')()
        return False

    def _widget_has_selection(self, widget: QWidget) -> bool:
        """指定されたウィジェットでテキストが選択されているかどうかを安全にチェックする。"""
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            cursor = widget.textCursor()
            return cursor is not None and cursor.hasSelection()
        if hasattr(widget, 'hasSelectedText'):
            return getattr(widget, 'hasSelectedText')()
        if hasattr(widget, 'selectedText'):
            return bool(getattr(widget, 'selectedText')())
        return False

    def _text_widget_candidates(self) -> List[TextEditorWidget]:
        """クリップボード操作の対象となりうるテキストウィジェットのリストを優先度順に生成する。"""
        candidates: List[TextEditorWidget] = []

        # 1. 現在フォーカスされているウィジェット
        focus_widget = self.main.focusWidget()
        if isinstance(focus_widget, (QTextEdit, QPlainTextEdit)):
            candidates.append(focus_widget)

        # 2. 選択されているテキスト注釈の編集ウィジェット
        annotation_editor = self._selected_text_annotation_editor()
        if annotation_editor and annotation_editor not in candidates:
            candidates.append(annotation_editor)

        # 3. 現在表示中の答案シートの編集ウィジェット
        if hasattr(self.main, 'answer_tab_widget'):
            current_sheet = self.main.answer_tab_widget.currentWidget()
            if current_sheet:
                editor = current_sheet.current_editor()
                if isinstance(editor, (QTextEdit, QPlainTextEdit)) and editor not in candidates:
                    candidates.append(editor)

        # 4. 表示されているメモウィンドウの編集ウィジェット
        if hasattr(self.main, 'memo_window') and self.main.memo_window and self.main.memo_window.isVisible():
            memo_edit = getattr(self.main.memo_window, 'memo_edit', None)
            if isinstance(memo_edit, QTextEdit) and memo_edit not in candidates:
                candidates.append(memo_edit)

        return candidates

    def _resolve_clipboard_target(self, operation: str) -> Optional[TextEditorWidget]:
        """
        指定された操作（'copy', 'cut', 'paste'）に最適なターゲットウィジェットを解決する。

        Args:
            operation (str): "copy", "cut", "paste" のいずれか。

        Returns:
            Optional[TextEditorWidget]: 操作対象として解決されたウィジェット。見つからなければNone。
        """
        candidates = self._text_widget_candidates()

        # 'copy'操作の場合、読み取り専用の法令ビューアも候補に加える
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

    def handle_copy(self) -> None:
        """コピー操作を処理する。適切なターゲットを見つけてcopy()を呼び出す。"""
        widget = self._resolve_clipboard_target('copy')
        if widget and hasattr(widget, 'copy'):
            widget.copy()

    def handle_cut(self) -> None:
        """カット操作を処理する。適切なターゲットを見つけてcut()を呼び出す。"""
        widget = self._resolve_clipboard_target('cut')
        if widget and hasattr(widget, 'cut'):
            widget.cut()

    def handle_paste(self) -> None:
        """ペースト操作を処理する。適切なターゲットを見つけてpaste()を呼び出す。"""
        widget = self._resolve_clipboard_target('paste')
        if widget and hasattr(widget, 'paste'):
            widget.paste()