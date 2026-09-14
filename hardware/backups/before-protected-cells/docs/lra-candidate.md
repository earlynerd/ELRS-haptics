# VLV041235L candidate and flex contact footprint

2026-09-12: User proposed Vybronics VLV041235L with matching board solder pads. It remains a candidate; M1–M8 have not been changed from placeholders.

[DigiKey listing](https://www.digikey.com/en/products/detail/vybronics-inc/VLV041235L/12323578): 1670-VLV041235L-ND, 569 listed in stock when checked, USD 3.90 at quantity one and USD 3.458 at quantity ten. These are a dated web snapshot, not reserved inventory.

[Vybronics product page](https://www.vybronics.com/linear-lra-vibration-motors/v-lv041235l) explicitly supports direct PCB attachment through double-sided solder contacts on the flex tail, using hot-bar soldering. Its body is 12 x 4 x 3.5 mm, with Z-axis motion, 240 Hz resonance, 1.8 Vrms rating and 60 mArms maximum rated current. The supplied 3M 4905 adhesive is shown separately in the drawing; allow its thickness in the installed assembly. Secure the body to the pod/PCB mechanically rather than supporting it by the electrical joints.

The [A/2 datasheet](https://www.vybronics.com/wp-content/uploads/datasheet-files/Vybronics-VLV041235L-datasheet.pdf) is cached as `hardware/datasheets/VLV041235L.pdf`. Drawing page 10 shows 0.8 x 1.8 mm contacts with a 1.0 mm gap, giving 1.8 mm center pitch. The solder contacts are on a projecting flex tail, not underneath the metal body.

`HapticBracelet:Vybronics_VLV041235L_FPC_Contact_Draft` provides proposed 1.0 x 2.2 mm PCB lands on that pitch. The extra land area is an engineering allowance for local soldering, not a manufacturer recommended land pattern. F.Fab depicts the nominal contact rectangles. There are no paste apertures: this draft assumes local attachment after ordinary PCB assembly, and does not imply whole-actuator reflow qualification. Pad numbering is project-assigned for the two driver outputs; it is not a manufacturer polarity designation.

The footprint deliberately covers only the two contact lands. It has no body courtyard or fixed actuator location because flex routing and housing mounting remain to be chosen. Check a sample's contact alignment, adhesive stack, solder access and flex strain before assigning the footprint for manufacture. A hot-bar connection is manufacturer-described; a hand-iron attachment using accessible upper contacts is a prototype assembly proposal that still needs a trial.

## Working pod packaging concept

The user proposed a central actuator with a surrounding PCB opening, allowing the LRA and its housing mounting seat to project through the board plane. Use this as the working concept, with the actuator bonded to the wrist-facing housing and its flex contacts landing on the adjacent PCB edge. Size the opening around the actuator, adhesive, seat, assembly tolerances and flex routing rather than the bare metal body alone. This is a packaging proposal; no dimensioned PCB outline or mechanical CAD is implemented yet.

The [dimensioned packaging study B](../mechanical/pod-study/README.md) sketches a 7 x 15 mm opening within provisional regular and main pod envelopes, using the user's 195 mm wrist circumference. Per the user's correction, cells bond directly to the lid's inner face with open clearance below; there is no supporting shelf or separate cell compartment. All dimensions other than wrist circumference remain proposals. Native PCB outlines are still unchanged.

Leave the surrounding volume available for circuitry and optional thin pouch cells. Cell envelopes must include sealed edges, tabs and manufacturer-required clearance; the lid supports each bonded cell, keeping it clear of the actuator and PCB cutout edge. A rigid actuator mounting seat is the initial concept; a compliant contact plate remains an optional experiment.

Use Myo-inspired flexible links between rigid pods. The exact link geometry and material are open. A proposed printed implementation uses replaceable TPU links with mechanical capture in the rigid shells, and slack, strain-relieved wiring through the links. Provide both bending and circumference expansion; wire slack must accommodate the full extension. Adafruit's [firsthand Myo teardown](https://learn.adafruit.com/myo-armband-teardown/inside-myo) documents the rubber connection and elaborate flex PCB, not a print-ready link geometry for this project.

## Protector sourcing result

The initial S-821AAAI sourcing question was resolved by the user's selection of stocked S-821AAAC-H8T7S for the prototype, explicitly accepting its 4.590 V overcharge threshold. It is now implemented as U27. See [sourcing history](protection-sourcing.md) and [circuit implementation](pack-protection-implementation.md) for the exact choice and its limitations.
