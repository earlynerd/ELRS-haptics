# Two PCBA projects

One wrist uses one main board and seven copies of one universal satellite. Each design has separate `.kicad_pro`, `.kicad_sch` and `.kicad_pcb` files. Custom libraries remain shared under `hardware/`.

## Main

`hardware/main/main.kicad_pro` contains 70 components across five sheets. The top sheet preserves the user's redraw. Child sheets contain wired functional circuits. Retained main references are unchanged, including U18/U3/M1 for the local MCU/driver/LRA, J101 for CHAIN OUT, and J200/F100 for its protected battery branch.

The existing 21 × 61 mm envelope, antenna recess and actuator cutout are preserved. The applied main placement preserves the user edge anchors and groups supporting parts near their ICs; see [placement checkpoint](main-board-placement.md). J1 is now TC2030 ICE, replacing J102; C29/C30 are removed. Routing remains pending.

## Universal satellite

`hardware/satellite/satellite.kicad_pro` preserves the user's pod-6 circuit and placement, renumbered locally. All 23 existing component values and footprints are unchanged. JP1 adds a copper selector footprint, excluded from the schematic BOM.

| Function | Satellite reference | Previous pod-6 reference |
| --- | --- | --- |
| MCU / driver / actuator | U1 / U2 / M1 | U24 / U9 / M7 |
| CHAIN IN / CHAIN OUT | J1 / J2 | J124 / J125 |
| ICE / battery / optional NTC | J3 / J4 / J5 | J126 / J206 / J127 |
| Branch fuse | F1 | F106 |
| RX link / TX resistor | R1 / R2 | R160 / R161 |
| RX / TX pullups | R3 / R4 | R162 / R163 |
| NTC bias / SDA / SCL pullups | R5 / R6 / R7 | R165 / R20 / R21 |
| MCU 100n / 10u / 22u | C1 / C2 / C3 | C160 / C161 / C163 |
| NTC filter / driver bypass / REG / driver bulk | C4 / C5 / C6 / C7 | C162 / C23 / C24 / C25 |

References are local: satellite U1 is the M2003; main U1 is the ESP32. Older component-specific documents use archived eight-pod numbering; use this table for satellite references.

## JP1 configuration

| JP1 pad | Circuit |
| --- | --- |
| 1 | RETURN_DOWN, J2 pin 5 |
| 2, centre | RETURN_UP, J1 pin 5 |
| 3 | TX_OUT, R2 pin 2 and J2 pin 3 |

The stock three-pad footprint has a factory copper bridge between 1 and 2. The pad-1 triangle identifies the left pad in the current front view.

- Satellites 1–6: retain **1–2 NORMAL**. Downstream return passes upstream without joining local TX.
- Satellite 7: **cut 1–2, then solder 2–3 END**. Local TX feeds the upstream return; downstream return is isolated.

Never bridge all three. Returning an END board to NORMAL means removing 2–3 and restoring 1–2. Check continuity across the cut and selected bridge before use. There is no end-only resistor or alternate satellite PCB/BOM.

## Harness

Connect main J101 to satellite 1 J1, then each satellite J2 to the next J1, pin-for-pin. Last satellite J2 is unused; no wires cross the clasp. Redundant main J100 is removed; the ESP32 feeds the local pod on-board.

| Pin | Function |
| --- | --- |
| 1 | +3V3_POD, switched electronics supply |
| 2 | GND |
| 3 | UART RX at IN, UART TX at OUT |
| 4 | VBAT, protected battery-output bus |
| 5 | Serial return selected by JP1 |

Forward UART traffic still visits all eight MCUs. Only the last satellite drives the return to ESP RX. Loader UART pins are unchanged. Cycle switched pod power for whole-chain reset; each ICE connector retains only its own MCU reset. Five wires are fitted per link. The 2 mm pitch and 1.4 x 1.6 mm lands remain; each bank is 2 mm shorter.

## Preservation and checks

The saved redraw retained all 261 components, values and footprints from revision 0.9. Its only pin-connectivity changes were split `3V3`/`+3V3` and `POD_3V3`/`+3V3_POD` aliases. New projects consistently use `+3V3` and `+3V3_POD`. An obsolete dangling QOD wire/label was removed without changing the connected discharge circuit.

`tools/check_split_projects.py` compares inventories, values, footprints and connected pin sets against revision 0.9, allowing the requested return split, removal of main J100 and Q5/R6/R7/R44/C40, and removal of the old reset pad and compaction to five pads (old VBAT/return pins 5/6 become 4/5), plus removal of the USB CC/current-switch circuit, two new CC pull-downs and direct VBUS-to-charger wiring. It checks both selector states, every PCB pad net, preserved component placement, board outline/cutout count and satellite routing constraints. The physical 1–2 bridge is a KiCad net tie, intentionally joining the two return nets in NORMAL mode.

Main has 70 components, 196 open connections, three silk/library warnings and zero schematic/PCB parity issues. One ERC reset-input item remains because the M2003 internal pull-up is not represented in the symbol; satellite ERC, DRC and opens remain zero. The driver reset/supply tie is 0.1524 mm. This is migration evidence, not manufacturing or hardware qualification.

The combined project is archived intact. A later JLCPCB panel will be derived from the two masters after main routing is complete.
