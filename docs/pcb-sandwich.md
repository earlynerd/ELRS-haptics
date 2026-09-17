# PCB-faced pods and TPU spacer

Current mechanical layout, 2026-09-15. Both active PCB masters use the **20 × 46 mm, R2.5** outside contour of the regular pod in `tools/build_myo_flat_v011.py`. The enlarged integrated main shell is superseded for this construction. Electrical parts remain at the user's saved positions; this change establishes the mechanical boundary for further placement.

The universal pod PCB forms the skin-facing plate, with the VLV041235L attached on its inward face using the supplied peel-and-stick tape. Its former actuator cutout is removed. A dashed 4 × 12 mm rectangle on Dwgs.User is a proposed body location in the former opening; the existing M1 flex-contact lands are preserved and still need arranging for that attachment. Board thickness remains 0.8 mm in the active four-layer masters; thinner skin plates remain an experiment rather than an applied stackup change.

The controller PCB forms the upper face on pod 0. The other seven pods use blank upper plates with the same contour and screw pattern. Those blank plate manufacturing files and the new TPU spacer CAD are not yet generated. Pod 0 retains no battery or external NTC. All seven other cells remain bonded to the upper plate, clear of the lower electronics and LRA.

## Outward-facing user button (2026-09-17)

SW3 is Panasonic **EVPAWBD4A**, a 3 × 2 × 0.6 mm top-push tactile switch with 1.6 N operating force. It is on **B.Cu**, at the existing saved centre (50.1, 61.1) mm, facing out of the pod. TS/MR-to-GND connectivity is unchanged. The project footprint uses the manufacturer's terminal-with-cutout land pattern: two 0.55 × 1.5 mm pads, 2.7 mm inner gap, and 80% paste area for a 0.1 mm stencil. Keep exposed copper and vias out of the central 1.9 × 2 mm underside region.

The footprint includes `hardware/HapticBracelet.3dshapes/EVPAWBD4A_nominal.step`. This is a simplified datasheet-derived model, not manufacturer CAD: nominal 3 × 2 mm body, 3.5 mm terminal span and 0.6 mm total height; terminal cutouts and internal geometry are omitted. A flexible protective cover remains a proposed mechanical follow-up, requiring a fit/feel trial. Routing to the relocated pads remains part of the ongoing board layout.

The replacement passes ERC and adds no DRC findings relative to the saved input. The controller still has 20 existing DRC findings, 144 opens and two unrelated schematic parity findings (Q1 footprint mismatch and extra U15). Evidence and the rendered outer face are in `hardware/verification/sw3-evpaw/`; input backups are in `hardware/backups/pre-sw3-evpaw-20260917/`.

## Contact-band drawings

- **Cmts.User, solid:** inner edge of the proposed 1.2 mm-wide TPU contact strip. Keep this perimeter strip free of components and exposed solder on the inward face, except at the intentional corner standoff reliefs.
- **Dwgs.User, dashed:** component-placement limit at 1.5 mm from the outside edge, allowing a further 0.3 mm margin.
- **Cmts.User, dashed circles:** proposed Ø4.6 mm local relief around each standoff solder land. The mounts and reliefs intentionally overlap the contact band so the standoffs pass through the TPU frame. The relief leaves 0.45 mm to each adjacent straight board edge; the corner shape and local TPU web still need resolving in spacer CAD.

These are mechanical drawing guides, not copper keepout zones or changes to the electrical clearance rules. Covered copper can remain beneath the TPU. Harness exits and the USB opening will need local spacer relief once placement is settled. The 1.2 mm strip derives from the previous shell wall; compression, print tolerances and retention still need a coupon trial.

## Four-corner fastening

Coordinates below are relative to the upper-left of either board, with Y increasing downwards:

| Reference | X (mm) | Y (mm) |
| --- | ---: | ---: |
| H1 | 2.75 | 2.75 |
| H2 | 17.25 | 2.75 |
| H3 | 2.75 | 43.25 |
| H4 | 17.25 | 43.25 |

The lower board uses **M1.6 solderable closed-base standoffs**, with a Ø3.3 mm body and Ø4 mm electrically isolated solder land. No mounting hole or locating spigot penetrates the skin-facing board. The land and segmented paste geometry come from KiCad's Würth WA-SMSI 97730606330 footprint and the [manufacturer drawing](https://www.we-online.com/components/products/datasheet/97730606330R.pdf). The project footprint deliberately has no height-specific 3D model or final MPN. The reference part is 6 mm high, but that height is **not selected** for the bracelet: the LRA and a 3 mm cell already exceed 6 mm wherever their bodies overlap.

The controller plate has **Ø1.8 mm NPTH screw-clearance holes**, with Ø4.5 mm courtyard envelopes on both faces for the screw head and mating standoff. Screws enter from the outside; controller components face into the pod. The corner pattern is symmetric under flipping the upper plate. Final standoff height, screw length/head and TPU compression remain open. The standoffs should set the plate separation; the cell is not part of the clamping load path.

## Verification

`tools/verify_split_projects.ps1` refreshes native reports and runs `tools/check_pod_faces.py`. It compares electrical component values, connectivity, placements, pads and routes against the immediately preceding user-saved sources, checks both outlines and drawing bands, and checks the four mounting sites. No DRC exclusions were added.

- Both schematics: zero ERC and zero schematic/PCB parity issues.
- Universal pod: 201 segments, 42 vias, zero DRC violations and zero opens.
- Controller: 146 opens and 20 DRC findings during placement. These include the upper mounts overlapping the ESP32 area; moving the mounts outward cleared the lower-right mount/USB courtyard overlap. Existing component-to-component clashes are retained for the user's placement work.

Sources before this edit are preserved in `hardware/backups/pre-pod-faces-20260915/`. The mounting manifest is `hardware/mounting-layout.json`; previews and preservation reports are under `hardware/verification/pod-faces/`. Earlier enclosure CAD remains historical geometry, not a fit-qualified model of this sandwich.
