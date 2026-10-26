48-Channel Viewer (BNR Hibou Head Triage Tool)
A depot-level diagnostic visualizer and component screening utility for the Crane Payment Innovations (CPI / MEI) BNR Advance Series banknote recyclers.
While the Hibou sensor array reports telemetry in a 64-channel frame, 48 channels represent true optical document photodetectors (12 active sensors per board across 4 boards), while the remaining 16 channels carry supervisory electrical telemetry (power rails and analog reference voltages).
The 48-Channel Viewer isolates and visualizes these active optical channels, giving bench technicians real-time visibility into photodiode gain, emitter strength, and sub-board transceiver balance without requiring full bill validation routines or live currency cycling.
1. Hardware Architecture & Channel Mapping
The BNR Hibou recognition head consists of four distinct sub-boards organized into an Inner Throat pair and an Outer Exit pair. Each physical board exposes a 16-channel slice within the 64-channel DSP buffer:
12 Active Optical Channels (Channels 00-11): Conditioned photodetector stages across the document path.
4 Supervisory Telemetry Channels (Channels 12-15): Analog power rails and ground references.
                  HIBOU OPTICAL CAVITY (DOCUMENT PATH)
       =========================================================
          [Upper Roof Assembly - Shared Latch / Hinge Cavity]
            RED BOARD (Inner Upper)        BLUE BOARD (Outer Upper)
            12x Receiver Photodiodes       Emitters / UV Transceiver
            (Ch 00-11 + 4 Rails)           (Ch 32-43 + 4 Rails)
       ------------------- Bill Transit Path -------------------
            BLACK BOARD (Inner Lower)      GREEN BOARD (Outer Lower)
            Emitters (Visible / IR)        12x Receiver Photodiodes
            (Ch 48-59 + 4 Rails)           (Ch 16-27 + 4 Rails)
          [Lower Deck Assembly - Belt Drive / Transport Floor]
       =========================================================

Transmissive Pairing & Board Matrix
RED BOARD: Inner Upper Receiver
Active Optical Sensors: CH 00 - 11 (Ta1 Transmission & Reflection)
Supervisory Telemetry (Rails): CH 12 (+12V), CH 13 (-12V), CH 14 (+3.3V), CH 15 (GND)
Illuminated By: BLACK BOARD
GREEN BOARD: Outer Lower Receiver
Active Optical Sensors: CH 16 - 27 (Tb Transmission & Reflection)
Supervisory Telemetry (Rails): CH 28 (+12V), CH 29 (-12V), CH 30 (+3.3V), CH 31 (GND)
Illuminated By: BLUE BOARD
BLUE BOARD: Outer Upper Transceiver
Active Optical Sensors: CH 32 - 43 (UV / Optical Thickness)
Supervisory Telemetry (Rails): CH 44 (+12V), CH 45 (-12V), CH 46 (+3.3V), CH 47 (GND)
Illuminated By: Self / Green Board
BLACK BOARD: Inner Lower Transceiver
Active Optical Sensors: CH 48 - 59 (Visible/IR Emitters & Sweep)
Supervisory Telemetry (Rails): CH 60 (+12V), CH 61 (-12V), CH 62 (+3.3V), CH 63 (GND)
Illuminated By: Self / Red Board

2. Opposing Pair Triage Logic
Because Red and Green are pure receiver boards (unpopulated LED footprints) and Black and Blue house the LED emitter banks, optical dropouts require opposing-board root-cause analysis:

Inner Throat Failure (Red Channels 00-11 drop below 100 counts):

Do not replace the Red board first. Verify the BLACK BOARD LED drive string or clean the upper/lower inner lenses.

Outer Exit Failure (Green Channels 16-27 drop below 100 counts):

Do not replace the Green board first. Inspect the BLUE BOARD UV/IR emitters or clean the exit prisms.

Entire 12-Channel Drop on Red or Green (Opposing emitters confirmed illuminated):

Isolates the onboard analog multiplexer (MUX IC), MC33078 operational amplifier, or local analog rail collapse on that specific receiver board.

8-Channel Stepped Block Dropout (e.g., CH 00-07 flat):

Pinpoints an analog multiplexer bank defect or stuck address select line (A0-A2).

3. Signal Thresholds & Diagnostic Criteria
The viewer samples raw 10-bit Analog-to-Digital Converter (ADC) counts (0 to 1023 integer scale) or normalized 8-bit calibration counts (0 to 255):

< 150 counts (or < 50 for 8-bit) -> DEAD / OPEN (Red Indicator)
Fault Mode: Dead emitter LED, open photodiode, damaged flex cable, or cut PCB trace.

150 - 649 counts (or 50 - 180 for 8-bit) -> MARGINAL / DEGRADED (Amber Indicator)
Fault Mode: Optical contamination, scratched acrylic lens, or degraded emitter/photodiode.

650 - 850 counts (or 181 - 240 for 8-bit) -> NOMINAL (Green Indicator)
Fault Mode: Standard target calibration window under reference coupon pass.

850 counts (or > 240 for 8-bit) -> SATURATED / SHORT (Yellow Indicator)
Fault Mode: Shorted input pin, railed op-amp output (MC33078/TL064), or ambient light leak.

4. EEPROM Gain Health Banding
When connected to hardware, the viewer audits the stored calibration multipliers from internal EEPROM/Flash against factory tolerance limits:

Gain Multiplier = Target Reference Count / Calibrated ADC Response

   
PDF

0.80x - 1.80x (PASS / OK): Optimal optical clarity and photodiode efficiency.

1.81x - 2.50x (WARN / AMBER): Compensating for high optical attenuation (dust, light pipe scratches, or aging LED).

2.50x or Byte 254/255 (FAIL / RED): Severe optical obstruction, failed emitter, or open-circuit phototransistor.

< 0.50x (LOW / YELLOW): Shunted circuit or ambient light saturation.

5. Prerequisites & Environment
Architecture: 32-bit (x86) Python environment is strictly required. Crane's BnrCtlDotNet40MeiReserved.dll cannot be loaded into a 64-bit runtime.

Operating System: Windows 10 / 11 (x86 or x64 with WOW64).

Drivers: CPI WinUSB driver stack installed via STS Advance or standalone installer (C:\Program Files (x86)\Crane Payment Innovations\STS Advance for BNR).

Process Exclusivity: Ensure BnrService.exe, StsAdvance.exe, or MeiUsbService.exe are closed prior to opening a connection to avoid WinUSB handle contention.

6. Installation & Execution
PowerShell
# 1. Create a 32-bit virtual environment
py -3.11-32 -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install PyQt5 pythonnet

# 3. Launch the 48-Channel Viewer
python bnr_48ch_viewer.py

7. Operating Procedure
Initialize Connection: Launch the tool and click "Connect Hardware". The viewer binds to Mei.Bnr.Bnr, issues MEI_RESERVED factory authentication, resets the transport state machine, and evaluates stored EEPROM gain tables.

Run Calibration Strip: Click "Run Coupon Test" and insert a white calibration strip into the inlet slot. The transport pulls the strip across both optical heads, registers the sweep completion, captures the raw ADC snapshot, and rolls the coupon back out the bezel.

Inspect Active Channels: Verify that all 12 optical bars on each of the 4 board cards settle within the green nominal target (650-850 counts).

Inspect Board Rails: Review the rail indicators at the base of each card (+12V, -12V, +3.3V, and GND) to verify power distribution integrity across the transport spine.