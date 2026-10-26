"""
bnr_sdk.status_codes
Symbolic representations of CPI/XFS native return codes, module states,
and recognition failure classifications decompiled from BnrCtlDotNet40MeiReserved.
"""
from enum import IntEnum


class OperationalStatus(IntEnum):
    """Mei.Bnr.Module.OperationalStatus"""
    OPERATIONAL = 0
    CHECKING_ERROR = 1
    NOT_OPERATIONAL = 2
    OPERATIONAL_DEGRADED = 3
    SOFTWARE_LOCKED = 4
    UNKNOWN = -1


class BillRecognitionStatus(IntEnum):
    """Mei.Bnr.BillRecognitionStatus"""
    UNKNOWN = 0
    NOT_DENOMINATED = 1
    NOT_VALIDATED = 2
    SUPERIMPOSED = 3
    UNFIT = 4
    RECOGNIZED = 5


class SizeCheckAlgoResult(IntEnum):
    """Mei.Bnr.SizeCheckAlgoResult"""
    TEST_OK = 0
    BAD_LENGTH = 1
    BAD_WIDTH = 2
    UNKNOWN = 3


class SafeDoorStatus(IntEnum):
    """Mei.Bnr.SafeDoorStatus"""
    OPEN = 6194
    LOCKED = 6196
    UNKNOWN = 6197


class TransportStatus(IntEnum):
    """Mei.Bnr.TransportStatus"""
    OK = 6203
    INOPERATIVE = 6204
    UNKNOWN = 6206


class SystemErrorCode(IntEnum):
    """Mei.Bnr.SystemErrorCode"""
    NO_ERROR = 0
    OPENED = 1
    UNLOCKED = 2


class ModuleErrorCode(IntEnum):
    """Mei.Bnr.Module.ErrorCode"""
    NO_ERROR = 0
    COM_BREAKDOWN = 1
    INCOMPATIBLE_MODULE = 2
    MISSING_MODULE = 3
    OPENED = 4
    WRONG_MODULE_TYPE = 5
    BOOT_RUNNING = 6
    CANNOT_EXTRACT_BILL = 7
    INCOMPATIBLE_SOFTWARE = 8
    MODULE_NOT_DETECTED = 9
    SHUTTER_CLOSED = 10
    NO_COM = 11
    SIGNAL_TOO_HIGH = 12
    SIGNAL_TOO_LOW = 13


class RecognitionSensorErrorCode(IntEnum):
    """Mei.Bnr.Module.Element.RecognitionSensor.ErrorCode"""
    NO_ERROR = 0
    OFFSET_COMPENSATION_ERROR = 1
    REMAINING_OFFSET_TOO_LOW = 2
    REMAINING_OFFSET_TOO_HIGH = 3
    CANNOT_REGULATE_FOR_DSR_IDENT = 4
    COEF_DIV_BY_ZERO = 5
    COEF_NEG_VALUE = 6
    COEF_OVERFLOW = 7
    COEF_OUT_OF_RANGE = 8
    CANNOT_REGULATE = 9


class BnrXfsErrorCode(IntEnum):
    """Mei.Bnr.BnrXfsErrorCode"""
    SUCCESS = 0
    ILLEGAL = 1010
    NO_HARDWARE = 1011
    NO_EXIST = 1013
    FAILURE = 1015
    BUSY = 1017
    PARAMETER_INVALID = 1018
    CANCELED = 1021
    NOT_SUPPORTED = 1022
    FIRMWARE_ERROR = 1023
    HARDWARE_ERROR = 1025
    USER_ERROR = 2001
    CASH_IN_ACTIVE = 6072
    CASH_DEVICE_ERROR = 6073
    CASH_UNIT_ERROR = 6074
    INVALID_CASH_UNIT = 6080
    INVALID_CURRENCY = 6081
    INVALID_MIX_NUMBER = 6085
    NOT_DISPENSABLE = 6087
    NO_BILLS = 6088
    NO_CASH_IN_STARTED = 6089
    TOO_MANY_BILLS = 6092


class BnrUsbErrorCode(IntEnum):
    """Mei.Bnr.BnrUsbErrorCode"""
    CRC = 10001
    STALL_PID = 10004
    DEVICE_NOT_RESPONDING = 10005
    BUFFER_OVERRUN = 10012
    BUFFER_UNDERRUN = 10013
    ENDPOINT_HALTED = 10048
    NO_MEMORY = 10256
    ERROR_BUSY = 10259
    REQUEST_FAILED = 10260
    DEVICE_NOT_FOUND = 10517
    IO_TIMEOUT = 10520
    DEVICE_REMOVED = 10521
    DEVICE_LOCKED = 10524


# High-level Return Code flags emitted during CashIn / Coupon runs
class BnrReturnCode(IntEnum):
    SUCCESS_NO_NOTE = 1
    EXP_RECOGNITION_DETAILS = 2
    EXP_COUPON_READ = 32
    EXP_RECOGNITION_EVENT = 64
    EXP_OPTICAL_MEASUREMENT = 128
    INVALID_BILL = 1024
    CALIBRATION_SUCCESS = 2048
    EXP_RECOGNITION_COMPLETE = 4096
    EXP_CALIBRATION_DATA = 8192