# Hardware scripts

The active designs are native KiCad projects under `hardware/main/` and `hardware/satellite/`.

## Placement measurements

Save the PCB, then run from the project root:

```powershell
./tools/evaluate_placement.ps1
./tools/evaluate_placement.ps1 -ExcludeNet '^GND$'
./tools/evaluate_placement.ps1 -Compare 'hardware/verification/placement-score/PREVIOUS/placement.json'
```

Each invocation creates a timestamped report directory and leaves the PCB untouched. `placement.md` is the readable report; `placement.json` contains every measured connection, per-net and incident-component totals, source hash and KiCad version. `drc.json` and `drc.log` retain the native checks. `-Board` selects another PCB; `-Out` selects an explicit output directory. Comparison requires matching pad/net topology and filters. Unsaved editor placement is not visible to this tool.

Two distinct measures are reported: fresh KiCad DRC unconnected endpoint spans (remaining airwires), and a Euclidean minimum spanning tree over each net's copper pad centres (routing-independent placement proxy). Reported statistics are count, total, mean, median, nearest-rank P95 and maximum, in mm. Every copper pad is included, including same-footprint/duplicate-number pads; coincident pads contribute zero-length edges. The latter can change the mean relative to KiCad's ratsnest even when totals agree. No nets are excluded by default. Ground-only filtering is useful but does not imply all other nets are signals.

The remaining-airwire measurement is an estimate reconstructed from native unconnected item pairs and nearest pad-centre/track-end/via anchors, rather than direct access to the editor's displayed ratsnest. DRC track positions identify a track's start, so the tool resolves the nearer endpoint. Unsupported endpoints such as zone objects cause an explicit error rather than an invented distance. This is tested on unrouted, partially routed and fully routed fixtures.

Use total length to compare placements of the same circuit. Existing routing, planes, layer transitions, obstacles, trace width and electrical priority are not modeled by the placement tree. Native DRC uses saved zone fills without modifying/refilling them. Short circuits can also affect native connectivity, so inspect DRC alongside the metrics. A lower score is not a fabrication or placement acceptance gate. Critical power loops, decoupling, RF/USB, enclosure constraints and courtyard clearance remain separate checks.

Tests (KiCad Python):

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' tools/test_evaluate_placement.py
```

Run `verify_split_projects.ps1` to export current netlists, run ERC/DRC and verify preservation of the accepted circuit/placement. It does not regenerate schematics or PCBs. The comparison baseline must be deliberately updated when future circuit or placement changes are accepted.

`redraw_projects.py`, `readable_schematic.py`, `split_pcb_projects.py`, `route_satellite_selector.py` and `render_split_projects.cjs` record the two-project migration. Mutation entry points require explicit migration flags and are not incremental editors. In particular, repeating the selector router would duplicate tracks.

Earlier scripts target the archived eight-island architecture. Their reports remain in historical verification directories; they are not the active validation or generation workflow. Do not run an old generator against the new project structure.
