# Historical packaging study D

The dimensions below established the envelopes. [Revision 0.6 placement](../../docs/pcb-placement.md) and [fit coupons](../fit-mockup/README.md) now implement the next step. The native cutout is shifted 1 mm left and its flex lands are near an end, so the centred actuator and mid-side flex drawings here are superseded. USB/button/RGB footprints are now selected. These study images remain historical references rather than the latest component placement.

# Pod packaging study D

User wrist circumference: **195 mm**, supplied on 2026-09-12. Axial width has not been specified; all other dimensions below are design proposals. View `pod-dimensions.svg` or `pod-dimensions.png`. Regenerate the SVG and parameter record with `python tools/sketch_pods.py` from the project root.

| Envelope | Around wrist | Along arm | Radial thickness |
| --- | ---: | ---: | ---: |
| Regular pod shell | 20 | 38 | 10.5 |
| ESP32/USB pod shell | 24 | 64 | 10.5 |
| Regular PCB | 17 | 35 | 0.8 |
| Main PCB before antenna relief | 21 | 61 | 0.8 |
| Central PCB opening | 7 | 15 | through |
| Battery body, each of eight pods | 12 | 32 | 3.0 |
| Lid battery allocation, excluding adhesive | 14 | 34 | 3.5 |

All dimensions are mm. These are nominal flat packaging envelopes, not fabrication geometry or a demonstrated component placement. The main pod grows primarily along the arm to retain circumferential room for eight actuators. Both drawings center the actuator and link positions on the same axial datum. Rounded end contours and link symbols are illustrative; exact retention details are open.

## Actuator and cell stack

The opening leaves nominal 0.8 mm clearance per side around a proposed 5.4 x 13.4 mm housing mounting seat. The actuator's 4 x 12 mm metal body leaves another 0.7 mm per side on the seat. Allowance for the flex tail, its bend and solder access is still to be resolved using a sample. The flex is drawn symbolically rather than as a production contour.

Radial coordinates start at the flat inner skin-contact datum: inner wall z=0..1, actuator adhesive z=1..1.5, LRA body z=1.5..5, and a conservative separate 0.35 mm foam allowance up to z=5.35. The battery allocation occupies z=5.8..9.3, leaving 0.45 mm nominal clearance above the actuator foam allowance. A proposed 0.2 mm adhesive layer occupies z=9.3..9.5 and bonds the cell directly to the lid, which ends at z=10.5. There is no shelf or separate cell compartment. The PCB occupies z=2..2.8 with regular-pod component tops allocated below z=4.8. Local component and solder heights must be checked during placement.

The [Vybronics A/2 drawing, page 10](https://www.vybronics.com/wp-content/uploads/datasheet-files/Vybronics-VLV041235L-datasheet.pdf) gives the body, 0.5 mm adhesive and a separate 0.35 mm foam callout. The study reserves these additively until the actual assembled sample resolves their installed stack. The 10.5 mm thickness does not yet include changes needed for a curved contact surface, closure details or shell deflection.

Bond one protected 3 x 12 x 32 mm battery inside every lid; keep its factory PCM. The 14 x 34 x 3.5 mm allocation gives 1 mm around the body in plan and 0.5 mm additional radial allowance, plus 0.2 mm lid adhesive. These are provisional clearances, not supplier-qualified expansion or wire-bend allowances. Plan soldered protected-output leads, with the external connector removed; no pocket is allocated for the stock PH2.0 plug. Leave lead slack to open the lid, and keep PCM/tabs insulated and strain relieved. There is no separate compartment or shelf.

## Controller pod

Revision D retains provisional side access for the existing SW3 wake/off button and a lid window for D1 RGB status. Both sit near the USB end, away from the antenna. Symbols indicate packaging allocations, not selected component outlines. BOOT and RESET remain internal recovery controls. The LED is discrete common-anode RGB; its package and the button actuator still need selection.

The ESP32-C6-MINI-1 body is 13.2 x 16.6 x 2.4 mm per the [Espressif module datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf). Its antenna faces an axial end of the shell. The sketched relief indicates intent only; final copper, PCB and component clearances must follow the [ESP32-C6 layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/pcb-layout-design.html). Keep the antenna region clear of cells and metal covers. Body-loaded RF performance remains untested.

USB occupies a proposed 9 x 7 mm plan allocation at the opposite axial end, with opening and plug insertion room still dependent on the selected receptacle. MCU, driver and power blocks show area allocation only, not all 269 schematic components placed. Two-sided placement may be needed. No PCB outline has been changed.

## Circumference and flexible links

Seven regular widths plus one main width total 164 mm. Subtracting from the measured 195 mm leaves 31 mm, or 3.875 mm per gap. **That is a first flat-length budget, not a relaxed link dimension or a circular fit solution.** Wrist shape, chord/arc geometry, radial location of link anchors, tension and clearance change it. A circular equivalent of the measured circumference has radius about 31.0 mm, but a wrist is not circular and that radius is not specified as the final shell curvature.

Use paired Myo-inspired TPU U-flexures at all eight mechanical gaps and co-print them with the rigid pod shells as one claspless band. The electrical chain remains open: only seven gaps carry the current five-conductor harness, and no conductor crosses the eighth TPU seam. The old 31 mm remainder and 3.875 mm equal-gap value are flat-length estimates only. Revision 0.7 instead places the retained pod widths as tangent chords on a 195 mm circular skin reference and divides the remaining skin arc equally; wrist ovality, preload, wire slack, material stiffness and flexure fatigue remain physical checks.

## Verification scope

Checked the manufacturer actuator drawing and module body dimensions. Rendered the generated SVG and visually inspected it for dimension-label overlap and readable section details. This study has no assembled CAD, boolean fit checks, routing validation, antenna validation or printed fit evidence. Its purpose is to choose packaging envelopes before PCB outlines and cells are fixed.

## Revision D battery placement

Each regular shell grows 4 mm along the arm. The main shell grows 12 mm along the arm so its lid can carry the eighth battery between the antenna end and USB end. Circumferential widths stay 20/24 mm; radial height grows 0.5 mm for additional battery allowance.

Coordinates below use the shell's left/antenna-side end as x/y=0 in the plan drawing. Regular battery allocation: x=3..17, y=2..36; main allocation: x=5..19, y=22..56. The body fits centered inside each allocation. The main USB block starts at y=57; the antenna body ends at approximately y=6.6, leaving over 15 mm to the battery allocation. This is a conservative packaging separation, not an RF qualification. Module height outside the battery region is not constrained by the regular-pod 4.8 mm component ceiling. The eight LRAs/link anchors retain a common axial centerline when the pods are worn.

Dashed overlays in the plan show the lid-mounted batteries above the board, not PCB cutouts. The capacitor 0805 footprint fits the component height allocation in principle; full board placement, capacitor MPN, lid closure, lead exit and wrist curvature remain unresolved. `dimensions.json` records these allocations and eight-cell intent; no fabrication PCB outlines have been generated.
