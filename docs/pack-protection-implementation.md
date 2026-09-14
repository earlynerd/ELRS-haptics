# Eight batteries with built-in protection

> Project update (2026-09-13): active sources are `hardware/main/` and `hardware/satellite/`. Main references are unchanged; historical satellite references map to the one universal design in [PCBA projects](pcba-projects.md). Any combined-board placement/count or verification statements below describe the earlier checkpoint; [current routing status](pcb-routing.md) supersedes them.

Native revision 0.5 follows the user's choice to use eight protected 90 mAh pouch batteries, one per pod, with their factory PCMs intact. The YDL301230 protected assembly is the working example: 3 x 12 x 32 mm excluding leads/connector. This supersedes the central S-821AAAC circuit.

## Implemented connectivity

- J200-J207 pin 1: protected PACK+ through F100-F107 to shared VBAT.
- J200-J207 pin 2: protected PACK- to system GND. Never connect raw cell negative to GND around a low-side PCM.
- VBAT directly reaches BQ25186 U11 BAT pin 2, C36 and J3 pin 1. It is pad 4 of the five-pad harness.
- U27, Q6, Q7, R54-R56 and C44 are removed. The old child sheet and checks are archived in `hardware/backups/before-protected-cells/`. Unused library assets and source datasheets are historical, not populated parts.
- BQ25186 charging/ship mode, TPS63802 regulation, TPS22918 pod power control, button and RGB remain.

The factory PCMs are external to the PCB schematic, represented at the battery interface. No raw-cell bypass connection is provided. All eight branches are planned populated; fuse part/rating and solder-pad footprints remain open. The battery itself is an off-board assembly, not the MPN of the J200-J207 PCB interface.

## Capacity, current and recovery

Eight 90 mAh batteries give 720 mAh / 2.664 Wh nominal. The YDL example permits 45 mA continuous discharge per cell, giving 360 mA aggregate with equal sharing. Its 18 mA standard and 45 mA maximum charging currents correspond to 144/360 mA with eight equal branches. Charger settings remain unimplemented; these are not defaults for an unknown active branch count.

Each PCM can disconnect and reconnect independently. Remaining branches carry the load/charge current. Individual PCM overcurrent protection does not reproduce the former shared 1.93 A cutoff. Retain local fuse provisions; finalize their ratings against the wiring, battery PCM and actual loads. Check depleted-cell charging, independent cutoff, reconnection and sharing with physical samples. The YDL PDF and listing contain conflicting PCM current figures, so those thresholds are not treated as a verified system cutoff.

## Additional bulk capacitance

Each pod adds a 22 uF 10 V X5R 0805 capacitor on POD_3V3 (C103 through C173 in increments of 10), alongside its existing local capacitors. The total switched-rail capacitance is 266.6 uF nominal. C42 changes from 1 nF to 4.7 nF for approximately 8.65 ms typical 10-90% rise and 81.6 mA capacitor-only startup current, using TPS22918 Equation 3. Effective capacitance/DC bias, startup load and discharge timing need physical checks; capacitor MPNs remain open.

## Evidence

`tools/check_connectivity.py`, `tools/check_usb_power.py` and `tools/check_protected_cells.py` pass against the fresh 269-component XML netlist. `tools/check_pack_protection.py` remains a compatibility entry point to the new checks. ERC: zero errors and zero warnings across 13 active sheets. Reports are in `hardware/verification/`; current previews are in `hardware/preview/protected-cells/`.

Sources: [YDL datasheet](https://ydlbattery.com/cdn/shop/files/YDL-301230-90mAh-specification.pdf?v=17344537468879431347), cached as `hardware/datasheets/YDL301230.pdf`; [TI TPS22918](https://www.ti.com/lit/ds/symlink/tps22918.pdf), section 8.3.2. Verification covers the PCB interfaces and nominal calculations, not external PCM functionality, firmware, PCB layout or physical qualification.
