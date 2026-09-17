> **2026-09-17: user's placement restored.** The assistant's functional-group refinement was reverted at the user's request. The active PCB exactly matches the pre-refinement backup, including the accepted SW3 replacement. The older report below remains historical.

# Main board placement checkpoint

The 69-footprint placement is applied to `hardware/main/main.kicad_pcb` (2026-09-13). It starts from the user's functional groups, incorporates J1 Tag-Connect and omits the intentionally removed C29/C30. The older `verification/main-placement/` proposal is historical.

![Main placement](../hardware/verification/main-recovery-pads/placement.png)

U1, J2, J101, J200, J103 and M1 retain their exact saved positions and rotations. The outline, antenna overhang and actuator opening are unchanged. Fitted components remain on the front; bare J3 recovery pads are on the underside. J1 sits beside the right side of the opening; its three locating holes clear copper and board edges. D1 now sits below the left side of the ESP32, in the space freed by the two removed switches. SW3 sits on the left; enclosure access must follow these control positions.

The charger and IN/SYS/BAT capacitors form a group below the left side of the opening. The buck-boost stage sits below that, with L1 beside its switching pins and feedback on the opposite side. The MCU occupies the lower middle; the driver sits beside the LRA contacts. USB protection stays near J2 and series resistors near the ESP32 USB pins.

## ESP recovery and local placement revision

SW1/SW2 are removed. J3 is a bare three-pad bank on B.Cu at (45.5, 55.0) mm: pin 1 EN, pin 2 GND, pin 3 BOOT/GPIO9. Pads are 1 mm diameter on 1.5 mm pitch, without paste; no connector is fitted. The roughly 4.5 x 3.9 mm courtyard includes readable underside legends. The preview shows this underside bank with dashed outlines, viewed through the board from above. Reserve an underside service opening here; the enclosure opening itself has not yet been modeled.

SW3 retains its left-facing side actuator. R3/C1 reset bias and R5 boot pull-up are retained. The USB resistors are now ordered D-/D+ below their matching pins, with I2C pull-ups to the left and boot pull-ups to the right. R42 is beside the ESP TX pin, instead of across the module. C1 and supply bulk C3 are repositioned along the left edge. D1 and its resistors occupy the former switch area. All footprints outside these 15 ESP-support parts remain at their prior locations.

Pad-centre distances: USB series resistors 1.74/1.70 mm; I2C pull-ups 2.02/1.85 mm; boot pull-ups 1.69/1.76 mm; UART series resistor 1.69 mm; reset C1 1.60 mm. These are placement distances, not routed lengths.

## Placement evidence

The repeatable search uses native pad positions, courtyard bounds, fixed anchors, orthogonal rotations and weighted critical connections. It is a constrained placement pass, not proof of a global optimum. The preview shows pads and courtyard bounds.

| Connection | Straight-line pad-centre distance |
| --- | ---: |
| TPS63802 to L1, each switching pin | 2.02 mm |
| TPS63802 input to C37 | 1.75 mm |
| TPS63802 output to C38 / C39 | 2.14 / 4.32 mm |
| BQ25186 IN / SYS / BAT capacitors | 1.51 / 1.90 / 2.70 mm |
| M2003 supply to C100 | 1.74 mm |
| DRV2625 supply to C5 / REG to C6 | 1.86 / 1.30 mm |
| ESP32 supply to C2 | 1.60 mm |

These are geometric distances, not routed lengths or loop inductance. Routing must keep local capacitor grounds short, join regulator control ground appropriately, separate feedback from switching nodes and maintain a continuous ground reference. Secondary bulk capacitors are less tightly constrained than primary bypass capacitors.

Native checks report zero schematic/PCB mismatches and no copper, courtyard, hole or edge-clearance errors. Three warnings remain: two ESP32 silkscreen/edge warnings and the existing ESP32 footprint/library difference. Main has 191 open connections, one existing driver NRST/VDD segment and no vias. One ERC item remains for the Tag-Connect open-drain reset output and M2003 input with its internal pull-up; it is recorded explicitly. Satellite validation remains clean and its source is unchanged.

## Files and next step

- Accepted positions: `hardware/main/placement-reference.json`.
- Preview and measurements: `hardware/verification/main-recovery-pads/`.
- Latest before-apply backup: `hardware/backups/pre-esp-recovery-pads-20260913/`.
- Initial user board: `hardware/backups/user-main-groups-20260913/`.
- Current native reports: `hardware/verification/project-split/`.

Routing remains pending. Start with regulator power loops and local decoupling, then USB; use F.Cu/B.Cu for signals, In1 GND and In2 power. Retain the 6 mil minimum and avoid via-in-pad. Local placement adjustments may be needed during routing.
