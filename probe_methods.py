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

targets = [
    "CashInStart",
    "CashIn",
    "CashInRollback",
    "CashInEnd",
    "CancelWaiting",
    "GetSignature",
    "GetDetailedRecognitionResult",
    "CalibrateWithCoupon",
]

# Use clr.GetClrType to get the underlying System.Type
bnr_type = clr.GetClrType(Bnr)
all_methods = bnr_type.GetMethods()

for target in targets:
    matched = [m for m in all_methods if m.Name == target]
    print(f"\n=== {target} Overloads ({len(matched)}) ===")
    for m in matched:
        param_list = [f"{p.ParameterType.Name} {p.Name}" for p in m.GetParameters()]
        params_str = ", ".join(param_list)
        print(f"  {m.ReturnType.Name} {m.Name}({params_str})")