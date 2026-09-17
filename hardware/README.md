# Hardware sources

Open `main/main.kicad_pro` and `satellite/satellite.kicad_pro` in KiCad 10.

- `main/`: one controller daughterboard PCBA; its haptic pod is a separate universal board.
- `satellite/`: one universal PCBA, built eight times per wrist. JP1 selects normal or end-of-chain operation.
- `HapticBracelet.kicad_sym`, `HapticBracelet.pretty/`: shared libraries referenced by both projects.
- `panel/`: future derived manufacturing panel, never the source for board edits.
- `verification/project-split/`: current schematic PDFs, previews and check reports.
- `archive/combined-project/`: superseded eight-island project, preserved intact.
- `backups/`: historical snapshots, including the saved user redraw before migration.

Both boards now use the regular pod's full 20 × 46 mm, R2.5 outside contour. Four M1.6 standoff lands on the universal lower board match four 1.8 mm clearance holes on the controller plate. Neither board has an actuator opening. Cmts.User marks the 1.2 mm TPU contact band; Dwgs.User marks a 1.5 mm placement inset. Existing electrical positions and routes are preserved. See [PCB sandwich construction](../docs/pcb-sandwich.md) for mounting height and placement status. Schematics and boards are edited natively; construction scripts are migration provenance.

Current topology and checks: [stacked controller architecture](../docs/pcba-projects.md). Pod 0 has no cell or external NTC; pods 1-7 have both.
