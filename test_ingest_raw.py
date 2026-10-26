import os
import sys
import time

STS_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"
if os.path.exists(STS_DIR):
    sys.path.append(STS_DIR)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(STS_DIR)

import clr
clr.AddReference("BnrCtlDotNet40MeiReserved")
from Mei.Bnr import Bnr
import System

bnr = Bnr()
print("[1] Opening Bnr handle...")
bnr.Open()

# Print starting status
st = bnr.Status
print(f"[2] DeviceStatus: {st.DeviceStatus} ({int(st.DeviceStatus)}), TransportStatus: {st.TransportStatus} ({int(st.TransportStatus)})")

# Reset any stale commands
for op in ("CancelWaiting", "CashInRollback", "CashInEnd"):
    if hasattr(bnr, op):
        try:
            getattr(bnr, op)()
            time.sleep(0.2)
        except Exception:
            pass

print("\n[3] Calling CashInStart(True)...")
try:
    ret_start = bnr.CashInStart(System.Boolean(True))
    print(f"    CashInStart returned: {ret_start}")
except Exception as ex:
    print(f"    CashInStart Exception: {ex}")

print("\n[4] Waiting 2 seconds for bezel LED to illuminate...")
time.sleep(2.0)

print("\n[5] Calling CashIn('USD')...")
print("    >>> PUSH CALIBRATION STRIP OR $1 BILL INTO THE INLET NOW <<<")
try:
    ret_cashin = bnr.CashIn("USD")
    print(f"    CashIn returned: {ret_cashin}")
except Exception as ex:
    print(f"    CashIn Exception: {ex}")

print("\n[6] Checking Signatures...")
try:
    sig0 = list(bnr.GetSignature(0))
    print(f"    GetSignature(0) len: {len(sig0)}, non-zero count: {sum(1 for x in sig0 if x > 0)}")
    print(f"    First 8 values: {sig0[:8]}")
except Exception as ex:
    print(f"    GetSignature(0) error: {ex}")

try:
    sig1 = list(bnr.GetSignature(1))
    print(f"    GetSignature(1) len: {len(sig1)}, non-zero count: {sum(1 for x in sig1 if x > 0)}")
    print(f"    First 8 values: {sig1[:8]}")
except Exception as ex:
    print(f"    GetSignature(1) error: {ex}")

# Eject/rollback note to release mouth
try:
    bnr.CashInRollback()
except Exception:
    pass

bnr.Close()
print("[7] Complete.")