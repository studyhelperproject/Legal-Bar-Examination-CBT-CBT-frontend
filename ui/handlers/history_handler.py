from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from ..main_window import MainWindow

class HistoryHandler:
    """
    アプリケーションの「元に戻す（Undo）」および「やり直し（Redo）」機能を管理するクラス。

    PDFの表示状態、注釈、答案の内容など、アプリケーションの主要な状態をスナップショットとして
    スタックに記録し、ユーザーが過去の状態に戻ったり、進んだりできるようにします。
    """
    def __init__(self, main_window: MainWindow) -> None:
        """
        HistoryHandlerのコンストラクタ。

        Args:
            main_window (MainWindow): 親となるメインウィンドウインスタンス。
        """
        self.main: MainWindow = main_window
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.max_history: int = 50
        self._restoring: bool = False

    def is_restoring(self) -> bool:
        """現在、状態を復元中かどうかを返す。これにより、復元中の操作が新たな履歴として登録されるのを防ぐ。"""
        return self._restoring

    def clear_history(self) -> None:
        """Undo/Redoの履歴をすべてクリアする。"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._update_history_actions()

    def register_snapshot(self) -> None:
        """
        現在のアプリケーションの状態をスナップショットとして取得し、Undoスタックに登録する。
        Redoスタックはクリアされる。
        """
        if self._restoring:
            return

        snapshot = self._serialize_state()
        if not snapshot:
            return

        # 連続する重複したスナップショットを避ける
        if self.undo_stack and snapshot == self.undo_stack[-1]:
            return

        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        self.redo_stack.clear()
        self._update_history_actions()

    def undo(self) -> None:
        """一つ前の状態に戻す。"""
        if len(self.undo_stack) <= 1:
            return

        current = self.undo_stack.pop()
        self.redo_stack.append(current)

        target = self.undo_stack[-1]
        self._restore_state(target)
        self._update_history_actions()

    def redo(self) -> None:
        """元に戻した操作をやり直す。"""
        if not self.redo_stack:
            return

        target = self.redo_stack.pop()
        self._restore_state(target)
        self.undo_stack.append(target)
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        """Undo/Redoが可能かどうかに基づいて、ツールバーのボタンの有効/無効を切り替える。"""
        can_undo = len(self.undo_stack) > 1
        can_redo = bool(self.redo_stack)
        self.main.undo_toolbar_action.setEnabled(can_undo)
        self.main.redo_toolbar_action.setEnabled(can_redo)

    def _serialize_state(self) -> Dict[str, Any]:
        """
        現在のアプリケーションの状態をシリアライズし、単一の辞書（スナップショット）として返す。
        このスナップショットはUndo/Redoの単位となる。
        """
        if not self.main.pdf_handler.pdf_document:
            return {}

        h_val = self.main.pdf_scroll_area.horizontalScrollBar().value()
        v_val = self.main.pdf_scroll_area.verticalScrollBar().value()

        return {
            'pdf_state': {
                'current_page': self.main.pdf_handler.current_page,
                'zoom': self.main.pdf_handler.zoom_factor,
                'spread': self.main.pdf_handler.spread_mode,
                'fit_mode': self.main.pdf_handler.fit_mode,
                'scroll_horizontal': self.main.scroll_toggle_action.isChecked(),
                'scroll_values': (h_val, v_val),
            },
            'annotations': self.main.annotation_handler.serialize_all(),
            'answers': self._serialize_answers()
        }

    def _restore_state(self, state: Dict[str, Any]) -> None:
        """指定された状態スナップショットをアプリケーションに適用する。"""
        if not state:
            return

        self._restoring = True
        try:
            # PDFの状態を復元
            pdf_state = state.get('pdf_state', {})
            pdf_handler = self.main.pdf_handler
            pdf_handler.zoom_factor = pdf_state.get('zoom', 1.0)
            pdf_handler.spread_mode = pdf_state.get('spread', False)
            pdf_handler.fit_mode = pdf_state.get('fit_mode')

            horizontal = pdf_state.get('scroll_horizontal', False)
            self.main.scroll_toggle_action.setChecked(horizontal)
            pdf_handler._apply_scroll_settings_without_refresh(horizontal)
            self.main.spread_toggle_action.setChecked(pdf_handler.spread_mode)

            # 注釈を復元
            self.main.annotation_handler.deserialize_all(state.get('annotations', {}))

            # 答案を復元
            self._deserialize_answers(state.get('answers', []))

            # ページとスクロール位置を復元
            target_page = max(0, min(pdf_state.get('current_page', 0), pdf_handler.total_pages - 1))
            pdf_handler.show_page(target_page)

            scroll_values = pdf_state.get('scroll_values', (0, 0))
            self.main.pdf_scroll_area.horizontalScrollBar().setValue(scroll_values[0])
            self.main.pdf_scroll_area.verticalScrollBar().setValue(scroll_values[1])

            self.main.annotation_handler.clear_selection()
        finally:
            self._restoring = False

    def _serialize_answers(self) -> List[Dict[str, Any]]:
        """全答案シートの内容をシリアライズする。"""
        return [{
            'page_texts': sheet.get_page_texts(),
            'current_page': sheet.current_page_index
        } for sheet in self.main.answer_sheets]

    def _deserialize_answers(self, data: List[Dict[str, Any]]) -> None:
        """シリアライズされたデータから全答案シートの内容を復元する。"""
        if not data: return
        for i, sheet_data in enumerate(data):
            if i < len(self.main.answer_sheets):
                sheet = self.main.answer_sheets[i]
                texts = sheet_data.get('page_texts', [])
                padded = texts + [''] * (sheet.TOTAL_PAGES - len(texts))
                sheet.set_page_texts(padded[:sheet.TOTAL_PAGES])
                sheet.set_current_page(sheet_data.get('current_page', 0))
        self.main.update_char_count()

    def serialize_full_session(self) -> Dict[str, Any]:
        """
        セッション全体の状態をファイル保存用にシリアライズする。
        Undo/Redo用のスナップショットよりも多くの情報（タイマー、UI設定など）を含む。
        """
        payload = {
            'version': 1,
            'saved_at': datetime.now().isoformat(),
            'remaining_time': self.main.remaining_time,
            'timer_paused': self.main.timer_paused,
            'input_mode': self.main.input_mode,
            'answers': self._serialize_answers(),
            'law_bookmarks': self.main.law_bookmarks,
            'ui_font_scale': self.main.ui_font_scale,
        }
        if self.main.pdf_handler.current_pdf_path:
            payload['pdf'] = {
                'path': self.main.pdf_handler.current_pdf_path,
                'state': self._serialize_state()
            }
        else:
            payload['pdf'] = None
        return payload