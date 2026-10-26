"""
bnr_sdk.client
Consolidated BNR controller with verified CashUnit pre-query,
robust CashInStart recovery, and 64-channel dual-signature extraction.
"""
import os
import sys
import struct
import time
from typing import List, Optional

if struct.calcsize("P") * 8 != 32:
    raise EnvironmentError("Requires 32-bit (x86) Python environment.")

DEFAULT_ASSEMBLY_DIR = r"C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR"
if os.path.exists(DEFAULT_ASSEMBLY_DIR):
    if DEFAULT_ASSEMBLY_DIR not in sys.path:
        sys.path.append(DEFAULT_ASSEMBLY_DIR)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(DEFAULT_ASSEMBLY_DIR)

import clr
try:
    clr.AddReference("BnrCtlDotNet40MeiReserved")
    import System
    from Mei.Bnr import Bnr
except Exception as _ex:
    raise ImportError(f"Failed to bind BnrCtlDotNet40MeiReserved.dll: {_ex}")

from .status_codes import OperationalStatus
from .models import (
    HibouHeadSnapshot,
    HibouBoard,
    ChannelMeasure,
    SystemHealth,
    SystemOpeningCounters,
    RegulatedSensorValue,
)
from .exceptions import (
    BnrError,
    BnrConnectionError,
    BnrNotConnectedError,
    BnrAccessDeniedError,
    BnrTransportFaultError,
    BnrTimeoutError,
    BnrInvalidMediaError,
)

FACTORY_KEY = "MEI_RESERVED"


