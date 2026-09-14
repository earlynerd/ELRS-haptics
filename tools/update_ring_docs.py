"""Apply documentation migration and record inspected loader source hashes."""
from kicad_edit import ROOT,HW
import hashlib,json
if (HW/'backups/before-distributed-vbat').exists():
    raise SystemExit('Historical one-time migration; edit current documentation directly.')
readme='''# Haptic bracelet

Battery-powered attitude feedback for FPV flying, with eight haptic actuators around each wrist. An ESP32-C6 receives telemetry over ESP-NOW and controls eight M2003FC1AE/DRV2625 pods using the music robot's UART ring architecture. Each wrist uses one 1S pack with an open number of parallel pouch cells distributed around the bracelet.

Open **hardware/haptic-bracelet.kicad_pro** in KiCad 10. The native schematics are the editable source of truth. One project represents one wrist; build two for the pair.

## Current schematic

The 13 sheets contain the ESP32 controller with switched pod power and shared reset, a ring overview, eight individual pod circuits, the charger/regulator, USB-C data/power, and ESP32 support passives. Pod 0 also houses the main electronics; sheets do not prescribe separate PCBs.

- Each pod contains an M2003FC1AE, local I2C-connected DRV2625 and LRA placeholder.
- PF0/PF1 preserve the robot loader UART/ICE pins; PB13 holds the driver in reset during loading.
- Ordinary inter-pod wiring is switched power, ground, forwarded data and shared reset. Battery branches are additional.
- GPIO19/2 are ring TX/RX; GPIO18 asserts common reset through Q5; GPIO3 enables pod power through U26 TPS22918.
- All pod MCUs and drivers switch off together. Firmware sets TX low and disables the RX pull-up before removing power; no UART isolation buffers.
- USB-C connects to native ESP32 Serial/JTAG on GPIO12/13. BQ25186 charges the protected pack and TPS63802 supplies regulated 3.3 V. GPIO6/7 I2C serves main-board power/USB only.
- Every pod has removable UART links and ICE pads for initial flashing, plus an optional cell thermistor interface.

See [ring pods and power sequencing](docs/ring-pods.md), [pack/power architecture](docs/power-architecture.md) and [USB implementation](docs/usb-power-implementation.md) for pin maps and required firmware behavior. Architectural choices are recorded in [DECISIONS.md](DECISIONS.md).

## Verification and remaining work

KiCad 10.0.1 exports all 13 sheets. The 237-component exported netlist passes ring and USB/power connectivity checks. ERC has **0 errors and 8 warnings**, all the existing unused DRV2625 TRIG/INTZ pins tied to ground. Keep those pins in input/unused mode. No new ERC exclusions were added. Results are in `hardware/verification/`; current rendered previews are in `hardware/preview/ring-revision/`.

The PCB is initialized but empty. Actuator selection, driver package/footprint, power budget, final power/connector parts and footprints, protected pack implementation, mechanical partitioning and layout remain open. The DRV2625 custom symbol currently uses the YFF nine-ball pin map with no footprint assigned. M2003 uses TSSOP20. Battery count, capacity and runtime target remain open.

Firmware is not implemented or flashed for the bracelet. The schematic accommodates the inspected robot loader; unchanged-binary operation, UART power sequencing, temperature supervision, charging and physical behavior still need verification. Attitude-to-haptic mapping remains open around the user's sensory-feedback concept.

`tools/check_connectivity.py` and `tools/check_usb_power.py` audit a freshly exported XML netlist. One-time construction scripts refuse to overwrite their target revision; edit native files in KiCad. Previous native circuits are retained under `hardware/backups/before-usb-power/` and `hardware/backups/before-ring-pods/`.

## References

- [Nuvoton M2003 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_M2003_Series_EN_Rev1.00.pdf).
- [TI DRV2625 datasheet](https://www.ti.com/lit/ds/symlink/drv2625.pdf).
- [TI TPS22918 datasheet](https://www.ti.com/lit/ds/symlink/tps22918.pdf).
- [ESP32-C6-MINI-1 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf).
- [ExpressLRS backpack telemetry](https://www.expresslrs.org/software/backpack-telemetry/).

Power/USB source details and loader provenance are linked from the implementation documents.
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')
p=ROOT/'docs/power-architecture.md';s=p.read_text(encoding='utf-8')
s=s.replace('implemented, 2026-09-11','and switched ring-pod circuit implemented, 2026-09-12')
s=s.replace('|-- I2C mux','|-- USB/charger control').replace('+-- 8 haptic drivers','+-- TPS22918 switch --> 8 MCU + driver pods')
s=s.replace('upstream I2C bus at 0x6A, separate from the mux at 0x70 and downstream haptic drivers at 0x5A','main-board I2C bus at 0x6A alongside TUSB320LAI at 0x47. Each pod controls its own DRV2625 at 0x5A on local I2C')
start=s.index('Keep the existing common 3V3 rail initially,');end=s.index('\n\nThe charger/regulator',start)
s=s[:start]+'The regulated 3V3 rail supplies the ESP32 and main-board control. A TPS22918 switches all eight pod MCUs and drivers onto POD_3V3, with local decoupling. Firmware prevents UART back-powering by driving TX low and disabling the RX pull-up before shutdown. See [ring pods](ring-pods.md) for the reset circuit, interconnect and power sequence. Actuator headroom and simultaneous-current budget remain to be checked after LRA selection.'+s[end:]
s=s.replace('Exact sensor/interface implementation remains open.','Each pod now includes a local ADC/NTC provision; sensor selection, required-cell configuration and firmware remain open. Charging must be disabled before ring power-off or loader entry when it relies on those readings.')
p.write_text(s,encoding='utf-8')
p=ROOT/'docs/usb-power-implementation.md';s=p.read_text(encoding='utf-8')
s=s.replace('GPIO6/7 remain I2C, GPIO18 mux reset and GPIO19 haptic reset.','GPIO6/7 remain main-board I2C. GPIO18 now asserts shared pod reset through Q5; GPIO19/2 provide ring TX/RX and GPIO3 controls switched pod power. See [ring pods](ring-pods.md).')
s=s.replace('all four sheets','all 13 sheets').replace('Boot with haptics reset,','Boot with pod power off and UART pins in their unpowered states,')
p.write_text(s,encoding='utf-8')
decision='''
## 2026-09-12 - Switched pod power with firmware-managed UART states

