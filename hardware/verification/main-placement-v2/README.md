# Applied main placement, 2026-09-13

See ../../../docs/main-board-placement.md for constraints and distances. main.kicad_pcb is the applied 70-part checkpoint; placement.png/svg show native pads and courtyard bounds. The active sources are ../../main/. Current acceptance reports are ../project-split/.

input.kicad_pcb is the user placement with the new Tag-Connect footprint synchronized before optimization. previous.xml and active-latest* capture intermediate redraw checks; they are historical. metrics.json is an earlier candidate measurement and is superseded by critical-distances.json and the final native reports. apply-input-hashes.json documents a guarded apply attempt that correctly refused an intervening user save.

Latest original files are backed up under ../../backups/pre-main-placement-v2-latest-20260913/. Final placement has fixed user edge anchors, one existing NRST/VDD segment, no vias and 196 opens. This is placement evidence, not routing or fabrication qualification. One M2003 reset-input ERC item and three ESP32 silk/library DRC warnings remain.
