from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from .scrollable_editor import ScrollableAnswerEditor
from .text_editor_config import TextEditorConfig


class AnswerSheetPageWidget(QWidget):
    """
    司法試験の答案用紙の1ページを表現するウィジェット。
    """

    def __init__(self, config: TextEditorConfig, parent: Optional[QWidget] = None) -> None:
        """
        AnswerSheetPageWidgetのコンストラクタ。

        Args:
            config (TextEditorConfig): エディタのUI設定。
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)
        self.config = config
        self.editor: ScrollableAnswerEditor = ScrollableAnswerEditor(config=config, parent=self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.editor)

        self.setFocusProxy(self.editor)

    def get_content(self) -> str:
        """内部エディタのテキスト内容を取得する。"""
        return self.editor.get_content()

    def set_content(self, text: str) -> None:
        """内部エディタにテキスト内容を設定する。"""
        self.editor.set_content(text)

    def undo(self) -> None:
        """内部エディタのUndo操作を実行する。"""
        self.editor.undo()

    def redo(self) -> None:
        """内部エディタのRedo操作を実行する。"""
        self.editor.redo()