# Hardware sources

Open `main/main.kicad_pro` and `satellite/satellite.kicad_pro` in KiCad 10.

- `main/`: one main PCBA, including its local haptic circuit.
- `satellite/`: one universal PCBA, built seven times per wrist. JP1 selects normal or end-of-chain operation.
- `HapticBracelet.kicad_sym`, `HapticBracelet.pretty/`: shared libraries referenced by both projects.
- `panel/`: future derived manufacturing panel, never the source for board edits.
- `verification/project-split/`: current schematic PDFs, previews and check reports.
- `archive/combined-project/`: superseded eight-island project, preserved intact.
- `backups/`: historical snapshots, including the saved user redraw before migration.

The two PCB files each contain one board outline and one actuator opening. Schematics and boards are edited natively; construction scripts are migration provenance.
