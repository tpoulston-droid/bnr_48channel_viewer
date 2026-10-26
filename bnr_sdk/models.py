"""
bnr_sdk.models
Native binary ctypes structures matching decompiled C++ memory layouts
alongside high-level dataclasses for sensor telemetry.
"""
import ctypes
import struct
from dataclasses import dataclass, field
from typing import List, Optional

from .status_codes import (
    OperationalStatus,
    BillRecognitionStatus,
    SizeCheckAlgoResult,
    RecognitionSensorErrorCode,
)
"""
bnr_sdk.models
Data models and containers for Hibou optical and electrical telemetry.
"""
from enum import Enum

class HibouBoard(Enum):
    RED_UPPER_OPTICAL = 0
    GREEN_LOWER_OPTICAL = 1
    BLUE_UPPER_EXIT = 2
    BLACK_LOWER_EXIT = 3

@dataclass
class ChannelMeasure:
    channel_id: int
    raw_ad_count: int

@dataclass
class HibouHeadSnapshot:
    channels: List[ChannelMeasure] = field(default_factory=list)

    def get_board_channels(self, board: HibouBoard) -> List[ChannelMeasure]:
        """
        Returns the 16 channels belonging to a board:
          - RED_UPPER_OPTICAL:   Channels 00 - 15
          - GREEN_LOWER_OPTICAL: Channels 16 - 31
          - BLUE_UPPER_EXIT:     Channels 32 - 47
          - BLACK_LOWER_EXIT:    Channels 48 - 63
        """
        stride = 16
        idx_map = {
            HibouBoard.RED_UPPER_OPTICAL: 0,
            HibouBoard.GREEN_LOWER_OPTICAL: 1,
            HibouBoard.BLUE_UPPER_EXIT: 2,
            HibouBoard.BLACK_LOWER_EXIT: 3,
        }
        start = idx_map[board] * stride
        return self.channels[start : start + stride]


# ---------------------------------------------------------------------------
# NATIVE CTYPES STRUCTURES (Explicit decompiled byte layouts)
# ---------------------------------------------------------------------------

class SystemOpeningDetailsStruct(ctypes.LittleEndianStructure):
    """Matches Mei.Bnr.SystemOpeningDetails (Size = 12 bytes)"""
    _pack_ = 1
    _fields_ = [
        ("withBillStoppedCount", ctypes.c_uint16),       # Offset 0
        ("cashModulesLockCount", ctypes.c_uint16),       # Offset 2
        ("billIntakeCoverCount", ctypes.c_uint16),       # Offset 4
        ("recognitionSensorCoverCount", ctypes.c_uint16), # Offset 6
        ("spineCoverCount", ctypes.c_uint16),            # Offset 8
        ("bnfCoverCount", ctypes.c_uint16),              # Offset 10
    ]


class LoaderRecognitionRejectDetailsStruct(ctypes.LittleEndianStructure):
    """LoaderRecognitionRejectDetails (Size = 4 bytes)"""
    _pack_ = 1
    _fields_ = [
        ("forgeryCount", ctypes.c_uint16),  # Offset 0
        ("unknownCount", ctypes.c_uint16),  # Offset 2
    ]


class RegulatedSensorCalibrationValueStruct(ctypes.LittleEndianStructure):
    """Matches global::RegulatedSensorCalibrationValue (Size = 12 bytes)"""
    _pack_ = 1
    _fields_ = [
        ("elementId", ctypes.c_uint32),  # Offset 0
        ("threshold", ctypes.c_uint16),  # Offset 4
        ("value", ctypes.c_uint16),      # Offset 6
        ("offset", ctypes.c_uint16),     # Offset 8
        ("gain", ctypes.c_uint16),       # Offset 10
    ]


class T_ModuleRegulationBuffer(ctypes.Structure):
    """Unmanaged buffer for moduleMeiReserved_GetRegulationValues (Size = 8228 bytes)"""
    _fields_ = [("raw_data", ctypes.c_uint8 * 8228)]


class T_ModuleMeasuresBuffer(ctypes.Structure):
    """Unmanaged buffer for moduleMeiReserved_GetMeasures (Size = 42900 bytes)"""
    _fields_ = [("raw_data", ctypes.c_uint8 * 42900)]


# ---------------------------------------------------------------------------
# HIGH-LEVEL PYTHON TELEMETRY MODELS
# ---------------------------------------------------------------------------

@dataclass
class ChannelTelemetry:
    channel_index: int
    raw_ad_count: int
    board: HibouBoard
    is_dead: bool = False
    is_saturated: bool = False


@dataclass
class SystemOpeningCounters:
    with_bill_stopped: int
    cash_modules_lock: int
    bill_intake_cover: int
    recognition_sensor_cover: int
    spine_cover: int
    bnf_cover: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "SystemOpeningCounters":
        if len(data) < 12:
            data = data.ljust(12, b"\x00")
        unpacked = struct.unpack_from("<6H", data, 0)
        return cls(*unpacked)

    @classmethod
    def from_managed(cls, managed_obj) -> "SystemOpeningCounters":
        return cls(
            with_bill_stopped=int(getattr(managed_obj, "WithBillStoppedCount", 0)),
            cash_modules_lock=int(getattr(managed_obj, "CashModulesLockCount", 0)),
            bill_intake_cover=int(getattr(managed_obj, "BillIntakeCoverCount", 0)),
            recognition_sensor_cover=int(getattr(managed_obj, "RecognitionSensorCoverCount", 0)),
            spine_cover=int(getattr(managed_obj, "SpineCoverCount", 0)),
            bnf_cover=int(getattr(managed_obj, "BnfCoverCount", 0)),
        )


@dataclass
class SystemHealth:
    is_connected: bool
    operational_status: OperationalStatus
    firmware_version: str
    power_supply_status: str
    power_supply_raw: int
    interlocks: Optional[SystemOpeningCounters] = None
    system_temperature_c: Optional[float] = None


@dataclass
class RegulatedSensorValue:
    element_id: int
    threshold: int
    value: int
    offset: int
    gain: int