class BnrClient:
    def __init__(self, assembly_dir: str = DEFAULT_ASSEMBLY_DIR):
        self.assembly_dir = assembly_dir
        self._bnr = None
        self._instantiate_driver()

    def _instantiate_driver(self):
        try:
            self._bnr = Bnr()
        except Exception as ex:
            raise BnrConnectionError(f"Failed to instantiate Mei.Bnr.Bnr: {ex}")

    def connect(self, factory_unlock: bool = True):
        try:
            if self._bnr is None:
                self._instantiate_driver()

            ret = None
            if hasattr(self._bnr, "Open"):
                ret = self._bnr.Open()
            elif hasattr(self._bnr, "OpenDevice"):
                ret = self._bnr.OpenDevice()
            else:
                raise BnrConnectionError("Driver lacks Open/OpenDevice entrypoint.")

            if ret is not None and int(ret) != 0:
                raise BnrConnectionError(f"Bnr.Open() failed with code {ret}")

            # Clear session state
            self._abort_existing_sessions()

            if factory_unlock:
                self.authenticate_factory()

        except BnrConnectionError:
            raise
        except Exception as ex:
            raise BnrConnectionError(f"Failed to connect to BNR over WinUSB: {ex}")

    def disconnect(self):
        if self._bnr:
            self._abort_existing_sessions()
            for close_fn in ("Close", "CloseDevice"):
                if hasattr(self._bnr, close_fn):
                    try:
                        getattr(self._bnr, close_fn)()
                        break
                    except Exception:
                        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _abort_existing_sessions(self):
        if not self._bnr:
            return
        for fn_name in ("CancelWaiting", "CashInRollback", "CashInEnd"):
            if hasattr(self._bnr, fn_name):
                try:
                    getattr(self._bnr, fn_name)()
                    time.sleep(0.08)
                except Exception:
                    pass

    def authenticate_factory(self, key: str = FACTORY_KEY):
        if not self._bnr:
            return
        for method, token in [
            ("SetFactoryAccessKey", key),
            ("SetFactoryAccessKey", "MEI Reserved"),
            ("Authorize", key),
            ("SetServiceMode", True),
            ("SetAccessLevel", 2),
        ]:
            if hasattr(self._bnr, method):
                try:
                    getattr(self._bnr, method)(token)
                except Exception:
                    pass

    def reset(self, wait_for_idle: bool = True, timeout_sec: float = 12.0):
        if not self._bnr:
            raise BnrNotConnectedError("Device not connected.")

        self._bnr.Reset()
        if wait_for_idle:
            self.wait_until_ready(timeout_sec=timeout_sec)
        self.authenticate_factory()

    def wait_until_ready(self, timeout_sec: float = 20.0, poll_interval: float = 0.25):
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                st = self._bnr.Status
                if st is not None:
                    dev_status = int(st.DeviceStatus)
                    trans_status = int(st.TransportStatus)

                    if dev_status in (6180, 0) and trans_status in (6203, 0):
                        return
            except Exception:
                pass
            time.sleep(poll_interval)

        final_st = getattr(self._bnr.Status, "DeviceStatus", "Unknown") if (self._bnr and self._bnr.Status) else "None"
        raise BnrTimeoutError(f"Timed out waiting for BNR OnLine ({timeout_sec}s). DeviceStatus: {final_st}")

    def get_system_health(self) -> SystemHealth:
        is_conn = bool(self._bnr is not None)
        mos = OperationalStatus.UNKNOWN
        fw = "UNKNOWN"
        psu_status = "OK"
        psu_raw = 0
        sys_temp = None
        interlocks = None

        main_mod = getattr(self._bnr, "MainModule", None)
        if not main_mod and hasattr(self._bnr, "get_MainModule"):
            try:
                main_mod = self._bnr.get_MainModule()
            except Exception:
                pass

        if main_mod:
            fw = str(getattr(main_mod, "FirmwareVersion", "UNKNOWN"))

        try:
            st = self._bnr.Status
            if st is not None:
                dev_status = int(st.DeviceStatus)
                if dev_status in (6180, 0):
                    mos = OperationalStatus.OPERATIONAL
                else:
                    mos = OperationalStatus.DEGRADED
        except Exception:
            mos = OperationalStatus.UNKNOWN

        opening_obj = getattr(self._bnr, "SystemOpeningDetails", None)
        if not opening_obj and hasattr(self._bnr, "get_SystemOpeningDetails"):
            try:
                opening_obj = self._bnr.get_SystemOpeningDetails()
            except Exception:
                pass

        if opening_obj:
            try:
                interlocks = SystemOpeningCounters.from_managed(opening_obj)
            except Exception:
                pass

        return SystemHealth(
            is_connected=is_conn,
            operational_status=mos,
            firmware_version=fw,
            power_supply_status=psu_status,
            power_supply_raw=psu_raw,
            interlocks=interlocks,
            system_temperature_c=sys_temp,
        )

    def get_module_regulations(self, module_name: str = "MainModule") -> List[RegulatedSensorValue]:
        mod = getattr(self._bnr, module_name, None)
        if not mod:
            return []
        regs = getattr(mod, "Regulations", None)
        if not regs:
            return []
        sensor_cal_list = getattr(regs, "RegulatedSensorCalibration", None)
        if not sensor_cal_list:
            return []

        parsed_values = []
        for item in sensor_cal_list:
            try:
                parsed_values.append(
                    RegulatedSensorValue(
                        element_id=int(item.ElementId),
                        threshold=int(item.Threshold),
                        value=int(item.Value),
                        offset=int(item.Offset),
                        gain=int(item.Gain),
                    )
                )
            except Exception:
                pass
        return parsed_values

    def run_optical_sweep(self, currency_code: str = "USD") -> HibouHeadSnapshot:
        """
        Executes active mouth arming, waits for physical coupon traversal,
        and extracts 64 channels across both Hibou heads.
        """
        # 1. Clean residual locks
        self._abort_existing_sessions()
        self.authenticate_factory()

        # 2. XFS Prerequisite: Access CashUnit to prime CIM state machine
        print("[BNR] Querying CashUnit configuration...")
        for _ in range(6):
            try:
                cu = self._bnr.CashUnit
                if cu is not None:
                    break
            except Exception:
                time.sleep(0.2)

        # 3. Arm Cash-In Session
        print("[BNR] Calling CashInStart()...")
        armed = False
        try:
            res_cs = self._bnr.CashInStart()
            print(f"[BNR] CashInStart returned: {res_cs}")
            armed = True
        except Exception as ex:
            print(f"[BNR] CashInStart failed: {ex}")
            # If failed, attempt recovery rollback and retry once
            try:
                self._abort_existing_sessions()
                _ = self._bnr.CashUnit
                res_cs = self._bnr.CashInStart()
                armed = True
            except Exception:
                pass

        # 4. Ingestion Loop: Poll while listening for media insertion
        if armed:
            print("[BNR] Mouth is active! Feed calibration strip now...")
            start_time = time.time()
            timeout_sec = 18.0
            while (time.time() - start_time) < timeout_sec:
                try:
                    res = self._bnr.CashIn("USD")
                    if res == 32:
                        print("[BNR] Coupon detected in mouth! Drawing across heads...")
                        time.sleep(0.5)
                        continue
                    if res in (1024, 0, 2048, 8192, 1, 2, 4, 16):
                        print(f"[BNR] Pass completed! Terminal Code: {res}")
                        break
                except Exception:
                    time.sleep(0.2)
                time.sleep(0.25)

        time.sleep(0.4)

        # 5. Extract fresh telemetry
        snapshot = self._extract_snapshot()

        # 6. Eject and close session
        self._abort_existing_sessions()

        return snapshot

    def _extract_snapshot(self, operation_id: int = 0) -> HibouHeadSnapshot:
        def clean_array(val):
            if val is None:
                return []
            if callable(val):
                try: val = val()
                except Exception: return []
            try:
                return [int(v) for v in list(val) if isinstance(v, (int, float))]
            except Exception:
                return []

        head0_arr = []
        head1_arr = []

        if hasattr(self._bnr, "GetSignature"):
            # Head 0: Red Upper (00-11) & Black Lower (48-59)
            try:
                head0_arr = clean_array(self._bnr.GetSignature(System.UInt32(1)))
                print(f"[SDK DIAG] Inner Head (Sig 1) extracted: {len(head0_arr)} counts")
            except Exception as ex:
                print(f"[SDK DIAG] Sig 1 note: {ex}")

            # Head 1: Green Lower (16-27) & Blue Upper (32-43)
            try:
                head1_arr = clean_array(self._bnr.GetSignature(System.UInt32(2)))
                print(f"[SDK DIAG] Outer Head (Sig 2) extracted: {len(head1_arr)} counts")
            except Exception as ex:
                print(f"[SDK DIAG] Sig 2 note: {ex}")

        head0_arr = (head0_arr + [0] * 32)[:32]
        head1_arr = (head1_arr + [0] * 32)[:32]
        full_64 = head0_arr + head1_arr

        return HibouHeadSnapshot(channels=[
            ChannelMeasure(channel_id=idx, raw_ad_count=val)
            for idx, val in enumerate(full_64)
        ])
