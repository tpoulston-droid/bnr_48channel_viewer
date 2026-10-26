"""
src.main
App entry point and 48-channel 2x2 physical Hibou head layout.
"""
import os
import sys

STS_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"

# 1. Allow Python CLR / pythonnet to find managed assemblies
if STS_DIR not in sys.path:
    sys.path.append(STS_DIR)

# 2. Tell the Windows unmanaged loader where to find native sibling DLLs
if os.path.exists(STS_DIR) and hasattr(os, "add_dll_directory"):
    os.add_dll_directory(STS_DIR)
import os
import sys

# 1. Path to CPI STS Advance (where native BnrCtl32.dll, MeiUsb.dll, etc. live)
STS_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"
# 2. Path to your project root (where you placed BnrCtlDotNet40MeiReserved.dll)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

for path in (STS_DIR, PROJECT_ROOT):
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.append(path)
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(path)

# Now load the CLR reference
import clr
clr.AddReference("BnrCtlDotNet40MeiReserved")
import clr
clr.AddReference("BnrCtlDotNet40MeiReserved")

from Mei.Bnr import Bnr
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QGridLayout, QHBoxLayout, QPushButton, QLabel, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt

from src.widgets.board_card import BoardCardWidget
from src.workers.sweep_worker import SweepWorker
from src.core.workflow_runner import WorkflowRunner
from bnr_sdk.models import HibouHeadSnapshot

class Bnr48ChannelViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BNR Workbench — 48-Channel Optical Hibou Viewer")
        self.resize(1150, 720)

        self._init_ui()
        self.worker = None

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # Header Controls
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel("Hibou Optical Transmittance & Reflectance Matrix")
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #263238;")
        
        self.btn_sweep = QPushButton("Run Optical Sweep")
        self.btn_sweep.setFixedHeight(34)
        self.btn_sweep.setStyleSheet("""
            QPushButton {
                background-color: #1976D2; color: white; font-weight: bold;
                border-radius: 4px; padding: 4px 18px;
            }
            QPushButton:hover { background-color: #1565C0; }
            QPushButton:disabled { background-color: #90CAF9; }
        """)
        self.btn_sweep.clicked.connect(self._start_sweep)

        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_sweep)
        root_layout.addLayout(top_bar)

        # 2x2 Physical Orientation Grid:
        # [Roof/Top Inner] Red   | [Roof/Top Exit]   Blue
        # [Floor/Bot Inner] Black | [Floor/Bot Exit]  Green
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_red = BoardCardWidget("Red Upper Optical", start_ch=0, is_emitter_active=False)
        self.card_blue = BoardCardWidget("Blue Upper Exit", start_ch=32, is_emitter_active=True)
        self.card_black = BoardCardWidget("Black Lower Exit", start_ch=48, is_emitter_active=True)
        self.card_green = BoardCardWidget("Green Lower Optical", start_ch=16, is_emitter_active=False)

        grid.addWidget(self.card_red, 0, 0)
        grid.addWidget(self.card_blue, 0, 1)
        grid.addWidget(self.card_black, 1, 0)
        grid.addWidget(self.card_green, 1, 1)

        root_layout.addLayout(grid)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Connect BNR and click 'Run Optical Sweep'.")

    def _start_sweep(self):
        self.btn_sweep.setEnabled(False)
        self.worker = SweepWorker()
        self.worker.status_updated.connect(self.status_bar.showMessage)
        self.worker.sweep_complete.connect(self._on_sweep_complete)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.finished.connect(lambda: self.btn_sweep.setEnabled(True))
        self.worker.start()

    def _on_sweep_complete(self, snapshot: HibouHeadSnapshot):
        data = WorkflowRunner.extract_48_optical_channels(snapshot)
        self.card_red.set_counts(data["red"])
        self.card_green.set_counts(data["green"])
        self.card_blue.set_counts(data["blue"])
        self.card_black.set_counts(data["black"])
        self.status_bar.showMessage("Sweep populated successfully.")

    def _on_worker_error(self, err_msg: str):
        self.status_bar.showMessage(err_msg)
        QMessageBox.critical(self, "Hardware Error", err_msg)

    def _on_sweep_complete(self, snapshot: HibouHeadSnapshot):
            data = WorkflowRunner.parse_snapshot(snapshot)
            
            cards = {
                "red": self.card_red,
                "green": self.card_green,
                "blue": self.card_blue,
                "black": self.card_black,
            }

            for name, card in cards.items():
                b_data = data[name]
                card.set_optical_counts(b_data["optical"])
                card.set_rail_voltages(
                    v_plus12=b_data["rails"]["+12V"],
                    v_minus12=b_data["rails"]["-12V"],
                    v_plus33=b_data["rails"]["+3.3V"],
                    v_gnd=b_data["rails"]["GND"],
                )

            self.status_bar.showMessage("Sweep & Rail Diagnostic populated successfully.")

def main():
    app = QApplication(sys.argv)
    window = Bnr48ChannelViewer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()