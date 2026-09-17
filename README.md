# Haptic bracelet

Battery-powered attitude feedback for FPV flying, with eight haptic actuators around each wrist. An ESP32-C6 receives telemetry over ESP-NOW and controls eight M2003FC1AE/DRV2625 pods using the music robot's UART ring architecture. Each wrist uses a seven-cell parallel battery group: protected cells in pods 1-7, with no cell in the stacked controller pod. Seven 90 mAh cells give 630 mAh; 301730/160 mAh cells are an alternative candidate pending selection and fit checks.

## Open the two KiCad projects

| PCBA | Editable project | Quantity per wrist |
| --- | --- | --- |
| Controller daughterboard | [hardware/main/main.kicad_pro](hardware/main/main.kicad_pro) | 1 |
| Universal pod | [hardware/satellite/satellite.kicad_pro](hardware/satellite/satellite.kicad_pro) | 8 |

Each project has its own schematic and PCB. Shared custom libraries live under `hardware/`. Use KiCad 10; native files are the editable source of truth.

**JP1 defaults to 1-2 NORMAL. On the last satellite, cut the 1-2 copper bridge and solder 2-3 END.** Its centre pad feeds the upstream return, selecting downstream return or local TX. Never bridge all three. See [project structure and jumper configuration](docs/pcba-projects.md).

The former eight-island project is retained under `hardware/archive/combined-project/`, with the untouched starting snapshot and hashes under `hardware/backups/before-two-projects/`. Close any editor still showing the former root project and open the new projects above for further work.

## Schematics and layout

The main project has five sheets: the user's redrawn controller/power-switch top sheet, stacked universal-pod interface, charger/regulator, USB, and controller support. The satellite has one sheet. Support components are wired around their ICs; labels serve power rails and circuit/sheet interfaces.

[Main schematic PDF](hardware/verification/project-split/main.pdf) · [Satellite schematic PDF](hardware/verification/project-split/satellite.pdf) · [Satellite layers](hardware/verification/project-split/layers.png)

The redraw audit found no deleted components, changed values or changed footprint assignments. The new `+3V3` and `+3V3_POD` power symbols had split the old `3V3` and `POD_3V3` nets; those names are now consistent. An obsolete dangling QOD wire/label was removed. Fresh connectivity checks preserve the verified circuit apart from the documented selector, five-pad harness, reset removal and USB simplification.

Both boards now use the pod's full **20 × 46 mm, R2.5** outside contour. The universal skin-facing board has four M1.6 SMT standoff lands and no actuator cutout; the controller plate has matching 1.8 mm screw-clearance holes. The VLV041235L retains its factory adhesive. Drawing layers mark the TPU contact band and placement margin. See [PCB sandwich construction](docs/pcb-sandwich.md).

All existing electrical positions and routes are preserved, including the user's latest main placement. Both projects have zero ERC and schematic/PCB parity issues. The universal board retains 201 segments, 42 vias, zero DRC violations and zero opens. The controller has 146 opens and 21 DRC findings during placement, including clashes around the new mounts. Both active stackups remain four-layer, 0.8 mm; standoff height and thinner skin-plate trials are open. See [current architecture](docs/pcba-projects.md).

## System decisions

- Five wires run through seven gaps: switched supply, GND, forwarded UART data, protected VBAT and serial return. The compact five-pad banks use pin 4 for VBAT and pin 5 for return. The eighth gap has no conductor; the current housing uses paired planar U-flexures at all eight gaps and closes the flat strip at a seam inside the main shell.
- Each pod contains an M2003FC1AE, DRV2625YFFR and VLV041235L. PF0/PF1 preserve the loader UART/ICE pins. Driver NRST follows VDD; hard recovery cycles pod power.
- USB-C uses two 5.1k CC pull-downs and connects to ESP32-C6 native Serial/JTAG on GPIO12/13. VBUS directly feeds the charger; its internal limit replaces external USB current-switch circuitry. BQ25186 charges the protected pack, TPS63802 supplies 3.3 V, and TPS22918 switches all pod electronics.
- Every pod has local bulk capacitance, removable UART links, ICE pads and an optional cell thermistor interface. Each protected battery feeds VBAT through its local branch fuse; factory PCMs stay fitted.
- Main SW3 is the wake/ship button; D1 is the RGB status LED. Firmware must manage charging and UART pin states around power changes.

See [ring and power sequencing](docs/ring-pods.md), [power architecture](docs/power-architecture.md), [USB implementation](docs/usb-power-implementation.md), and [DECISIONS.md](DECISIONS.md).

## Firmware

