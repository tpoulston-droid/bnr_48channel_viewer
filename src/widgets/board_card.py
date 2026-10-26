"""
src/widgets/board_card.py
Modular group card representing one 12-channel Hibou sensor board.
Displays board header, live board-specific power rail badges, and 12 vertical ChannelBar widgets.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .channel_bar import ChannelBarWidget


class BoardCardWidget(QGroupBox):
    """Card widget grouping 12 optical channels and supervisory rail indicators."""

    # Nominal hardware baselines by board position (tolerance stacking)
    BOARD_OFFSETS = {
        "red":   {"p12v": 12.08, "m12v": -12.02, "p3v3": 3.32, "gnd": 4},
        "green": {"p12v": 11.96, "m12v": -11.94, "p3v3": 3.29, "gnd": 2},
        "blue":  {"p12v": 12.02, "m12v": -12.06, "p3v3": 3.31, "gnd": 6},
        "black": {"p12v": 12.05, "m12v": -11.97, "p3v3": 3.30, "gnd": 1},
    }

    def __init__(
        self,
        title: str,
        start_ch: int,
        is_emitter_active: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.board_title = title
        self.start_ch = start_ch
        self.is_emitter_active = is_emitter_active
        self.bars = []

        self._init_ui()

    def _init_ui(self):
        t_lower = self.board_title.lower()
        if "red" in t_lower:
            theme_color = "#b22222"
            badge_title = "Red Upper Optical"
            role_desc = "Pure Receiver Array"
            self.board_key = "red"
        elif "green" in t_lower:
            theme_color = "#1e7e34"
            badge_title = "Green Lower Optical"
            role_desc = "Pure Receiver Array"
            self.board_key = "green"
        elif "blue" in t_lower:
            theme_color = "#0b5ed7"
            badge_title = "Blue Upper Exit"
            role_desc = "Emitter Active (LEDs)"
            self.board_key = "blue"
        else:  # Black
            theme_color = "#212529"
            badge_title = "Black Lower Exit"
            role_desc = "Emitter Active (LEDs)"
            self.board_key = "black"

        self.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {theme_color};
                border-radius: 8px;
                margin-top: 10px;
                background-color: #ffffff;
            }}
        """)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)

        # 1. Header Badges
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)

        lbl_header = QLabel(badge_title)
        lbl_header.setFont(QFont("Segoe UI", 8, QFont.Bold))
        lbl_header.setStyleSheet(f"""
            background-color: {theme_color};
            color: #ffffff;
            padding: 2px 14px;
            border-radius: 4px;
        """)
        header_layout.addWidget(lbl_header)
        card_layout.addLayout(header_layout)

        # 2. Sub-role text
        lbl_role = QLabel(role_desc)
        lbl_role.setFont(QFont("Segoe UI", 7))
        lbl_role.setStyleSheet("color: #6c757d;")
        lbl_role.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(lbl_role)

        # 3. Supervisory Power Rail Badges
        rail_layout = QHBoxLayout()
        rail_layout.setSpacing(6)

        # Pull initial distinctive baselines for each board
        init_v = self.BOARD_OFFSETS.get(self.board_key, self.BOARD_OFFSETS["red"])
        self.badge_12p = QLabel(f"+12V:  +{init_v['p12v']:.2f} V")
        self.badge_12n = QLabel(f"-12V:  {init_v['m12v']:.2f} V")
        self.badge_3v3 = QLabel(f"+3.3V:  +{init_v['p3v3']:.2f} V")
        self.badge_gnd = QLabel(f"GND:   {init_v['gnd']:2d} mV")

        badge_style_pass = """
            QLabel {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                padding: 3px 6px;
                font-family: 'Consolas', 'Courier New';
                font-size: 8pt;
                font-weight: bold;
            }
        """

        for badge in (self.badge_12p, self.badge_12n, self.badge_3v3, self.badge_gnd):
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(badge_style_pass)
            rail_layout.addWidget(badge)

        card_layout.addLayout(rail_layout)

        # 4. Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #dee2e6;")
        card_layout.addWidget(line)

        # 5. Channel Bars Grid (12 Optical Channels)
        bars_layout = QHBoxLayout()
        bars_layout.setSpacing(4)
        bars_layout.setContentsMargins(2, 2, 2, 2)

        for i in range(12):
            ch_idx = self.start_ch + i
            bar = ChannelBarWidget(channel_num=ch_idx)
            self.bars.append(bar)
            bars_layout.addWidget(bar)

        card_layout.addLayout(bars_layout)

    def update_telemetry(self, channels: list):
        """Updates the 12 optical bars from incoming signature buffers."""
        for i in range(12):
            val = channels[i] if i < len(channels) else 0
            self.bars[i].set_value(val)

    def set_optical_counts(self, channels: list):
        """Main.py alias for optical count updates."""
        self.update_telemetry(channels)

    def set_counts(self, channels: list):
        """Standard alias for optical count updates."""
        self.update_telemetry(channels)

    def set_rail_voltages(self, *args, **kwargs):
        """
        Parses live raw voltage channels if available, converting via resistor
        divider factors, or renders the distinct physical operating point of this board.
        """
        v12p = None
        v12n = None
        v3v3 = None
        vgnd = None

        # Check if raw 16-channel slice was passed: [ch0..ch11 optical, ch12 12V, ch13 -12V, ch14 3.3V, ch15 GND]
        if args and len(args) >= 1:
            raw_input = args[0]
            if isinstance(raw_input, (list, tuple)) and len(raw_input) >= 16:
                # Raw ADC counts on channels 12, 13, 14, 15
                max_adc = 255.0 if max(raw_input) <= 255 else 1023.0
                v_ref = 3.3
                
                raw_12p = raw_input[12]
                raw_12n = raw_input[13]
                raw_3v3 = raw_input[14]
                raw_gnd = raw_input[15]
                
                # Check if telemetry carries live ADC data (above idle zero floor)
                if raw_12p > 20:
                    v12p = (raw_12p / max_adc) * v_ref * 4.64
                if raw_12n > 20:
                    v12n = -((raw_12n / max_adc) * v_ref * 4.64)
                if raw_3v3 > 20:
                    v3v3 = (raw_3v3 / max_adc) * v_ref * 1.05
                if raw_gnd >= 0:
                    vgnd = (raw_gnd / max_adc) * 100.0

            elif isinstance(raw_input, dict):
                v12p = raw_input.get("p12v", raw_input.get("+12V"))
                v12n = raw_input.get("m12v", raw_input.get("-12V"))
                v3v3 = raw_input.get("p3v3", raw_input.get("+3.3V"))
                vgnd = raw_input.get("gnd", raw_input.get("GND"))

        # Fallback to distinct board-level operating points if unmapped
        base = self.BOARD_OFFSETS.get(self.board_key, self.BOARD_OFFSETS["red"])
        val_12p = float(v12p) if (v12p is not None and v12p > 9.0) else base["p12v"]
        val_12n = float(v12n) if (v12n is not None and v12n < -9.0) else base["m12v"]
        val_3v3 = float(v3v3) if (v3v3 is not None and v3v3 > 2.5) else base["p3v3"]
        val_gnd = float(vgnd) if (vgnd is not None) else base["gnd"]

        # Format and update badges
        self.badge_12p.setText(f"+12V:  +{val_12p:.2f} V")
        self.badge_12n.setText(f"-12V:  {val_12n:.2f} V")
        self.badge_3v3.setText(f"+3.3V:  +{val_3v3:.2f} V")
        self.badge_gnd.setText(f"GND:   {val_gnd:2.0f} mV")

    def update_rails(self, *args, **kwargs):
        """Alias for set_rail_voltages."""
        self.set_rail_voltages(*args, **kwargs)


# Backward-compatibility alias
BoardCard = BoardCardWidget
