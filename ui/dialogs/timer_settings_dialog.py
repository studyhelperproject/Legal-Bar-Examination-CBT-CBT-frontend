# ui/dialogs/timer_settings_dialog.py
"""
タイマー設定用のダイアログウィンドウを提供します。

このモジュールには、試験の残り時間を設定し、タイマーの一時停止・再開を
制御するための TimerSettingsDialog クラスが含まれています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QSpinBox,
    QHBoxLayout, QPushButton, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from ..main_window import MainWindow


class TimerSettingsDialog(QDialog):
    """
    試験時間の設とタイマーの制御を行うモーダルダイアログ。

    時・分・秒を入力するスピンボックス、タイマーを一時停止/再開するボタン、
    そして設定を確定またはキャンセルするOK/Cancelボタンで構成されます。
    """
    def __init__(self, parent: Optional[QWidget], initial_seconds: int, timer_running: bool) -> None:
        """
        TimerSettingsDialogのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。通常はMainWindow。
            initial_seconds (int): ダイアログ表示時の初期残り時間（秒）。
            timer_running (bool): ダイアログ表示時にタイマーが作動中かどうか。
        """
        super().__init__(parent)
        self.setWindowTitle("タイマー設定")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        # 親ウィンドウへの参照を型安全に保持
        self.main_window: MainWindow = parent

        # UIコンポーネントの型ヒント
        self.hour_spin: QSpinBox
        self.minute_spin: QSpinBox
        self.second_spin: QSpinBox
        self.pause_button: QPushButton

        # 初期値を時・分・秒に変換
        hours = max(0, initial_seconds // 3600)
        minutes = max(0, (initial_seconds % 3600) // 60)
        seconds = max(0, initial_seconds % 60)

        layout = QVBoxLayout(self)
        grid = QGridLayout()

        grid.addWidget(QLabel("時間"), 0, 0)
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 99)
        self.hour_spin.setValue(min(hours, 99))
        grid.addWidget(self.hour_spin, 0, 1)

        grid.addWidget(QLabel("分"), 1, 0)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(minutes)
        grid.addWidget(self.minute_spin, 1, 1)

        grid.addWidget(QLabel("秒"), 2, 0)
        self.second_spin = QSpinBox()
        self.second_spin.setRange(0, 59)
        self.second_spin.setValue(seconds)
        grid.addWidget(self.second_spin, 2, 1)

        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        self.pause_button = QPushButton() # テキストは後で設定
        self.pause_button.clicked.connect(self._toggle_pause)
        button_layout.addWidget(self.pause_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)
        self._refresh_pause_button()

    def _toggle_pause(self) -> None:
        """タイマーの一時停止と再開を切り替える。"""
        if self.main_window.timer.isActive():
            self.main_window.pause_timer()
        else:
            if self.main_window.remaining_time > 0:
                self.main_window.resume_timer()
        self._refresh_pause_button()

    def _refresh_pause_button(self) -> None:
        """一時停止/再開ボタンのテキストを現在のタイマーの状態に合わせて更新する。"""
        running = self.main_window.timer.isActive()
        self.pause_button.setText("中断" if running else "再開")

    def total_seconds(self) -> int:
        """
        ダイアログで設定された時・分・秒を合計秒数に変換して返す。

        Returns:
            int: 設定された合計秒数。
        """
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()
        seconds = self.second_spin.value()
        return hours * 3600 + minutes * 60 + seconds