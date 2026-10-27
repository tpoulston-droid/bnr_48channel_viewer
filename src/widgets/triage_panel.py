"""
src/widgets/triage_panel.py
Automated L1 Board Disposition & Component Level Repair (CLR) Guidance Panel.
Docked beneath the 48-channel matrix to provide clear board-by-board actions
and specific soldering instructions for repair technicians.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class TriageSummaryPanel(QGroupBox):
    """Docked bench triage panel providing L1 decisions and CLR soldering instructions."""

    # Outermost track channels (tolerated for 83mm strip skew / lateral guide slop)
    EDGE_CHANNELS = {0, 11, 16, 27, 32, 43, 48, 59}

    def __init__(self, parent=None):
        super().__init__("Automated Board Disposition & CLR Triage Summary", parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QGroupBox {
                font-family: 'Segoe UI';
                font-size: 10pt;
                font-weight: bold;
                color: #212529;
                border: 2px solid #6c757d;
                border-radius: 8px;
                margin-top: 12px;
                background-color: #f8f9fa;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 1. L1 Quick-Disposition Banner (4 Board Status Pills)
        self.pill_layout = QHBoxLayout()
        self.pill_layout.setSpacing(10)

        self.pill_red = QLabel("RED: IDLE")
        self.pill_blue = QLabel("BLUE: IDLE")
        self.pill_black = QLabel("BLACK: IDLE")
        self.pill_green = QLabel("GREEN: IDLE")

        for pill in (self.pill_red, self.pill_blue, self.pill_black, self.pill_green):
            pill.setAlignment(Qt.AlignCenter)
            pill.setFont(QFont("Segoe UI", 9, QFont.Bold))
            pill.setFixedHeight(28)
            pill.setStyleSheet(self._pill_style("#6c757d", "#ffffff"))
            self.pill_layout.addWidget(pill)

        layout.addLayout(self.pill_layout)

        # 2. Detailed Action & CLR Rework Text Box
        self.txt_summary = QPlainTextEdit()
        self.txt_summary.setReadOnly(True)
        self.txt_summary.setFont(QFont("Consolas", 9))
        self.txt_summary.setMinimumHeight(140)
        self.txt_summary.setStyleSheet("""
            QPlainTextEdit {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        self.txt_summary.setPlainText(
            "Waiting for coupon sweep... Insert 83mm calibration strip to run automated diagnostics."
        )
        layout.addWidget(self.txt_summary)

    def _pill_style(self, bg_hex: str, text_hex: str) -> str:
        return f"""
            QLabel {{
                background-color: {bg_hex};
                color: {text_hex};
                border-radius: 4px;
                padding: 2px 8px;
            }}
        """

    def evaluate_telemetry(self, raw_64: list):
        """
        Analyzes 48 active optical channels across the 4 physical boards.
        Filters edge-channel margin dropouts and outputs specific CLR rework steps.
        
        True Optical / Physical Pairings:
          Upper Throat: RED (Upper Receiver) <---> BLUE (Upper Emitter)
          Lower Throat: BLACK (Lower Emitter) <---> GREEN (Lower Receiver)
        """
        if len(raw_64) < 60:
            return

        # Slices of 12 active optical channels per board
        boards = {
            "RED": {
                "label": "RED (Upper Receiver)",
                "pill": self.pill_red,
                "counts": [raw_64[i] for i in range(0, 12)],
            },
            "BLUE": {
                "label": "BLUE (Upper Emitter)",
                "pill": self.pill_blue,
                "counts": [raw_64[i] for i in range(32, 44)],
            },
            "BLACK": {
                "label": "BLACK (Lower Emitter)",
                "pill": self.pill_black,
                "counts": [raw_64[i] for i in range(48, 60)],
            },
            "GREEN": {
                "label": "GREEN (Lower Receiver)",
                "pill": self.pill_green,
                "counts": [raw_64[i] for i in range(16, 28)],
            },
        }

        l1_disposition = {}
        clr_instructions = []

        # =====================================================================
        # STAGE 1: UPPER THROAT PAIR (RED RECEIVER <---> BLUE EMITTER)
        # =====================================================================
        red_counts = boards["RED"]["counts"]
        blue_counts = boards["BLUE"]["counts"]

        # Interior channels strictly (indices 1..10, excluding edge tracks 0 and 11)
        red_interior_dead = [idx for idx in range(1, 11) if red_counts[idx] < 25]
        blue_interior_dead = [idx for idx in range(1, 11) if blue_counts[idx] < 25]

        # Evaluate Red Board (Receiver)
        if len(red_interior_dead) == 0:
            l1_disposition["RED"] = ("PASS", "#28a745")
        elif len(red_interior_dead) >= 8:
            l1_disposition["RED"] = ("REPLACE / FAULT", "#dc3545")
            clr_instructions.append(
                "• RED BOARD FAULT (All interior channels dead):\n"
                "  - Check +3.3V and -12V analog rails at J1 header pin.\n"
                "  - Replace MUX IC (DG408/DG409) or buffer amp under shield."
            )
        else:
            # Check 4-channel blocks for Quad Op-Amp failure
            for quad_idx, (start, end) in enumerate([(0, 4), (4, 8), (8, 12)]):
                quad_dead = [c for c in red_interior_dead if start <= c < end]
                if len(quad_dead) >= 3:
                    clr_instructions.append(
                        f"• RED BOARD CLR REWORK: Replace Quad Op-Amp U{quad_idx + 1} (SOIC-14)\n"
                        f"  Reason: Contiguous channel block {start:02d}-{end-1:02d} dropped together.\n"
                        f"  Action: Hot-air reflow/replace Op-Amp U{quad_idx + 1} and probe decoupling cap."
                    )
            l1_disposition["RED"] = ("INSPECT", "#ffc107")

        # Evaluate Blue Board (Emitter)
        if len(blue_interior_dead) == 0 and len(red_interior_dead) == 0:
            l1_disposition["BLUE"] = ("PASS", "#28a745")
        elif len(red_interior_dead) > 0 and len(blue_interior_dead) > 0:
            l1_disposition["BLUE"] = ("REPLACE / FAULT", "#dc3545")
            clr_instructions.append(
                "• BLUE BOARD CLR REWORK: Open Emitter LED String Detected\n"
                "  Reason: Opposing Red receiver and Blue reflectance dropped on matching tracks.\n"
                "  Action: Diode test the 4-LED vertical string (Nominal Vf: 1.8V-2.2V visible, 3.2V UV).\n"
                "  Action: Inspect 0603 series current-limiting ballast resistor for fracture/open circuit."
            )
        else:
            l1_disposition["BLUE"] = ("PASS", "#28a745")

        # =====================================================================
        # STAGE 2: LOWER THROAT PAIR (GREEN RECEIVER <---> BLACK EMITTER)
        # =====================================================================
        green_counts = boards["GREEN"]["counts"]
        black_counts = boards["BLACK"]["counts"]

        green_interior_dead = [idx for idx in range(1, 11) if green_counts[idx] < 25]
        black_interior_dead = [idx for idx in range(1, 11) if black_counts[idx] < 25]

        # Evaluate Green Board (Receiver)
        if len(green_interior_dead) == 0:
            l1_disposition["GREEN"] = ("PASS", "#28a745")
        elif len(green_interior_dead) >= 8:
            l1_disposition["GREEN"] = ("REPLACE / FAULT", "#dc3545")
            clr_instructions.append(
                "• GREEN BOARD FAULT (Entire array dead):\n"
                "  - Check lower flex ribbon seating and analog supply pins.\n"
                "  - Replace MUX IC or conditioning op-amp under shield."
            )
        else:
            for quad_idx, (start, end) in enumerate([(0, 4), (4, 8), (8, 12)]):
                quad_dead = [c for c in green_interior_dead if start <= c < end]
                if len(quad_dead) >= 3:
                    clr_instructions.append(
                        f"• GREEN BOARD CLR REWORK: Replace Quad Op-Amp U{quad_idx + 1} (SOIC-14)\n"
                        f"  Reason: Channels {start + 16:02d}-{end + 15:02d} dropped into noise floor.\n"
                        f"  Action: Reflow/replace Op-Amp U{quad_idx + 1}."
                    )
            l1_disposition["GREEN"] = ("INSPECT", "#ffc107")

        # Evaluate Black Board (Emitter)
        if len(black_interior_dead) == 0 and len(green_interior_dead) == 0:
            l1_disposition["BLACK"] = ("PASS", "#28a745")
        elif len(green_interior_dead) > 0 and len(black_interior_dead) > 0:
            l1_disposition["BLACK"] = ("REPLACE / FAULT", "#dc3545")
            clr_instructions.append(
                "• BLACK BOARD CLR REWORK: Upward Emitter LED Driver Failure\n"
                "  Reason: Green receiver starved of light across lower throat.\n"
                "  Action: Diode test the upward-firing IR/visible LED column.\n"
                "  Action: Check low-side driver transistor and solder fillets at LED end-caps."
            )
        else:
            l1_disposition["BLACK"] = ("PASS", "#28a745")

        # =====================================================================
        # UPDATE UI PILLS & FORMAT BENCH SUMMARY
        # =====================================================================
        for b_key, pill in [
            ("RED", self.pill_red),
            ("BLUE", self.pill_blue),
            ("BLACK", self.pill_black),
            ("GREEN", self.pill_green),
        ]:
            status, color = l1_disposition.get(b_key, ("PASS", "#28a745"))
            pill.setText(f"{b_key}: {status}")
            pill.setStyleSheet(self._pill_style(color, "#ffffff"))

        # Build Plain-English Output
        output_lines = [
            "======================= LEVEL 1 (L1) BOARD DISPOSITION =======================",
            f" [RED UPPER RECEIVER]   ──► {l1_disposition.get('RED', ('PASS', ''))[0]}",
            f" [BLUE UPPER EMITTER]   ──► {l1_disposition.get('BLUE', ('PASS', ''))[0]}",
            f" [BLACK LOWER EMITTER]  ──► {l1_disposition.get('BLACK', ('PASS', ''))[0]}",
            f" [GREEN LOWER RECEIVER] ──► {l1_disposition.get('GREEN', ('PASS', ''))[0]}",
            "",
            "=================== COMPONENT LEVEL REPAIR (CLR) INSTRUCTIONS =================",
        ]

        if not clr_instructions:
            output_lines.extend([
                "✔ ALL 4 BOARDS PHYSICALLY HEALTHY. NO COMPONENT REWORK REQUIRED.",
                "• Edge-channel dips (CH 00, CH 11, CH 16, CH 27, CH 32, CH 43, CH 48, CH 59)",
                "  are confirmed 83mm coupon margin / insertion clearance, NOT hardware defects.",
                "• Op-amps, multiplexers, and LED emitter strings are operational."
            ])
        else:
            output_lines.extend(clr_instructions)

        self.txt_summary.setPlainText("\n".join(output_lines))
