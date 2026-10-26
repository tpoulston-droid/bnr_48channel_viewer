import os
import sys

STS_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"
if os.path.exists(STS_DIR):
    sys.path.append(STS_DIR)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(STS_DIR)

import clr
clr.AddReference("BnrCtlDotNet40MeiReserved")
from System.Reflection import Assembly
import Mei.Bnr

asm = Assembly.Load("BnrCtlDotNet40MeiReserved")

def inspect_type(type_name):
    t = asm.GetType(type_name)
    if not t:
        print(f"\n[NOT FOUND] {type_name}")
        return
    print(f"\n=== {t.FullName} ===")
    props = [p.Name for p in t.GetProperties()]
    methods = [m.Name for m in t.GetMethods() if not m.Name.startswith("get_") and not m.Name.startswith("set_")]
    fields = [f.Name for f in t.GetFields()]
    if props:
        print(f"  Properties ({len(props)}): {props[:15]}")
    if fields:
        print(f"  Fields ({len(fields)}): {fields[:15]}")
    if methods:
        print(f"  Methods: {methods}")

inspect_type("Mei.Bnr.ReservedAccess")
inspect_type("Mei.Bnr.Module.MainModule.Measures")
inspect_type("Mei.Bnr.Module.MainModule.RecognitionCalibrationValue")
inspect_type("Mei.Bnr.Module.MainModule.Status")