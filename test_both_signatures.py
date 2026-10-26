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
import System

bnr = Bnr()
bnr.Open()

# Head 0 (Inner Hibou: Red & Black) = GetSignature(1)
sig_inner = list(bnr.GetSignature(System.UInt32(1)))
# Head 1 (Outer Hibou: Blue & Green) = GetSignature(2)
sig_outer = list(bnr.GetSignature(System.UInt32(2)))

print(f"Inner Head (Head 0 / Sig 1): len={len(sig_inner)}, non-zeros={sum(1 for x in sig_inner if x > 0)}")
print(f"  Red Board  (00-11): {sig_inner[:12]}")
print(f"  Black Board (48-59): {sig_inner[16:28]}")

print(f"\nOuter Head (Head 1 / Sig 2): len={len(sig_outer)}, non-zeros={sum(1 for x in sig_outer if x > 0)}")
print(f"  Green Board (16-27): {sig_outer[:12]}")
print(f"  Blue Board  (32-43): {sig_outer[16:28]}")

bnr.Close()