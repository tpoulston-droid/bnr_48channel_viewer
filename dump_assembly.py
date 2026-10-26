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

OUTPUT_FILE = "assembly_dump.txt"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    def log(msg=""):
        print(msg)
        f.write(str(msg) + "\n")

    log("=== Loading BnrCtlDotNet40MeiReserved ===")
    asm = Assembly.Load("BnrCtlDotNet40MeiReserved")
    types = asm.GetTypes()
    log(f"Total Types in Assembly: {len(types)}")

    user_types = [
        t for t in types 
        if not t.FullName.startswith("<") 
        and "CrtImplementationDetails" not in t.FullName
        and "CppImplementationDetails" not in t.FullName
    ]

    for t in user_types:
        methods = [
            m.Name for m in t.GetMethods() 
            if not m.Name.startswith("get_") 
            and not m.Name.startswith("set_") 
            and not m.Name.startswith("__")
        ]
        
        interesting = [
            m for m in methods 
            if any(k in m.lower() for k in ["measure", "optical", "ad", "channel", "signature", "calib", "test", "read", "raw", "hibou", "auth"])
        ]

        if interesting or len(methods) <= 10:
            log(f"\nType: {t.FullName} ({len(methods)} methods)")
            if interesting:
                log(f"   Key Methods: {interesting}")
            else:
                log(f"   Methods: {methods}")

print(f"\n[DONE] Results written to {os.path.abspath(OUTPUT_FILE)}")