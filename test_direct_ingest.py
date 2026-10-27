import os
import sys
import time

CPI_BIN_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"
if os.path.exists(CPI_BIN_DIR):
    sys.path.append(CPI_BIN_DIR)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(CPI_BIN_DIR)

import clr
clr.AddReference("BnrCtlDotNet40MeiReserved")
from Mei.Bnr import Bnr
import System

bnr = Bnr()
print("[1] Opening BNR driver...")
bnr.Open()

# 1. Check Device & Transport States
st = bnr.Status
print(f"[2] Initial State -> DeviceStatus: {st.DeviceStatus} ({int(st.DeviceStatus)}), Transport: {st.TransportStatus} ({int(st.TransportStatus)})")

if int(st.DeviceStatus) == 6179:  # OffLine
    print("    [!] Transport is OffLine. Issuing Reset()...")
    bnr.Reset()

# 2. Wait until Transport is fully idle and not Busy
print("[3] Waiting for transport to become IDLE and not Busy...")
for sec in range(25):
    try:
        st = bnr.Status
        d_st = int(st.DeviceStatus)
        t_st = int(st.TransportStatus)
        if d_st == 6180:  # OnLine
            # TransportStatus 6203 is Ok/Idle
            print(f"    ✔ Transport is OnLine ({d_st}) and ready ({t_st})")
            break
    except Exception:
        pass
    time.sleep(1.0)

# 3. Clean up lingering transaction states (safely)
for fn in ("CashInRollback", "CashInEnd", "CancelWaiting"):
    if hasattr(bnr, fn):
        try:
            getattr(bnr, fn)()
            time.sleep(0.1)
        except Exception:
            pass

# Give transport 1 second to settle after rollback
time.sleep(1.0)

# 4. Safely check / query CashUnit (with retry against Busy)
print("[4] Checking CashUnit configuration...")
cu_loaded = False
for attempt in range(15):
    try:
        cu = bnr.CashUnit
        if cu is not None:
            cu_loaded = True
            print("    ✔ CashUnit state verified.")
            break
    except Exception as ex:
        time.sleep(0.6)

if not cu_loaded:
    print("    [!] CashUnit check deferred (Device still cycling), continuing to CashInStart...")

# 5. Start CashIn Session (Handle CashInActive if already armed)
print("\n[5] Arming CashInStart()...")
res_start = None
for attempt in range(4):
    try:
        res_start = bnr.CashInStart()
        print(f"    ✔ CashInStart returned: {res_start}")
        break
    except Exception as ex:
        err_msg = str(ex)
        if "CashInActive" in err_msg:
            print("    [!] CashInActive lock detected. Forcing CashInRollback() to free session...")
            try:
                bnr.CashInRollback()
            except Exception:
                try:
                    bnr.CashInEnd()
                except Exception:
                    pass
            time.sleep(0.8)
        else:
            time.sleep(0.6)

# 6. Continuous Ingestion Loop
print("\n[6] MOUTH IS ARMED! YOU HAVE 25 SECONDS.")
print("    >>> PUSH 83mm CALIBRATION STRIP OR $1 BILL INTO BEZEL NOW <<<")

t0 = time.time()
timeout_sec = 25.0
media_inserted = False

while (time.time() - t0) < timeout_sec:
    try:
        rc = bnr.CashIn("USD")

        # Event 32 = paper detected entering mouth
        if rc == 32:
            print("    [EVENT] Paper detected! Motor M1 pulling coupon across Hibou...")
            media_inserted = True
            time.sleep(0.8)
            break

    except Exception:
        time.sleep(0.15)

    elapsed = int(time.time() - t0)
    if elapsed > 0 and elapsed % 4 == 0:
        print(f"    ...waiting for paper insertion ({int(timeout_sec - elapsed)}s remaining)")
        time.sleep(0.7)

    time.sleep(0.15)

if media_inserted:
    print("    Waiting for physical sweep pass to clear transport...")
    time.sleep(1.2)
else:
    print("\n[TIMEOUT] No paper inserted.")

# 7. Extract Signatures
try:
    sig1 = list(bnr.GetSignature(System.UInt32(1)))
    sig2 = list(bnr.GetSignature(System.UInt32(2)))
    print(f"\n[7] Post-Pass Signatures:")
    print(f"    Inner Head (Sig 1): {sum(1 for x in sig1 if x > 0)}/32 non-zero | First 8: {sig1[:8]}")
    print(f"    Outer Head (Sig 2): {sum(1 for x in sig2 if x > 0)}/32 non-zero | First 8: {sig2[:8]}")
except Exception as ex:
    print(f"\n[7] Signature readout notice: {ex}")

# 8. Eject and close session
try:
    bnr.CashInRollback()
except Exception:
    try:
        bnr.CashInEnd()
    except Exception:
        pass

bnr.Close()
print("[8] Session closed cleanly.")
