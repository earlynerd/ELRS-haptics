# Pod packaging study C

User wrist circumference: **195 mm**, supplied on 2026-09-12. Axial width has not been specified; all other dimensions below are design proposals. View `pod-dimensions.svg` or `pod-dimensions.png`. Regenerate the SVG and parameter record with `python tools/sketch_pods.py` from the project root.

| Envelope | Around wrist | Along arm | Radial thickness |
| --- | ---: | ---: | ---: |
| Regular pod shell | 20 | 34 | 10 |
| ESP32/USB pod shell | 24 | 52 | 10 |
| Regular PCB | 17 | 31 | 0.8 |
| Main PCB before antenna relief | 21 | 49 | 0.8 |
| Central PCB opening | 7 | 15 | through |
| Regular optional cell envelope, excluding lid adhesive | 16 | 28 | 3.0 |

All dimensions are mm. These are nominal flat packaging envelopes, not fabrication geometry or a demonstrated component placement. The main pod grows primarily along the arm to retain circumferential room for eight actuators. Both drawings center the actuator and link positions on the same axial datum. Rounded end contours and link symbols are illustrative; exact retention details are open.

## Actuator and cell stack

The opening leaves nominal 0.8 mm clearance per side around a proposed 5.4 x 13.4 mm housing mounting seat. The actuator's 4 x 12 mm metal body leaves another 0.7 mm per side on the seat. Allowance for the flex tail, its bend and solder access is still to be resolved using a sample. The flex is drawn symbolically rather than as a production contour.

Radial coordinates start at the flat inner skin-contact datum: inner wall z=0..1, actuator adhesive z=1..1.5, LRA body z=1.5..5, and a conservative separate 0.35 mm foam allowance up to z=5.35. The optional cell envelope occupies z=5.8..8.8, leaving 0.45 mm nominal clearance above the actuator foam allowance. A proposed 0.2 mm adhesive layer occupies z=8.8..9 and bonds the cell directly to the lid, which ends at z=10. There is no shelf or separate cell compartment. The PCB occupies z=2..2.8 with regular-pod component tops allocated below z=4.8. Local component and solder heights must be checked during placement.

The [Vybronics A/2 drawing, page 10](https://www.vybronics.com/wp-content/uploads/datasheet-files/Vybronics-VLV041235L-datasheet.pdf) gives the body, 0.5 mm adhesive and a separate 0.35 mm foam callout. The study reserves these additively until the actual assembled sample resolves their installed stack. The 10 mm thickness does not yet include changes needed for a curved contact surface, closure details or shell deflection.

Per the user's correction, bond the cell directly to the lid's inner surface above the electronics and actuator. The adhesive and lid support it, with open clearance underneath; do not add a cell shelf or compartment. **16 x 28 x 3.0 is an allocated envelope, not the nominal size of a cell to order**: the cell's tolerance, sealed perimeter, tabs, wiring, insulation and required expansion allowance must fit within it. The extra 0.2 mm for lid adhesive is an unselected design allowance. Leave enough lead slack to open the lid for assembly. No capacity or cell availability is assumed. Main pod has no cell allocation in this revision.

## Controller pod

Revision C adds provisional side access for the existing SW3 wake/off button and a lid window for D1 RGB status. Both sit near the USB end, away from the antenna. Symbols indicate packaging allocations, not selected component outlines. BOOT and RESET remain internal recovery controls. The LED is discrete common-anode RGB; its package and the button actuator still need selection.

The ESP32-C6-MINI-1 body is 13.2 x 16.6 x 2.4 mm per the [Espressif module datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf). Its antenna faces an axial end of the shell. The sketched relief indicates intent only; final copper, PCB and component clearances must follow the [ESP32-C6 layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/pcb-layout-design.html). Keep the antenna region clear of cells and metal covers. Body-loaded RF performance remains untested.

USB occupies a proposed 9 x 7 mm plan allocation at the opposite axial end, with opening and plug insertion room still dependent on the selected receptacle. MCU, driver and power blocks show area allocation only, not all 254 schematic components placed. Two-sided placement may be needed. No PCB outline has been changed.

## Circumference and flexible links

Seven regular widths plus one main width total 164 mm. Subtracting from the measured 195 mm leaves 31 mm, or 3.875 mm per gap. **That is a first flat-length budget, not a relaxed link dimension or a circular fit solution.** Wrist shape, chord/arc geometry, radial location of link anchors, tension and clearance change it. A circular equivalent of the measured circumference has radius about 31.0 mm, but a wrist is not circular and that radius is not specified as the final shell curvature.

Use seven Myo-inspired flexible links and one opening mechanical clasp between the final pod and main pod. Each wired link carries six conductors, including a passive serial return back along the chain; no conductor crosses the clasp. Opening the bracelet therefore leaves the electrical circuit intact. The 31 mm total gap budget above is now shared by seven flexible gaps plus the clasp; 3.875 mm each remains only an equal-gap first estimate. Final clasp width can differ, with the other gaps adjusted accordingly. Flexible links need mechanical capture and wire slack for full extension. Purple end blocks are conceptual interfaces, not dimensioned catches; the main/end variants will need a clasp feature on their free sides.

## Verification scope

Checked the manufacturer actuator drawing and module body dimensions. Rendered the generated SVG and visually inspected it for dimension-label overlap and readable section details. This study has no assembled CAD, boolean fit checks, routing validation, antenna validation or printed fit evidence. Its purpose is to choose packaging envelopes before PCB outlines and cells are fixed.
