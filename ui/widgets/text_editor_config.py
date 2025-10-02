from dataclasses import dataclass, field
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QFontInfo

@dataclass
class TextEditorConfig:
    """
    テキストエディタのUI設定をカプセル化するデータクラス。
    """
    font_family: str = "Hiragino Mincho ProN"
    fallback_font_family: str = "MS Mincho"
    font_size: int = 14
    line_color: QColor = field(default_factory=lambda: QColor(220, 220, 220))
    line_number_color: QColor = field(default_factory=lambda: QColor("#888888"))
    line_number_bg_color: QColor = field(default_factory=lambda: QColor("#f0f0f0"))
    line_number_border_color: QColor = field(default_factory=lambda: QColor("#d0d0d0"))
    background_color: QColor = field(default_factory=lambda: QColor(Qt.GlobalColor.white))
    editor_background_color: QColor = field(default_factory=lambda: QColor("transparent"))

    def get_font(self) -> QFont:
        """
        プライマリフォントを試み、利用できない場合はフォールバックフォントを使用してQFontオブジェクトを返す。
        """
        font = QFont(self.font_family, self.font_size)
        if not QFontInfo(font).exactMatch():
            font = QFont(self.fallback_font_family, self.font_size)
        return font