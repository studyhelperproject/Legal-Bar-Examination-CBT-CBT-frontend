# ui/dialogs.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QSpinBox,
    QHBoxLayout, QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt

class TimerSettingsDialog(QDialog):
    def __init__(self, parent, initial_seconds, timer_running):
        super().__init__(parent)
        self.setWindowTitle("タイマー設定")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.main_window = parent

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
        self.pause_button = QPushButton("中断" if timer_running else "再開")
        self.pause_button.clicked.connect(self._toggle_pause)
        button_layout.addWidget(self.pause_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)
        self._refresh_pause_button()

    def _toggle_pause(self):
        if self.main_window.timer.isActive():
            self.main_window.pause_timer()
        else:
            if self.main_window.remaining_time > 0:
                self.main_window.resume_timer()
        self._refresh_pause_button()

    def _refresh_pause_button(self):
        running = self.main_window.timer.isActive()
        self.pause_button.setText("中断" if running else "再開")

    def total_seconds(self):
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()
        seconds = self.second_spin.value()
        return hours * 3600 + minutes * 60 + seconds