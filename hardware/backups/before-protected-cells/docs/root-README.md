# Haptic bracelet

Battery-powered attitude feedback for FPV flying, with eight haptic actuators around each wrist. An ESP32-C6 receives telemetry over ESP-NOW and controls eight M2003FC1AE/DRV2625 pods using the music robot's UART ring architecture. Each wrist uses one 1S pack with an open number of parallel pouch cells distributed around the bracelet.

Open **hardware/haptic-bracelet.kicad_pro** in KiCad 10. The native schematics are the editable source of truth. One project represents one wrist; build two for the pair.

## Current schematic

The 14 sheets contain the ESP32 controller with switched pod power and shared reset, a ring overview, eight individual pod circuits, the charger/regulator, high-side pack protection, USB-C data/power, and ESP32 support passives. Pod 0 also houses the main electronics; sheets do not prescribe separate PCBs.

- Each pod contains an M2003FC1AE, local I2C-connected DRV2625 and LRA placeholder.
- PF0/PF1 preserve the robot loader UART/ICE pins; PB13 holds the driver in reset during loading.
- Six conductors cross each of seven wired gaps: switched 3.3 V, ground, forwarded data, shared reset, unswitched VBAT_RAW and serial return. The end pod bridges TX to the return; intermediate pods pass it through to the ESP32. The eighth gap is a purely mechanical clasp with no wiring. Optional cell connections retain local positive-branch fuses and feed the central S-821AAAC high-side pack protector.
- GPIO19/2 are ring TX/RX; GPIO18 asserts common reset through Q5; GPIO3 enables pod power through U26 TPS22918.
- All pod MCUs and drivers switch off together. Firmware sets TX low and disables the RX pull-up before removing power; no UART isolation buffers.
- USB-C connects to native ESP32 Serial/JTAG on GPIO12/13. BQ25186 charges the protected pack and TPS63802 supplies regulated 3.3 V. GPIO6/7 I2C serves main-board power/USB only.
- Every pod has removable UART links and ICE pads for initial flashing, plus an optional cell thermistor interface.

See [ring pods and power sequencing](docs/ring-pods.md), [pack/power architecture](docs/power-architecture.md) and [USB implementation](docs/usb-power-implementation.md) for pin maps and required firmware behavior. Architectural choices are recorded in [DECISIONS.md](DECISIONS.md).

## Verification and remaining work

KiCad 10.0.1 exports all 14 sheets. The 268-component exported netlist passes the six-wire ring/return, USB/power and new pack-protection connectivity checks; the RGB/button circuit remains as previously checked. ERC has **0 errors and 0 warnings**. The unused DRV2625 TRIG/INTZ pins have explicit no-connect flags on all eight pod sheets. No ERC exclusions were added. Results are in `hardware/verification/`; current rendered previews are in `hardware/preview/pack-protection/`.

The PCB is initialized but empty. Actuator selection, driver package/footprint, power budget, final power/connector parts and footprints, cell/fuse ratings, mechanical partitioning and layout remain open. The prototype protector circuit and its footprint are implemented; see [pack protection](docs/pack-protection-implementation.md) for selected parts, trip values and validation scope. The DRV2625 custom symbol currently uses the YFF nine-ball pin map with no footprint assigned. M2003 uses TSSOP20. Battery count, capacity and runtime target remain open.

Firmware is not implemented or flashed for the bracelet. The schematic accommodates the inspected robot loader; unchanged-binary operation, UART power sequencing, temperature supervision, charging and physical behavior still need verification. Attitude-to-haptic mapping remains open around the user's sensory-feedback concept.

`tools/check_connectivity.py`, `tools/check_usb_power.py` and `tools/check_pack_protection.py` audit a freshly exported XML netlist. One-time construction scripts refuse to overwrite their target revision; edit native files in KiCad. Previous native circuits are retained under `hardware/backups/`, including `before-pack-protection/`.

## References

- [Nuvoton M2003 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_M2003_Series_EN_Rev1.00.pdf).
- [TI DRV2625 datasheet](https://www.ti.com/lit/ds/symlink/drv2625.pdf).
- [TI TPS22918 datasheet](https://www.ti.com/lit/ds/symlink/tps22918.pdf).
- [ESP32-C6-MINI-1 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf).
- [ExpressLRS backpack telemetry](https://www.expresslrs.org/software/backpack-telemetry/).

Power/USB source details and loader provenance are linked from the implementation documents.

The proposed [VLV041235L actuator and draft flex contact footprint](docs/lra-candidate.md) are documented separately; the schematic actuator placeholders remain pending final selection.

The [dimensional pod study](mechanical/pod-study/README.md) uses the user's measured 195 mm wrist circumference. Revision C proposes 20 x 34 x 10 mm regular shells and a 24 x 52 x 10 mm main shell, with a central actuator opening, optional cells bonded to the lid's inner face, and main-pod button/RGB window provisions. These are packaging envelopes; PCB outlines, cells and wrist fit remain open.

SW3 is the accessible wake/off button. D1 is a discrete common-anode RGB status LED on GPIO4/5/15, with individual resistors and default-off pullups; exact LED and switch mechanical parts remain open. See [standby and controls](docs/standby-and-controls.md). Indication firmware is not implemented.

The proposed [301230 / 90 mAh cell](docs/cell-candidate-301230.md) is being assessed for one cell per pod (720 mAh per wrist with eight). The study C cell envelope is 2 mm shorter than this nominal cell, and the main pod still needs a cell allocation; exact cell dimensions and current ratings are pending.
