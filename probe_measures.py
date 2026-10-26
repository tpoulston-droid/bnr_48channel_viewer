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

bnr_type = clr.GetClrType(Bnr)
all_methods = bnr_type.GetMethods()

# Look for measure, telemetry, diagnostic, or raw optical functions
keywords = ["measure", "hibou", "raw", "optical", "channel", "adcount", "telemetry", "test", "auth"]
matched = [m for m in all_methods if any(k in m.Name.lower() for k in keywords)]

print(f"=== Found {len(matched)} Diagnostic/Measure Methods ===")
for m in matched:
    param_list = [f"{p.ParameterType.Name} {p.Name}" for p in m.GetParameters()]
    print(f"  {m.ReturnType.Name} {m.Name}({', '.join(param_list)})")