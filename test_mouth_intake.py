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
print("[1] Opening BNR driver...")
bnr.Open()

# 1. Teardown any leftover session from the previous run
for fn in ("CancelWaiting", "CashInRollback", "CashInEnd"):
    if hasattr(bnr, fn):
        try:
            getattr(bnr, fn)()
            time.sleep(0.2)
        except Exception:
            pass

# 2. Wait for mechanical homing to settle so BNR is no longer Busy
print("[2] Waiting for transport to finish homing...")
for attempt in range(25):
    try:
        st = bnr.Status
        dev_st = int(st.DeviceStatus)
        trans_st = int(st.TransportStatus)
        if dev_st in (6180, 0) and trans_st in (6203, 0):
            print(f"    BNR is ready and idle ({dev_st}, {trans_st})")
            break
    except Exception:
        pass
    time.sleep(0.3)

# 3. Query CashUnit with retry to satisfy the XFS state machine
print("[3] Querying CashUnit configuration...")
cu = None
for _ in range(10):
    try:
        cu = bnr.CashUnit
        if cu is not None:
            print("    CashUnit configuration confirmed.")
            break
    except Exception as ex:
        if "Busy" in str(ex):
            time.sleep(0.4)
        else:
            break

# 4. Arm Cash-In Session
print("[4] Calling CashInStart()...")
res_start = bnr.CashInStart()
print(f"    CashInStart returned: {res_start}")

# 5. Hold mouth open for coupon insertion
print("\n[5] MOUTH IS ACTIVE!")
print("    >>> PUSH CALIBRATION STRIP OR $1 BILL INTO BEZEL MOUTH NOW <<<")

start_time = time.time()
timeout_sec = 20.0
completed_code = None

while (time.time() - start_time) < timeout_sec:
    try:
        res = bnr.CashIn("USD")
        
        # 32 = Note entering inlet mouth / breaking entrance sensors
        if res == 32:
            print("    [EVENT] Bill detected! Drawing across Hibou heads...")
            time.sleep(0.6)
            continue

        # Terminal codes: 1024 (non-currency/coupon reject), 0, 2048, 8192
        if res in (1024, 0, 2048, 8192, 32768, 1):
            completed_code = res
            print(f"    [EVENT] Traversal finished with code: {res}")
            break

    except Exception as ex:
        # If bill is actively pulling across the heads, ignore transient busy
        time.sleep(0.2)

    elapsed = int(time.time() - start_time)
    if elapsed > 0 and elapsed % 4 == 0:
        print(f"    ...listening for insertion ({timeout_sec - elapsed:.0f}s left)")
        time.sleep(0.8)

    time.sleep(0.25)

time.sleep(0.5)

# 6. Read both optical heads (Head 0: Sig 1, Head 1: Sig 2)
print("\n[6] Optical Head Telemetry Readout:")
try:
    sig1 = list(bnr.GetSignature(System.UInt32(1)))
    sig2 = list(bnr.GetSignature(System.UInt32(2)))
    print(f"    Head 0 (Sig 1 - Red/Black): non-zero={sum(1 for x in sig1 if x > 0)}/32 | sample: {sig1[:8]}")
    print(f"    Head 1 (Sig 2 - Green/Blue): non-zero={sum(1 for x in sig2 if x > 0)}/32 | sample: {sig2[:8]}")
except Exception as ex:
    print(f"    Signature readout error: {ex}")

# 7. Eject note/strip and close session
try:
    bnr.CashInRollback()
except Exception:
    try:
        bnr.CashInEnd()
    except Exception:
        pass

bnr.Close()
print("[7] Session closed cleanly.")