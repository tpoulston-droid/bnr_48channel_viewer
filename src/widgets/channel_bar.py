"""
src/widgets/channel_bar.py
Individual vertical bar widget representing an optical photodiode channel.
Provides flexible parameter binding and backward-compatibility method aliases.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QProgressBar, QSizePolicy, QVBoxLayout, QWidget


class ChannelBar(QWidget):
    """Vertical bar widget rendering an optical photodiode sensor channel."""

    def __init__(
        self,
        ch_num: int = 0,
        parent=None,
        max_range: int = 255,
        channel_num: int = None,
        channel_id: int = None,
        **kwargs,
    ):
        super().__init__(parent)

        # Support ch_num, channel_num, or channel_id keyword arguments
        if channel_num is not None:
            self.ch_num = int(channel_num)
        elif channel_id is not None:
            self.ch_num = int(channel_id)
        else:
            self.ch_num = int(ch_num)

        self.max_range = max_range
        self.current_value = 0

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # 1. Channel Title (CH 00 - CH 59)
        self.lbl_title = QLabel(f"CH {self.ch_num:02d}")
        self.lbl_title.setFont(QFont("Segoe UI", 7, QFont.Bold))
        self.lbl_title.setStyleSheet("color: #212529;")
        self.lbl_title.setAlignment(Qt.AlignCenter)

        # 2. Vertical Progress Bar
        self.pbar = QProgressBar()
        self.pbar.setOrientation(Qt.Vertical)
        self.pbar.setRange(0, self.max_range)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        self.pbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.pbar.setFixedWidth(18)
        self.pbar.setMinimumHeight(110)

        # 3. Numeric Count Readout
        self.lbl_val = QLabel("0")
        self.lbl_val.setFont(QFont("Segoe UI", 7))
        self.lbl_val.setStyleSheet("color: #495057;")
        self.lbl_val.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.lbl_title, 0, Qt.AlignCenter)
        layout.addWidget(self.pbar, 1, Qt.AlignCenter)
        layout.addWidget(self.lbl_val, 0, Qt.AlignCenter)

        self._apply_bar_style("#28a745")

    def _apply_bar_style(self, color_hex: str):
        """Applies stylesheet styling to the vertical progress bar."""
        self.pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #f1f3f5;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 2px;
            }}
        """)

    def _apply_style(self, color_hex: str):
        """Backward-compatibility alias for _apply_bar_style."""
        self._apply_bar_style(color_hex)

    def set_value(self, val: int):
        """
        Updates the vertical bar and numeric count.
        Triage thresholds:
          - Active / Healthy: >= 25 counts (Green)
          - Edge Margin / Low Attenuation: 10 - 24 counts (Yellow)
          - Dead Channel / Disconnected / Blocked: < 10 counts (Red)
        """
        v = int(val)
        self.current_value = v

        if v > self.pbar.maximum():
            self.pbar.setMaximum(1023)

        self.pbar.setValue(max(0, min(self.pbar.maximum(), v)))
        self.lbl_val.setText(str(v))

        if v >= 25:
            color = "#28a745"  # Green
            self.lbl_val.setStyleSheet("color: #212529; font-weight: normal;")
        elif v >= 10:
            color = "#ffc107"  # Yellow
            self.lbl_val.setStyleSheet("color: #856404; font-weight: bold;")
        else:
            color = "#dc3545"  # Red
            self.lbl_val.setStyleSheet("color: #dc3545; font-weight: bold;")

        self._apply_bar_style(color)

    def setValue(self, val: int):
        """Qt API alias for set_value."""
        self.set_value(val)

    def update_value(self, val: int):
        """Legacy helper alias for set_value."""
        self.set_value(val)


# Backward-compatibility alias
ChannelBarWidget = ChannelBar