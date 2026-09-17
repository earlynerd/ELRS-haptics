# Running and interpreting the evaluator

Use a Python interpreter that can import `pcbnew`. On the verified Windows machine this is `C:/Program Files/KiCad/10.0/bin/python.exe`. The Python entry point accepts `--kicad-cli PATH` for other installations. No third-party Python packages are required beyond KiCad's bindings.

```powershell
& '<skill>/scripts/evaluate_placement.ps1' -Board './hardware/main/main.kicad_pcb'
& '<skill>/scripts/evaluate_placement.ps1' -Board './hardware/main/main.kicad_pcb' -ExcludeNet '^GND$'
& '<skill>/scripts/evaluate_placement.ps1' -Board './hardware/main/main.kicad_pcb' -Compare './previous/placement.json'
```

The packaged wrapper requires an explicit board and writes timestamped reports under the caller's `placement-reports/`, never into the skill installation. `-Out`, `-KiCadBin`, and repeatable regex filters are available. The board must be saved; there is no live editor connection.

Direct invocation:

```text
<KiCad Python> <skill>/scripts/evaluate_placement.py BOARD --out REPORT_DIR --kicad-cli CLI
```

Outputs: `placement.md`, `placement.json`, `drc.json`, `drc.log`, and writable KiCad runtime directories when not already configured. Reports contain the source board hash and KiCad version. The script checks that the PCB bytes did not change during measurement. It does not snapshot the whole project atomically; avoid concurrent edits during a comparison.

## Meaning of the metrics

- The placement proxy uses a deterministic Euclidean minimum spanning tree per net over all netted copper pad centres. It ignores existing routing, layer transitions, obstacles, pad edges, widths and plane intent. It is a geometric proxy, not a proof of minimum route length or routability.
- Every pad instance is a node, including same-footprint pads and duplicate pad numbers. Coincident nodes have zero-length edges. JSON flags same-footprint tree edges. KiCad's ratsnest count can differ while the total length agrees.
- Remaining connections use native DRC-selected item pairs and nearest supported anchors. Supported anchors are pad centres, track/arc endpoints and via positions. No shortest-distance-to-copper or intermediate arc calculation is performed. Unsupported objects cause an explicit error; do not replace an error with an apparently valid zero score.
- Reported statistics are count, total, mean, median, nearest-rank P95 and maximum. Empty results have count/total zero and null mean/percentile/max, not an invented average of zero.
- All nets are included by default. Filters are regex searches against full net names, so anchor them when exact exclusion is intended. A report excluding GND is not automatically a signal-only report.
- Baseline comparison requires matching pad IDs/net assignments and identical filter lists. Replacement of pads, even with an equivalent circuit, invalidates automatic comparison. Rebaseline deliberately and explain why. Do not compare different tool metric definitions as though they were identical.
- Incident component totals are diagnostic and double-count edges shared across components. An MST edge is not a mandate to route that specific point-to-point connection.
- DRC uses saved zone fills, without refill. Shorts can distort connectivity. Inspect the native findings alongside the score; do not optimize a shorted or mechanically invalid placement by metric alone.

## Validation

Run with KiCad Python:

```text
<KiCad Python> <skill>/scripts/test_evaluate_placement.py
```

Tests cover a known-distance MST, order/translation invariance, coincident and empty sets, comparison rejection, and native unrouted/partial/full-routing fixtures. The integration fixture confirms the remaining distance changes while placement-tree length stays fixed. Tests use temporary boards; they do not change the user's PCB.
