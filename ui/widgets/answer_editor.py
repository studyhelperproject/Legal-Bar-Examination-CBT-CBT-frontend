from typing import Optional

from PyQt6.QtCore import pyqtSignal, Qt, QMimeData
from PyQt6.QtGui import QFont, QFontInfo, QTextOption, QKeyEvent
from PyQt6.QtWidgets import QTextEdit, QWidget

class AnswerGridEditor(QTextEdit):
    """
    司法試験の答案用紙を模した、グリッドベースのテキスト入力ウィジェット。

    指定された最大文字数と行数に基づいてテキスト入力を管理します。
    テキストが変更された際には `contentModified` シグナルを発行します。

    Attributes:
        contentModified (pyqtSignal): テキスト内容がユーザーによって変更されたときに発行されるシグナル。
    """
    contentModified = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None, columns: int = 30, rows: int = 23) -> None:
        """
        AnswerGridEditorのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。
            columns (int): 1行あたりの最大文字数。
            rows (int): 最大行数。
        """
        super().__init__(parent)
        self.max_chars: int = columns
        self.max_lines: int = rows
        self._internal_change: bool = False

        # フォント設定（ヒラギノ明朝が見つからない場合はMS明朝にフォールバック）
        base_font = QFont("Hiragino Mincho ProN", 14)
        if not QFontInfo(base_font).exactMatch():
            base_font = QFont("MS Mincho", 14)
        self.setFont(base_font)

        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self) -> None:
        """
        textChangedシグナルを処理する内部スロット。
        プログラムによる内部的な変更でない場合にのみ `contentModified` シグナルを発行する。
        """
        if self._internal_change:
            return
        self.contentModified.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        キー入力イベントをオーバーライドし、Enterキーで改行を挿入するようにする。
        """
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.insertPlainText('\n')
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source: QMimeData) -> None:
        """
        ペースト操作をオーバーライドし、プレーンテキストのみを挿入するようにする。
        """
        if source.hasText():
            self.insertPlainText(source.text())

    def get_content(self) -> str:
        """
        エディタの現在のテキスト内容を返す。

        Returns:
            str: プレーンテキストの内容。
        """
        return self.toPlainText()

    def set_content(self, text: str) -> None:
        """
        エディタのテキスト内容をプログラム的に設定する。
        この操作では `contentModified` シグナルは発行されない。

        Args:
            text (str): 設定するテキスト。
        """
        self._internal_change = True
        try:
            self.setPlainText(text)
        finally:
            self._internal_change = False

    def undo(self) -> None:
        """Undo操作を実行する。"""
        super().undo()

    def redo(self) -> None:
        """Redo操作を実行する。"""
        super().redo()