# Bracelet context — verified from project files on 2026-09-17

This is a dated navigation aid, not a frozen design specification. Read current files before applying any value below. The early I2C-mux architecture, combined board, actuator cutouts, 17 × 35 mm contours, old component counts and side-switch arrangement were superseded. Earlier reports can contain internally valid evidence for those older designs.

## Current owners

- Active masters: `hardware/main/main.kicad_pcb` and `hardware/satellite/satellite.kicad_pcb`, with their corresponding schematic projects.
- Design choices: latest applicable entries in `DECISIONS.md`.
- Physical assembly: `docs/pcb-sandwich.md`, `hardware/mounting-layout.json`, `hardware/stacked-architecture.json`.
- Routing-rule history: `docs/pcb-routing.md`, especially its 2026-09-13 shared-rules section. Its older placement/count prose is explicitly historical.
- Functional grouping rationale: `docs/main-board-placement.md`; its coordinates and acceptance counts are historical, not the user's latest placement.
- Measurement implementation/provenance: project `tools/evaluate_placement.py`, `tools/test_evaluate_placement.py`, `hardware/verification/placement-score/`.
- Preservation checks: `tools/verify_split_projects.ps1` and its called checkers. Some compare against older accepted baselines and will correctly flag later intentional edits; inspect rather than bypass them.

## Accepted project constraints to recheck

- The later stacked arrangement uses one controller and eight universal pod boards, with seven cell-bearing pods and no cell in pod 0. Do not revive the earlier one-main/seven-satellite integrated-main architecture from an old report.
- Both active board contours are 20 × 46 mm, R2.5. Nominal active stackups remain four-layer, 0.8 mm; thinner plates are an experiment, not an applied default.
- Shared hole/standoff centres relative to the upper-left are (2.75,2.75), (17.25,2.75), (2.75,43.25), (17.25,43.25) mm. Upper screw clearance is 1.8 mm. Lower SMT standoffs have no hole through the skin plate. Final standoff height and screw choice remain open.
- The proposed TPU contact strip is 1.2 mm wide, with a 1.5 mm component inset and 4.6 mm corner reliefs. These drawings are not automatic DRC keepouts. Final compression, harness/USB relief and fit need physical work.
- The recorded routing policy is 0.1524 mm minimum track/clearance, at least 0.25 mm via drill, 0.20 mm copper-edge clearance, with direct/solid plane connections. Defaults and accepted layer use must be read from the live project. Do not generalize these numbers or the solid-connection policy to other boards.
- Avoid component solder-pad via holes under the accepted ordinary-via process; distinguish intentional hand-soldered wire pads from component lands. Do not silently introduce microvias or filled/capped via-in-pad fabrication.
- SW3 became EVPAWBD4A, 1.6 N, nominal 0.6 mm high, on outward B.Cu in this checkpoint. Preserve TS/MR and GND mapping. Its STEP is a labeled nominal approximation, not vendor CAD. Its protective cover is still a proposal.

## Lessons retained from previous project work

The user explicitly reaffirmed the placement process on 2026-09-17: group supporting passives with their functional IC/circuit, build tight local subgroups, then arrange the groups. Passives that immediately drop to vias on both pads are a cue to revisit their placement; prefer at least one direct same-layer termination where practical. This is a judgment-based review, not currently automated by the airwire evaluator.

The explicitly preferred four-layer usage is outer-layer routing, an unbroken ground plane, and a power plane sectioned for distribution of multiple rails. Read `layout-lessons.md` for return-path caveats and legitimate exceptions; do not turn this preference into a blanket approval of every power-plane split.

The user values editable native files, preserved manual placement and schematic redraws, and explicit physical evidence. Their assembly capability includes fine-pitch work; do not reopen package choices merely due to generic soldering concerns. Mechanical access and serviceability should remain deliberate.

Old model/render/DRC successes are not current fabrication approval. Query fresh findings instead of copying counts into a new report. Both the early seed and later placement checkpoints documented unfinished work; a clean subsection is not proof that the entire assembly is complete.
