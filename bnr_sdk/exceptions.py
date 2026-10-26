"""
bnr_sdk.exceptions
Structured exception hierarchy for the BNR hardware wrapper.
"""

class BnrError(Exception):
    """Base exception for all BNR SDK errors."""
    pass

class BnrConnectionError(BnrError):
    """Raised when opening or communicating over the WinUSB pipe fails."""
    pass

class BnrNotConnectedError(BnrError):
    """Raised when an operation is attempted without an open USB handle."""
    pass

class BnrAccessDeniedError(BnrError):
    """Raised when factory authentication / MEI_RESERVED key is rejected."""
    pass

class BnrTransportFaultError(BnrError):
    """Raised when a bill path jam, gate fault, or transport error occurs."""
    pass

class BnrTimeoutError(BnrError):
    """Raised when polling a state or operation exceeds the timeout limit."""
    pass

class BnrInvalidMediaError(BnrError):
    """Raised when an unrecognized coupon or invalid banknote is processed."""
    pass