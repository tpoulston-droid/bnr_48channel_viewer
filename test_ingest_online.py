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

bnr = Bnr()
print("[1] Opening driver...")
bnr.Open()

print(f"[2] Initial State -> DeviceStatus: {bnr.Status.DeviceStatus} ({int(bnr.Status.DeviceStatus)})")

# If OffLine (6179), run SelfTest / Reset to bring it OnLine (6180)
if int(bnr.Status.DeviceStatus) == 6179:
    print("[3] Device is OffLine. Performing Reset to bring OnLine...")
    try:
        bnr.Reset()
        time.sleep(3.0)
    except Exception as ex:
        print(f"    Reset notice: {ex}")

# Wait for OnLine
for _ in range(20):
    st = bnr.Status
    if int(st.DeviceStatus) == 6180:
        print(f"[4] Device is now ONLINE ({st.DeviceStatus})!")
        break
    time.sleep(0.5)

print("[5] Arming CashInStart()...")
try:
    ret_start = bnr.CashInStart()
    print(f"    CashInStart returned: {ret_start}")
except Exception as ex:
    print(f"    CashInStart error: {ex}")

print("\n[6] Calling CashIn('USD')...")
print("    >>> PUSH CALIBRATION STRIP OR $1 BILL INTO THE INLET NOW <<<")
try:
    ret_cashin = bnr.CashIn("USD")
    print(f"    CashIn completed with result: {ret_cashin}")
except Exception as ex:
    print(f"    CashIn error: {ex}")

# Rollback
try:
    bnr.CashInRollback()
except Exception:
    pass

bnr.Close()
print("[7] Done.")