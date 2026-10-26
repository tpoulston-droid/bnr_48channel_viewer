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
from System.Reflection import Assembly

asm = Assembly.Load("BnrCtlDotNet40MeiReserved")

bnr = Bnr()
bnr.Open()

print("=== Checking Bnr properties for MainModule / Measures ===")
for member in dir(bnr):
    m_lower = member.lower()
    if any(k in m_lower for k in ["measure", "mainmodule", "calibration", "recognition", "data"]):
        try:
            val = getattr(bnr, member)
            val_type = type(val).__name__ if val is not None else "None"
            print(f"  bnr.{member}: {val_type}")
        except Exception as ex:
            print(f"  bnr.{member}: (error: {ex})")

bnr.Close()