# First PCB placement — revision 0.6

> Project update (2026-09-13): active sources are `hardware/main/` and `hardware/satellite/`. Main references are unchanged; historical satellite references map to the one universal design in [PCBA projects](pcba-projects.md). Any combined-board placement/count or verification statements below describe the earlier checkpoint; [current routing status](pcb-routing.md) supersedes them.

**Historical checkpoint:** current native files have advanced to the [four-layer routing revision 0.7](pcb-routing.md). The counts, pending selections and unrouted status below describe revision 0.6 only.

The native `hardware/archive/combined-project/haptic-bracelet.kicad_pcb` originated from this checkpoint, which contained **all 269 components on eight separate board islands**, with 250 schematic nets and no tracks. This is an editable placement/packaging pass. There are no panel rails, breakaway tabs, tooling holes or fabrication outputs.

Satellite boards are 17 × 35 × 0.8 mm. The main board has a 21 × 61 mm envelope; its upper edge is recessed 5.1 mm so the ESP32 antenna overhangs it. All openings are 7 × 15 mm, offset 1 mm toward the left in the plan view, with 0.5 mm corner chamfers. Outer corners have 0.7 mm chamfers. The shell envelopes remain 20 × 38 × 10.5 and 24 × 64 × 10.5 mm. The eight LRAs retain a common axial datum when worn.

The six-wire pads have 2 mm pitch and 1.4 × 1.6 mm copper lands; battery/NTC pairs use the same land dimensions and pitch. ICE pads use 1.27 mm pitch with 0.85 × 0.9 mm lands. All wire/probe pads omit paste apertures. The circuit retains both IN and OUT interfaces on every pod for circuit reuse; the main/end clasp-side interfaces are not a cable crossing the clasp. At this historical checkpoint only pod 7 had R53; current satellites use the universal JP1 selector.

The LRA body bonds to the housing floor, through the board opening. Its tail exits near the short end and turns to the side. Drawing-layer rectangles reserve the proposed tail path near the lower-right corner of each cutout. The contact footprint is rotated 90 degrees there. The land pitch is drawing-derived; the precise three-dimensional fold and soldering access require a sample. Do not support the actuator by its flex joints.

## Selected parts and footprint evidence

| Function | Selection | Placement evidence / remaining check |
|---|---|---|
| Eight haptic drivers | DRV2625YFFR | Project 9-ball footprint: TI YFF0009 drawing, 0.4 mm pitch, 0.225 mm lands, +0.025 mm mask margin; 1.498 × 1.361 mm maximum body |
| Eight LRAs | VLV041235L | Vybronics page 10: 0.8 × 1.8 mm contacts, 1 mm gap; proposed PCB lands 1 × 2.2 mm, no paste |
| USB-C | GCT USB4105-GF-A | Stock KiCad GCT USB4105 footprint; manufacturer drawing and contact numbering checked |
| Accessible wake/off button | Panasonic EVQPUJ02K | Stock EVQPUJ/EVQPUA footprint, side-facing actuator; final opening/extender needs sample fit |
| Internal boot/reset buttons | E-Switch TL3305AF160QG | Stock TL3305A footprint; internal access with lid removed |
| RGB indicator | Lite-On LTST-C19HE1WT | Stock footprint; manufacturer numbering 1=red, 2=green, 3=blue, 4=common anode matches schematic |
| Charger | BQ25186DLHR | Stock TI DLH0010A 10-pin WSON plus pad 11, checked against TI land drawing |
| Buck-boost | TPS63802DLAR | Project asymmetric DLA0010A land pattern, including long pad 8; not a generic DFN substitute |
| USB CC controller | TUSB320LAIRWBR | Stock TI X2QFN-12 1.6 × 1.6 mm footprint |
| Inductor | DFE201612E-R47M=P2 | 2 × 1.6 × 1.2 mm body, TI-recommended series; proposed lands still need Murata land-pattern confirmation |
| Cell fuse provisions | 0805 footprint | Fuse part/rating remains unselected |

Schematic properties hold the selected MPNs and footprints. C3 moved from 0402 to 0805 for its 10 uF allocation; electrical values are unchanged. Parts are not ordered and stock is not reserved. RGB brightness/colour balance at the existing low drive currents still needs a bench check.

Source drawings are cached in `hardware/datasheets/` where downloadable. Primary references: [TI DRV2625](https://www.ti.com/lit/ds/symlink/drv2625.pdf), [TI TPS63802](https://www.ti.com/lit/ds/symlink/tps63802.pdf), [GCT USB4105](https://gct.co/files/drawings/usb4105.pdf), [Vybronics VLV041235L](https://www.vybronics.com/wp-content/uploads/datasheet-files/Vybronics-VLV041235L-datasheet.pdf), and the [Lite-On manufacturer drawing mirrored by LCSC](https://datasheet.lcsc.com/datasheet/pdf/90ed7984e9524cb6ec545052e2af5714.pdf?productCode=C458749).

## Validation and next layout pass

ERC remains zero. Native schematic/PCB parity is zero; all physical pad nets are compared independently with the exported schematic netlist. The eight native outlines each contain one actuator opening. Placement DRC has **zero errors excluding the expected unrouted connections**, with five remaining silkscreen warnings and 499 unconnected items. No DRC/ERC exclusions were added. Copper-to-edge allowance is 0.25 mm; DRV2625 footprints use 0.15 mm local copper clearance to accommodate their 0.175 mm pad gap. These are prototype design targets, not a selected fabricator's approval.

The satellite driver decouplers and bulk capacitors have explicit positions; remaining small components were packed by courtyard and connected-neighbour proximity. Routing must still refine decoupling, MCU supply returns, the TPS63802 switching loop and USB paths. The BGA escape/via technology and stackup need a routing trial before committing to two layers. A clean placement check does not establish that the nine-ball package can be escaped with ordinary through vias in the available area.

The [fit-only shell coupons](../mechanical/fit-mockup/README.md) provide a physical size trial before further layout. Final PCB supports, lid retention, TPU links, clasp, wire strain relief and curved wrist surfaces remain to design after that trial. Preserve the factory battery PCMs and the lid-mounted cell arrangement. Physical lead bends, component heights, antenna performance and fit are unverified.

`tools/build_placement.py` regenerates and **replaces** the placement. Run it only intentionally; it is not an incremental editor for a hand-routed PCB. Original files are preserved in `hardware/backups/before-placement/`. `hardware/verification/placement/placement.json` records positions and the mechanical datum; `tools/check_placement.py` performs independent validation.
