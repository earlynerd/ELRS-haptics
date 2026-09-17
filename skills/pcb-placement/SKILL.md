---
name: pcb-placement
description: Evaluate and improve KiCad PCB component placement using airwire metrics, critical electrical paths, mechanical constraints, and before/after checks. Use for placement reviews, comparing layouts, rearranging components, and layout-oriented footprint replacement. Does not replace a complete electrical or fabrication review.
---

# PCB placement

Help the user produce a compact, routable placement while preserving their circuit, mechanical requirements and existing work. A request to evaluate placement authorizes measurement and recommendations, not automatic rearrangement.

## Establish the actual starting point

- Identify the active PCB/schematic masters and current project rules. Read recent relevant decisions; dated reports, old generators and accepted-position files may describe superseded layouts.
- Inspect the user's saved changes before editing. Measure saved files and say so; do not present them as unsaved editor state. If an editor has unsaved changes that would be lost, resolve that conflict before replacing its files. An old lock file alone is not evidence of unsaved work.
- Record the board hash and existing DRC/parity findings. Keep backups before mutations. Do not reset user changes or regenerate the board from an old placement script.
- Identify fixed or mechanically constrained anchors: outline, mounting holes, antenna region, connectors, button access, LEDs, cable exits, recovery pads, batteries and actuator contact areas. Do not move these merely to lower a wire-length score.

For this bracelet project, read [references/haptic-bracelet.md](references/haptic-bracelet.md); recheck its dated constraints against the live files. Do not load it for unrelated boards.

## Evaluate placement

Use [scripts/evaluate_placement.py](scripts/evaluate_placement.py) with KiCad's Python. See [references/metrics.md](references/metrics.md) for commands, comparison semantics and limitations. The helper reads the board, invokes native DRC, and emits Markdown/JSON; it does not save or refill the PCB.

Report at least total/mean length and the longest connections, plus current physical conflicts. For a fixed topology, mean and total convey the same optimization direction; total is often easier to compare. Use per-net and component results to choose what to inspect, not to issue automatic move commands.

Distinguish:

- **Placement tree:** Euclidean minimum spanning tree over copper pad centres, independent of existing routing. Useful for repeated placement comparisons.
- **Remaining-span estimate:** KiCad DRC unconnected item pairs, with nearest pad-centre/track-end/via anchors. This approximates the displayed ratsnest; it is not a direct extraction of its graphic lines or actual route length.
- **Electrical quality:** Decoupling, switch-current loops, feedback coupling, return continuity, differential-pair topology and RF clearance. A short tree does not validate these.

Keep all-net results available. Ground nets can add many short edges and depress the mean; offer explicit net exclusions without silently dropping power nets. Compare like-for-like topology and filters. Routing the short connections first can raise the remaining average even as the board improves.

## Choose and apply useful improvements

Read [references/layout-lessons.md](references/layout-lessons.md) for the relevant electrical, mechanical or footprint guidance.

**Use functional grouping as the starting process.** Identify which IC or circuit function each passive serves from the schematic. Arrange those parts into tight, electrically sensible subgroups before arranging the groups across the board. Work out the local pin-to-pad connections and power/return paths inside each subgroup, then position and orient the groups around fixed anchors and their interconnections. Do not scatter passives to minimize a global wire-length score.

**Treat immediate vias at both ends of a passive as a placement smell.** Usually try to place or rotate it so at least one pad connects directly to its associated component or nearby destination on the same layer. This can reduce vias and untangle neighboring traces. Inspect actual routed exits; being on the same layer or close in XY does not prove a useful direct connection. This is a preference, not a ban: a short capacitor ground via to the reference plane can be appropriate, and actual electrical/mechanical constraints can justify both ends changing layer. Explain such exceptions instead of adding long detours merely to avoid vias.

**Preferred four-layer usage:** F.Cu and B.Cu carry signals and local routing; In1.Cu is a continuous ground plane; In2.Cu distributes power through appropriately separated rail regions. Preserve ground continuity and keep general signal routing off the inner planes. Confirm the project's actual stackup and rail topology before applying the preference; do not silently change an established stackup. In particular, assess reference continuity for bottom-side signals where the adjacent power plane is split.

Prioritize actual shorts, clearances and packing conflicts; then critical local paths; then general routing convenience. A longer LED wire may be acceptable to keep the LED visible, while a shorter but poorly arranged regulator loop may be unacceptable. Explain that tradeoff when it matters.

When edits are requested, work in bounded functional groups. Preserve unrelated footprints, pads/nets, tracks, vias, zones, outlines, project settings and schematic redraws. Preserve component identity and schematic paths during footprint replacement. Do not silently swap pins, nets, footprints or layers to improve a metric. Treat fixed anchors and user constraints as hard constraints unless the user changes them.

## Verify and deliver

- Repeat the same metric/filter configuration and inspect native DRC and schematic parity as relevant. If copper was edited, check with zones refilled on a candidate or authorized source; distinguish that from a read-only measurement of saved fill.
- Compare violations by type and affected items, not only total count. A new error hidden by a removed warning is not a clean result. Check that unedited objects remain unchanged.
- For footprint changes, verify the exact variant's land pattern and pin-to-net mapping, update schematic/library/placed footprint consistently, and inspect attached 3D body alignment. State when the model is approximate.
- Keep reference reports with source hashes. Refresh an accepted baseline deliberately only after the underlying change is accepted; do not weaken preservation checks to silence failures.
- Report the concrete improvement, tests/checks, and remaining layout or physical work. DRC, ERC, STEP and fit-coupon success are different evidence; none alone proves assembled fit, electrical performance or fabrication readiness.

Scale checks to scope. A placement measurement does not automatically require a full schematic/EMC/fabrication audit. For such an audit when requested, use an available dedicated KiCad review workflow and its complete evidence requirements.
