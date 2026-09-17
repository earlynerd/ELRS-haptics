# Two PCBA projects: stacked controller and universal pod

One wrist uses **one controller daughterboard and eight identical universal pod PCBAs**. The main housing contains pod 0 with the controller stacked above it. It has no battery or external thermistor. Pods 1-7 each carry a protected pouch battery and external thermistor. All eight pod boards have the same fitted circuitry; only external battery/NTC wiring and JP1 selection differ.

## Editable sources

| PCBA | Project | Quantity |
| --- | --- | ---: |
| Controller daughterboard | `hardware/main/main.kicad_pro` | 1 |
| Universal pod | `hardware/satellite/satellite.kicad_pro` | 8 |

The existing directory names are retained to preserve KiCad project links and shared libraries. There is no separate main-pod haptic circuit or PCB variant.

The controller has 48 electrical footprints plus four screw-clearance sites H1-H4 and five sheets: ESP32/pod power switch, stacked pod interface, charger/regulator, USB, and controller support. J101 now feeds the first external M2003 through R42. The former local M2003/DRV2625/LRA, ICE connector, cell branch and NTC circuitry are removed from the daughterboard.

The universal board retains all 24 electrical footprints, component values, electrical connections and routing, with four M1.6 solderable standoff sites H1-H4 added. U1 is its M2003, U2 the driver, M1 the actuator, J3 local ICE, J4 battery, J5 NTC, and F1 the battery branch fuse. Leave J4/J5 unwired on pod 0; keep the identical PCBA population.

## Five-contact stack and harness

Connect controller J101 to pod 0 J1 pin-for-pin. Connect each pod J2 to the next pod J1. Pod 7 J2 remains uncabled. There are seven inter-pod harness gaps plus the local stacked-board connection; the clasp gap remains unwired.

| Pin | Function at controller J101 |
| --- | --- |
| 1 | +3V3_POD output to all eight pod MCUs/drivers |
| 2 | GND |
| 3 | RING_D0: ESP TX through R42 to pod 0 RX |
| 4 | VBAT: seven protected cell branches to charger BAT |
| 5 | RING_RETURN: end pod TX back to ESP RX |

Existing five-pad footprints remain the electrical stack interface. Both PCB masters now use the full 20 × 46 mm pod face, with four shared corner fasteners and TPU contact-band guides. The actuator bonds to the unbroken lower board with its factory tape. See [PCB sandwich construction](pcb-sandwich.md) for exact dimensions, mounting footprints and open stack-height work.

## JP1 configuration

| Pod positions | JP1 configuration |
| --- | --- |
| 0-6 | Factory 1-2 NORMAL bridge retained |
| 7 | Cut 1-2 and bridge 2-3 END |

Pad 1 is downstream return, pad 2 upstream return, pad 3 local TX_OUT. Never bridge all three. The first pod behaves exactly like the other intermediate nodes; the ring still has eight M2003 nodes and the loader protocol is unchanged.

## Power and temperature

The controller retains BQ25186, TPS63802, TPS22918, SW3 and RGB D1. It draws battery power through J101 pin 4. Cycling +3V3_POD resets all eight pod circuits while the ESP32 remains on its own regulated rail.

Seven 90 mAh cells give 630 mAh nominal. The user's 301730/160 mAh suggestion is an alternative candidate: seven would give 1,120 mAh. No exact 301730 model, protected-pack dimensions or electrical limits have been selected or verified. See [cell candidate](cell-candidate-301230.md).

Firmware must retain eight-node enumeration but expect required cell-temperature sensors only on pods 1-7. Pod 0's unwired NTC input must not be treated as a failed required sensor. Seven-cell charge/load settings and sensor policy remain firmware work; this migration changes schematics and documentation only.

## Verification and layout status

Both projects have zero ERC and schematic/PCB parity issues. The universal pod retains 201 segments, 42 vias, zero DRC violations and zero opens. The controller retains the user's latest placement, with 146 opens and 21 DRC findings including mounting-area conflicts.

`tools/verify_split_projects.ps1` runs native checks and `tools/check_pod_faces.py`, which verifies circuit, placement, pad and route preservation against the 2026-09-15 pre-edit sources. Layout completion is reported separately from preservation.

The integrated design is backed up in `hardware/backups/pre-stacked-controller-20260914/`. The incomplete routing candidates in `hardware/verification/main-routing/` belong to that superseded integrated board and must not be applied to the daughterboard.

A later derived manufacturing panel may combine one controller and eight universal boards. No panel or fabrication release is created by this schematic migration.
