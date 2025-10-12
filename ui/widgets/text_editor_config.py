from dataclasses import dataclass, field
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QFontInfo

@dataclass
class TextEditorConfig:
    """
    テキストエディタのUI設定をカプセル化するデータクラス。
    """
    font_family: str = "ＭＳ 明朝"
    fallback_font_family: str = "MS Mincho"
    font_size: int = 20
    chars_per_line: int = 30
    line_height: int = 120
    
    # テキストエディタまわりのパディング
    padding_top: int = 0
    padding_right: int = 0
    padding_bottom: int = 0
    padding_left: int = 0

    line_color: QColor = field(default_factory=lambda: QColor(220, 220, 220))
    line_number_color: QColor = field(default_factory=lambda: QColor("#ff0000"))
    line_number_bg_color: QColor = field(default_factory=lambda: QColor("#f0f0f0"))
    line_number_border_color: QColor = field(default_factory=lambda: QColor("#d0d0d0"))
    background_color: QColor = field(default_factory=lambda: QColor(Qt.GlobalColor.white))
    # backgroundを白に。ここで白くしておかないと背景が黒くなる。
    editor_background_color: QColor = field(default_factory=lambda: QColor("#ffffff"))

    def get_font(self) -> QFont:
        """
        プライマリフォントを試み、利用できない場合はフォールバックフォントを使用してQFontオブジェクトを返す。
        """
        font = QFont(self.font_family, self.font_size)
        if not QFontInfo(font).exactMatch():
            font = QFont(self.fallback_font_family, self.font_size)
        return font

    def get_line_height(self) -> int:
        return self.line_height