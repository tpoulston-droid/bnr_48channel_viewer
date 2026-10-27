"""
src/main.py
48-Channel Optical Hibou Viewer for Crane BNR.
Features:
  - 4-Board 2x2 Transverse Matrix (Red, Blue, Black, Green)
  - Supervisory Power Rail Badges (+12V, -12V, +3.3V, GND)
  - Docked Automated Board Disposition & CLR Soldering Instructions Panel
  - CustomOffsetCompensator with SizeCheckAlgo validation
"""

import sys
import os
import struct

# Enforce 32-bit (x86) execution architecture
if struct.calcsize("P") * 8 != 32:
    raise EnvironmentError("Requires 32-bit (x86) Python environment.")

# Ensure project root is in sys.path so bnr_sdk is directly importable
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from bnr_sdk.client import BnrClient
from bnr_sdk.compensator import CustomOffsetCompensator
from widgets.board_card import BoardCardWidget
from widgets.triage_panel import TriageSummaryPanel


class OpticalSweepWorker(QThread):
    sweep_completed = pyqtSignal(object)
    sweep_failed = pyqtSignal(str)

    def __init__(self, client: BnrClient):
        super().__init__()
        self.client = client

    def run(self):
        try:
            snapshot = self.client.run_optical_sweep("USD")
            self.sweep_completed.emit(snapshot)
        except Exception as ex:
            self.sweep_failed.emit(str(ex))


class Bnr48ChannelViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BNR Workbench — 48-Channel Optical Hibou Viewer")
        self.resize(1140, 860)

        self.client = None
        self.compensator = CustomOffsetCompensator(target_count=200)

        self._init_client()
        self._init_ui()

    def _init_client(self):
        try:
            self.client = BnrClient()
            self.client.connect()
        except Exception as ex:
            print(f"[INIT WARNING] Could not auto-connect BNR: {ex}")

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Top Header Bar
        top_bar = QHBoxLayout()
        lbl_title = QLabel("Hibou Optical Transmittance & Reflectance Matrix")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_title.setStyleSheet("color: #212529;")
        top_bar.addWidget(lbl_title)

        top_bar.addStretch()

        self.btn_sweep = QPushButton("Run Optical Sweep")
        self.btn_sweep.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_sweep.setFixedHeight(34)
        self.btn_sweep.setFixedWidth(160)
        self.btn_sweep.setStyleSheet("""
            QPushButton {
                background-color: #0b5ed7;
                color: #ffffff;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #0a58ca;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.btn_sweep.clicked.connect(self._run_sweep)
        top_bar.addWidget(self.btn_sweep)
        main_layout.addLayout(top_bar)

        # 2. 2x2 Matrix of Board Cards
        grid = QGridLayout()
        grid.setSpacing(10)

        # Row 0: Upper Throat (Red & Blue)
        self.card_red = BoardCardWidget("Red Upper Optical", start_ch=0, is_emitter_active=False)
        self.card_blue = BoardCardWidget("Blue Upper Exit", start_ch=32, is_emitter_active=True)

        # Row 1: Lower Throat (Black & Green)
        self.card_black = BoardCardWidget("Black Lower Exit", start_ch=48, is_emitter_active=True)
        self.card_green = BoardCardWidget("Green Lower Optical", start_ch=16, is_emitter_active=False)

        grid.addWidget(self.card_red, 0, 0)
        grid.addWidget(self.card_blue, 0, 1)
        grid.addWidget(self.card_black, 1, 0)
        grid.addWidget(self.card_green, 1, 1)
        main_layout.addLayout(grid)

        # 3. Docked Automated Disposition & CLR Soldering Instructions Panel
        self.triage_panel = TriageSummaryPanel()
        main_layout.addWidget(self.triage_panel)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Click 'Run Optical Sweep' and insert 83mm calibration strip.")

    def _run_sweep(self):
        self.btn_sweep.setEnabled(False)
        self.status_bar.showMessage("Arming mouth... Feed calibration strip into bezel now!")

        if not self.client:
            self._init_client()

        self.worker = OpticalSweepWorker(self.client)
        self.worker.sweep_completed.connect(self._on_sweep_complete)
        self.worker.sweep_failed.connect(self._on_sweep_failed)
        self.worker.start()

    def _on_sweep_complete(self, snapshot):
        self.btn_sweep.setEnabled(True)

        # Raw 64-element array from the BNR telemetry
        raw_64 = [ch.raw_ad_count for ch in snapshot.channels]
        if len(raw_64) < 64:
            raw_64.extend([0] * (64 - len(raw_64)))

        # 1. Query Hardware SizeCheck via decompiled structures
        bnr_instance = getattr(self.client, "bnr_driver", None) or getattr(self.client, "_bnr", None)
        w_mm, l_mm, status_str = (None, None, "Unavailable")
        if bnr_instance:
            w_mm, l_mm, status_str = self.compensator.parse_size_check(bnr_instance)

        # 2. Offset & Vignette Compensation
        if not self.compensator.is_calibrated:
            self.compensator.calibrate_with_coupon(raw_64)

        display_counts = self.compensator.apply_compensation(raw_64)

        # 3. Update the 4 Board Cards with compensated display counts
        self.card_red.set_optical_counts(display_counts[0:12])
        self.card_green.set_optical_counts(display_counts[16:28])
        self.card_blue.set_optical_counts(display_counts[32:44])
        self.card_black.set_optical_counts(display_counts[48:60])

        # 4. Update Board Power Rails
        self.card_red.set_rail_voltages(raw_64[0:16])
        self.card_green.set_rail_voltages(raw_64[16:32])
        self.card_blue.set_rail_voltages(raw_64[32:48])
        self.card_black.set_rail_voltages(raw_64[48:64])

        # 5. Evaluate Automated L1 Triage & CLR Soldering Instructions
        self.triage_panel.evaluate_telemetry(raw_64)

        # 6. Status Bar Update
        if w_mm:
            self.status_bar.showMessage(
                f"Sweep complete. Media: {w_mm:.1f} mm W x {l_mm:.1f} mm L [{status_str}]. Compensation applied."
            )
        else:
            self.status_bar.showMessage("Sweep complete. Software offset compensation applied.")

    def _on_sweep_failed(self, error_msg: str):
        self.btn_sweep.setEnabled(True)
        self.status_bar.showMessage(f"Sweep error: {error_msg}")
        print(f"[SWEEP ERROR] {error_msg}")


def main():
    app = QApplication(sys.argv)
    window = Bnr48ChannelViewer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