- **Decision:** Switch all eight M2003/DRV2625 pods from 3V3 through TPS22918; leave ESP32 and charging control powered. GPIO3 enables power with a default-off pulldown. GPIO18 asserts shared reset through an NMOS with its reset pull-up on POD_3V3. Use GPIO19 TX and GPIO2 RX directly: assert pod reset, detach UART, drive TX low and disable the RX pull-up before power-off. Preserve PF0/PF1 loader UART pins and use PB13 for local driver reset. Disable charging before losing required pod temperature reports.
- **Why:** The user requested ring power shutdown and proposed GPIO states to avoid unnecessary signal isolators. The loader already drives PB13 low.
- **Supersedes:** Always-powered pod assumption; proposed UART isolation buffers. Implements the earlier M2003 UART ring decision in native schematics.
- **Affects:** Controller and pod schematics, ring firmware contract, docs/ring-pods.md. Firmware and bench validation remain open.
'''
p=ROOT/'DECISIONS.md';s=p.read_text(encoding='utf-8')
if '## 2026-09-12 - Switched pod power' not in s:p.write_text(s+decision,encoding='utf-8')
robot=ROOT.parent/'bl4818-servo-M23_2'
files=['ldrom/platform.c','ldrom/uart.c','ldrom/bl_internal.h','ldrom/main.c','include/firmware_image.h','scripts/ring_bootload.py']
report={'inspected':'2026-09-12','source_root':str(robot),'mode':'read-only; no firmware copied or changed','files':{f:hashlib.sha256((robot/f).read_bytes()).hexdigest() for f in files}}
(HW/'verification/robot-loader-reference.json').write_text(json.dumps(report,indent=2)+'\n')
print('Updated canonical documentation and loader provenance.')
