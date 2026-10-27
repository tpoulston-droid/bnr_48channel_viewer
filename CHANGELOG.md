# Changelog

All notable changes to the 48-Channel Optical Hibou Viewer will be documented in this file.

## [0.2.0] - 2026-10-27

### Added
- **Docked Automated Triage Summary Panel (`src/widgets/triage_panel.py`):**
  - Live L1 status pills for Red, Blue, Black, and Green boards.
  - Automated CLR soldering instructions targeting quad op-amps (U1–U3) and emitter LED strings.
- **Dynamic Offset Compensator (`bnr_sdk/compensator.py`):**
  - Software flat-field normalization and dark-offset baseline subtraction based on decompiled CPI `ResidualOffset` and `ScaleFactor` tables.
  - Integrated `SizeCheckAlgoDetailedResult` reflection parser to validate coupon width/skew (83 mm nominal).
- **Direct Transport Readiness Engine (`bnr_sdk/client.py`):**
  - Automated detection and recovery from `OffLine (6179)` state into `OnLine (6180)`.
  - Added XFS `CashUnit` prerequisite polling to prevent driver `Busy` race conditions.
  - Resolved `CashInActive` lock breaking using automated `CashInRollback()` session teardown.
  - Dual-head optical signature extraction (`GetSignature(1)` + `GetSignature(2)`) across all 64 ADC slots.

### Fixed
- Fixed WinUSB driver binding by explicitly enforcing `bnr.Open()` during initialization.
- Resolved `FileNotFoundException` by including CPI STS Advance installation path in `sys.path` and unmanaged DLL directories.
- Eliminated crash on missing `OpticalSnapshot` model imports in `bnr_sdk/models.py`.