The initial [bracelet firmware](firmware/README.md) now includes an ESP32-C6 controller, an M2003 haptic-pod application, the borrowed music-robot LDROM build, and portable protocol tests. The controller decodes MSPv2-wrapped CRSF attitude telemetry from a configured ExpressLRS Backpack sender, requires exactly eight enumerated pods, and drives a configurable absolute-attitude map at 50 Hz. The M2003 application controls one DRV2625 over local I2C and keeps the robot ring framing, enumeration, loader mailbox, image layout, and update packager.

The stacked hardware retains eight nodes but requires cell-temperature supervision on pods 1-7 only; that firmware policy and seven-cell charging limits remain to be implemented.

The first build defaults are deliberately inert until a Backpack source MAC is configured. Charging remains disabled. This code has been compiled, but it has not been flashed or exercised on bracelet hardware; see [firmware interfaces and open qualifications](firmware/protocol.md).

For staged hardware work, the controller now has a native USB [bring-up console](firmware/BRINGUP.md). It supports partial-ring enumeration, per-pod status and bounded single-actuator pulses without relaxing the eight-pod requirement for normal telemetry-driven output.

## Next work and manufacturing

Next establish the stacked daughterboard envelope, contact arrangement and placement before routing. JLCPCB is preferred; a later **derived panel** may combine one controller and eight identical universal pods. [hardware/panel](hardware/panel/README.md) is reserved for that output. No manufacturing panel or fabrication release has been created.

The exact production stack, USB geometry, enclosure supports/links, physical fit, battery sharing, power sequencing and haptic behavior remain to validate. Firmware is implemented as an initial buildable slice but has not been flashed. Loader compatibility is now build-verified against the inspected robot sources, not yet demonstrated on the bracelet ring.

`tools/verify_split_projects.ps1` refreshes both netlists, ERC/DRC reports and preservation checks. Current evidence is in `hardware/verification/project-split/`. Older construction scripts and routing directories document earlier revisions; do not use them to regenerate the active designs.

## References

- [Nuvoton M2003 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_M2003_Series_EN_Rev1.00.pdf).
- [TI DRV2625 datasheet](https://www.ti.com/lit/ds/symlink/drv2625.pdf).
- [TI TPS22918 datasheet](https://www.ti.com/lit/ds/symlink/tps22918.pdf).
- [ESP32-C6-MINI-1 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf).
- [ExpressLRS backpack telemetry](https://www.expresslrs.org/software/backpack-telemetry/).

Power/USB source details and loader provenance are linked from the implementation documents.

The proposed [VLV041235L actuator and draft flex contact footprint](docs/lra-candidate.md) are documented separately; the actuator is assigned to main M1 and satellite M1.

The [dimensional pod study](mechanical/pod-study/README.md) uses the measured 195 mm wrist. Revision D proposes 20 x 38 x 10.5 mm regular shells and a 24 x 64 x 10.5 mm main shell, with one protected 3 x 12 x 32 mm battery bonded inside every lid. The main battery is allocated away from the antenna and USB/button/RGB end. Width around the wrist stays unchanged. These are nominal shell envelopes; revision 0.6 implements PCB outlines and fit coupons but has no physical fit evidence.

The current [Myo-inspired flat housing v0.11](mechanical/myo-flat-v0.11/README.md) supports the main-pod TPU against its sidewalls down to the satellite ends, so all sixteen free U-folds use the same geometry. Its main clamshell is cut from one rounded rectangular envelope, with integrated end walls and recessed M2 x 8 mm screws. Satellite shells, lids and joint geometry are preserved. The approximately 239 x 72 mm strip targets PET-GF15/TPU on the H2D; local support remains necessary under the terminal roof and wall feet. STL/3MF, STEP and main-transition/closure coupons are included. CAD, mesh and preservation checks pass; the user's slicer screenshot is v0.10 evidence, while v0.11 slicing, fit and flexure testing remain open. Earlier releases are preserved.

SW3 is the accessible wake/off button. D1 is a discrete common-anode RGB status LED on GPIO4/5/15, with individual resistors; the placement selects LTST-C19HE1WT and EVQPUJ02K, respectively. See [standby and controls](docs/standby-and-controls.md). Initial firmware uses blue for waiting, green for fresh telemetry/output, and red for a ring fault; final indication and button behavior remain open.

The [YDL301230-class battery baseline](docs/cell-candidate-301230.md) provides 630 mAh and 315 mA continuous aggregate current with seven equally sharing cells. Factory PCMs stay intact. New 22 uF pod capacitors and C42=4.7 nF ramp control are documented in [ring power](docs/ring-pods.md).
