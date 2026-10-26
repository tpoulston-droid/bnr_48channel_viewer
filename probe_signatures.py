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

print("=== Testing GetSignature arguments ===")
for test_val in [1, 2, 3, 4, 10, 100, 0]:
    try:
        res = bnr.GetSignature(System.UInt32(test_val))
        arr = list(res)
        non_zeros = sum(1 for x in arr if x > 0)
        print(f"  GetSignature({test_val}) SUCCESS -> len: {len(arr)}, non-zero: {non_zeros}, first 4: {arr[:4]}")
    except Exception as ex:
        print(f"  GetSignature({test_val}) FAILED -> {ex}")

# Also check parameterless or alternative signature methods
for meth in ["GetSignature", "GetDispenseSignature", "DisplaySignature"]:
    if hasattr(bnr, meth):
        try:
            fn = getattr(bnr, meth)
            res = fn()
            arr = list(res)
            print(f"  {meth}() SUCCESS -> len: {len(arr)}, non-zero: {sum(1 for x in arr if x > 0)}")
        except Exception as ex:
            print(f"  {meth}() FAILED -> {ex}")

bnr.Close()