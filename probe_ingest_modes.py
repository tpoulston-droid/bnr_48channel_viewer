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
bnr.Open()

print(f"[STATUS] DeviceStatus: {bnr.Status.DeviceStatus} ({int(bnr.Status.DeviceStatus)})")
print(f"[STATUS] TransportStatus: {bnr.Status.TransportStatus} ({int(bnr.Status.TransportStatus)})")

# Reset any hanging transaction
for op in ("CancelWaiting", "CashInRollback", "CashInEnd"):
    if hasattr(bnr, op):
        try: getattr(bnr, op)(); time.sleep(0.1)
        except Exception: pass

# 1. Inspect CashUnit status
print("\n--- Checking CashUnit Configuration ---")
cu = getattr(bnr, "CashUnit", None) or getattr(bnr, "get_CashUnit", lambda: None)()
print(f"CashUnit present: {cu is not None}")
if cu is not None:
    try:
        p_units = getattr(cu, "PhysicalCashUnits", None)
        l_units = getattr(cu, "LogicalCashUnits", None)
        print(f"  Physical units count: {len(list(p_units)) if p_units else 0}")
        print(f"  Logical units count: {len(list(l_units)) if l_units else 0}")
    except Exception as ex:
        print(f"  CashUnit inspection error: {ex}")

# 2. Test CashInStart overloads and variants
print("\n--- Testing CashInStart Variants ---")
for label, fn in [
    ("CashInStart()", lambda: bnr.CashInStart()),
    ("CashInStart(True)", lambda: bnr.CashInStart(System.Boolean(True))),
    ("CashInStart(False)", lambda: bnr.CashInStart(System.Boolean(False))),
]:
    try:
        res = fn()
        print(f"  {label} SUCCESS -> returned {res}")
        try: bnr.CashInRollback()
        except Exception: pass
        try: bnr.CashInEnd()
        except Exception: pass
        break
    except Exception as ex:
        print(f"  {label} FAILED -> {ex}")

# 3. Test Direct Transport / Bezel Commands
print("\n--- Testing Bezel / Ingestion Readiness ---")
for meth in ["SetBezel", "SetBezelState", "EnableBezel", "SetCashInLimit"]:
    if hasattr(bnr, meth):
        print(f"  Found method: {meth}")

# 4. Check for lower-level or diagnostic test methods on Bnr
print("\n--- Diagnostic / Mechanical Test Methods ---")
bnr_methods = [m.Name for m in clr.GetClrType(Bnr).GetMethods()]
intake_methods = [m for m in bnr_methods if any(k in m.lower() for k in ["accept", "inlet", "motor", "feed", "take", "coupon", "bill", "drive"])]
print(f"  Relevant methods: {intake_methods}")

bnr.Close()