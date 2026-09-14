# Hardware scripts

The active designs are native KiCad projects under `hardware/main/` and `hardware/satellite/`.

Run `verify_split_projects.ps1` to export current netlists, run ERC/DRC and verify preservation of the accepted circuit/placement. It does not regenerate schematics or PCBs. The comparison baseline must be deliberately updated when future circuit or placement changes are accepted.

`redraw_projects.py`, `readable_schematic.py`, `split_pcb_projects.py`, `route_satellite_selector.py` and `render_split_projects.cjs` record the two-project migration. Mutation entry points require explicit migration flags and are not incremental editors. In particular, repeating the selector router would duplicate tracks.

Earlier scripts target the archived eight-island architecture. Their reports remain in historical verification directories; they are not the active validation or generation workflow. Do not run an old generator against the new project structure.
