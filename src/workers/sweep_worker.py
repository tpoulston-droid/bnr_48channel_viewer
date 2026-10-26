"""
src.workers.sweep_worker
Background QThread for WinUSB connection and Hibou sweep polling.
"""
from PyQt5.QtCore import QThread, pyqtSignal
from bnr_sdk.client import BnrClient
from bnr_sdk.models import HibouHeadSnapshot
from bnr_sdk.exceptions import BnrError

class SweepWorker(QThread):
    sweep_complete = pyqtSignal(HibouHeadSnapshot)
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True

    def run(self):
        self.status_updated.emit("Binding WinUSB & applying MEI_RESERVED...")
        try:
            with BnrClient() as client:
                self.status_updated.emit("BNR ready. Running optical coupon sweep...")
                snapshot = client.run_optical_sweep()
                self.sweep_complete.emit(snapshot)
                self.status_updated.emit("Sweep complete.")
        except BnrError as ex:
            self.error_occurred.emit(f"SDK Error: {str(ex)}")
        except Exception as ex:
            self.error_occurred.emit(f"System Error: {str(ex)}")

    def stop(self):
        self._is_running = False