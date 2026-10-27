"""
bnr_sdk/client.py
BNR hardware client wrapping BnrCtlDotNet40MeiReserved.dll with proven
intake motor triggering, optical signature capture, and robust DLL path resolution.
"""

import os
import sys
import time

CPI_BIN_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"
if os.path.exists(CPI_BIN_DIR) and CPI_BIN_DIR not in sys.path:
    sys.path.append(CPI_BIN_DIR)

if hasattr(os, "add_dll_directory") and os.path.exists(CPI_BIN_DIR):
    try:
        os.add_dll_directory(CPI_BIN_DIR)
    except Exception:
        pass

import clr

DLL_PATH = os.path.join(CPI_BIN_DIR, "BnrCtlDotNet40MeiReserved.dll")
if os.path.exists(DLL_PATH):
    clr.AddReference(DLL_PATH)
else:
    clr.AddReference("BnrCtlDotNet40MeiReserved")

from Mei.Bnr import Bnr
import System
from bnr_sdk.models import OpticalSnapshot, OpticalChannel


class BnrClient:
    def __init__(self):
        self.bnr = Bnr()
        self.connected = False

    @property
    def bnr_driver(self):
        return self.bnr

    def connect(self):
        """Binds the WinUSB communication pipe and applies factory access."""
        try:
            print("[BNR] Opening USB communication pipe via Bnr.Open()...")
            self.bnr.Open()
            self.connected = True
            print("[BNR] WinUSB pipe successfully opened.")
        except Exception as ex:
            if "AlreadyOpen" not in str(ex):
                print(f"[BNR WARN] Bnr.Open() notice: {ex}")

        try:
            self.bnr.SetFactoryAccessKey("MEI_RESERVED")
        except Exception:
            pass

        return True

    def run_optical_sweep(self, currency="USD", timeout_sec=25) -> OpticalSnapshot:
        """
        Executes a live optical sweep:
        1. Checks transport state and clears any leftover locks.
        2. Satisfies XFS CashUnit state requirement.
        3. Arms CashInStart() and listens for media insertion.
        4. Extracts post-pass 64-channel array and feeds it to UI & triage engine.
        """
        try:
            self.bnr.Open()
        except Exception:
            pass

        # 1. Bring device OnLine if OffLine
        try:
            st = self.bnr.Status
            if int(st.DeviceStatus) == 6179:
                print("[BNR] Transport is OffLine. Issuing Reset()...")
                self.bnr.Reset()
                for _ in range(25):
                    time.sleep(1.0)
                    if int(self.bnr.Status.DeviceStatus) == 6180:
                        break
        except Exception:
            pass

        # 2. Safely query CashUnit (XFS prerequisite)
        print("[BNR] Checking CashUnit configuration...")
        for _ in range(12):
            try:
                cu = self.bnr.CashUnit
                if cu is not None:
                    print("[BNR] ✔ CashUnit state verified.")
                    break
            except Exception:
                time.sleep(0.5)

        # 3. Clean up lingering transaction states
        for fn in ("CashInRollback", "CashInEnd", "CancelWaiting"):
            if hasattr(self.bnr, fn):
                try:
                    getattr(self.bnr, fn)()
                    time.sleep(0.08)
                except Exception:
                    pass

        # 4. Start Cash-In Session
        print("[BNR] Arming CashInStart()...")
        res_start = None
        for _ in range(4):
            try:
                res_start = self.bnr.CashInStart()
                print(f"[BNR] ✔ CashInStart returned: {res_start}")
                break
            except Exception as ex:
                if "CashInActive" in str(ex):
                    try:
                        self.bnr.CashInRollback()
                    except Exception:
                        pass
                    time.sleep(0.6)
                else:
                    time.sleep(0.5)

        # 5. Continuous Ingestion Loop (Catches both 32 and terminal codes)
        print("\n[BNR] >>> BEZEL ACTIVE: INSERT 83mm CALIBRATION STRIP NOW <<<")
        t0 = time.time()
        media_inserted = False

        while (time.time() - t0) < timeout_sec:
            try:
                rc = self.bnr.CashIn(currency)

                # Event 32 = paper entering mouth
                if rc == 32:
                    print("    [EVENT] Paper detected! Motor M1 engaged — pulling coupon...")
                    media_inserted = True
                    time.sleep(0.8)
                    break

                # If pass finished immediately (code 1024 coupon reject, 2048 calib, 8192 snapshot, 1)
                if rc in (1024, 2048, 8192, 1):
                    print(f"    [EVENT] Coupon sweep finished with code: {rc}")
                    media_inserted = True
                    break

            except Exception:
                time.sleep(0.15)

            elapsed = int(time.time() - t0)
            if elapsed > 0 and elapsed % 4 == 0:
                time.sleep(0.7)

            time.sleep(0.15)

        # Allow mechanical travel to settle across Hibou heads
        time.sleep(0.8)

        # 6. Extract Signatures
        sig1 = []
        sig2 = []
        try:
            sig1 = list(self.bnr.GetSignature(System.UInt32(1)))
        except Exception:
            try:
                sig1 = list(self.bnr.GetSignature(1))
            except Exception:
                pass

        try:
            sig2 = list(self.bnr.GetSignature(System.UInt32(2)))
        except Exception:
            try:
                sig2 = list(self.bnr.GetSignature(2))
            except Exception:
                pass

        print(f"[SDK DIAG] Inner Head (Sig 1): {len(sig1)} counts | Non-zero: {sum(1 for x in sig1 if x > 0)}/32")
        print(f"[SDK DIAG] Outer Head (Sig 2): {len(sig2)} counts | Non-zero: {sum(1 for x in sig2 if x > 0)}/32")

        raw_64 = sig1 + sig2
        if len(raw_64) < 64:
            raw_64.extend([0] * (64 - len(raw_64)))

        # 7. Eject coupon and close session
        try:
            self.bnr.CashInRollback()
        except Exception:
            try:
                self.bnr.CashInEnd()
            except Exception:
                pass

        channels = [
            OpticalChannel(
                channel_index=i,
                raw_ad_count=raw_64[i],
                board_group="RED" if i < 12 else ("GREEN" if i < 28 else ("BLUE" if i < 44 else "BLACK")),
                track_type="TRANSMISSIVE" if i < 28 else "REFLECTIVE",
            )
            for i in range(len(raw_64))
        ]
        return OpticalSnapshot(channels=channels)
