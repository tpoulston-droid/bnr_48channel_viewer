import os
import sys

STS_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"
if os.path.exists(STS_DIR):
    sys.path.append(STS_DIR)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(STS_DIR)

import clr
clr.AddReference("BnrCtlDotNet40MeiReserved")
from Mei.Bnr import Bnr

bnr = Bnr()
bnr.Open()

mm = bnr.MainModule
print("=== MainModule Properties & Methods ===")
props = [p for p in dir(mm) if not p.startswith("_")]
for p in props:
    try:
        val = getattr(mm, p)
        val_str = str(val)
        if len(val_str) > 60:
            val_str = val_str[:60] + "..."
        print(f"  mm.{p}: {type(val).__name__} = {val_str}")
    except Exception as ex:
        print(f"  mm.{p}: (error reading: {ex})")

bnr.Close()