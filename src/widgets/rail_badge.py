"""
src.widgets.rail_badge
Compact pill badge component indicating telemetry rail health (+12V, -12V, 3.3V, GND).
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel

class RailBadge(QFrame):
    # Nominal voltage thresholds & acceptable windows
    SPECS = {
        "+12V": {"nominal": 12.0, "warn_low": 10.8, "warn_high": 13.2, "ok_low": 11.4, "ok_high": 12.6},
        "-12V": {"nominal": -12.0, "warn_low": -13.2, "warn_high": -10.5, "ok_low": -12.6, "ok_high": -11.4},
        "+3.3V": {"nominal": 3.30, "warn_low": 3.00, "warn_high": 3.60, "ok_low": 3.15, "ok_high": 3.45},
        "GND":  {"nominal": 0.0, "warn_high": 0.050, "ok_high": 0.020},  # Units in V (e.g. 20mV nominal)
    }

    def __init__(self, rail_name: str, parent=None):
        super().__init__(parent)
        self.rail_name = rail_name
        self.spec = self.SPECS.get(rail_name, {})

        self.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        self.lbl_name = QLabel(f"<b>{self.rail_name}:</b>")
        self.lbl_name.setStyleSheet("font-size: 10px;")

        self.lbl_val = QLabel("-- V")
        self.lbl_val.setStyleSheet("font-size: 10px; font-weight: bold;")

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.lbl_val)

        self._set_style("gray")

    def update_voltage(self, voltage: float):
        """Updates reading and classifies state into NOMINAL (green), WARN (amber), or FAULT (red)."""
        state = self._classify(voltage)

        if self.rail_name == "GND":
            self.lbl_val.setText(f"{voltage * 1000.0:.0f} mV")
        else:
            self.lbl_val.setText(f"{voltage:+.2f} V")

        self._set_style(state)

    def _classify(self, val: float) -> str:
        if not self.spec:
            return "nominal"

        if self.rail_name == "GND":
            if abs(val) <= self.spec["ok_high"]:
                return "nominal"
            elif abs(val) <= self.spec["warn_high"]:
                return "warn"
            return "fault"

        # Bipolar and positive rails
        ok_l, ok_h = self.spec["ok_low"], self.spec["ok_high"]
        warn_l, warn_h = self.spec["warn_low"], self.spec["warn_high"]

        if ok_l <= val <= ok_h:
            return "nominal"
        elif warn_l <= val <= warn_h:
            return "warn"
        return "fault"

    def _set_style(self, state: str):
        colors = {
            "nominal": ("#E8F5E9", "#2E7D32", "#A5D6A7"),  # Soft green bg, dark green text, border
            "warn":    ("#FFF9C4", "#F57F17", "#FFF176"),  # Soft yellow bg, dark yellow text, border
            "fault":   ("#FFEBEE", "#C62828", "#EF9A9A"),  # Soft red bg, dark red text, border
            "gray":    ("#ECEFF1", "#546E7A", "#CFD8DC"),  # Default standby
        }
        bg, fg, border = colors.get(state, colors["gray"])
        self.setStyleSheet(f"""
            RailBadge {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QLabel {{
                color: {fg};
            }}
        """)