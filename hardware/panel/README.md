# Future manufacturing panel

Panelization is deferred until both individual PCB designs are complete.

The intended starting quantity is one controller daughterboard plus eight identical universal pods per wrist. Both designs are four-layer, nominally 0.8 mm. All satellites use the same Gerbers and assembly configuration; the final satellite's JP1 is changed by cutting 1–2 and soldering 2–3.

Create a future panel here as a derived output from `../main/main.kicad_pcb` and `../satellite/satellite.kicad_pcb`, recording source hashes and the selected JLCPCB stack and panel rules. Keep BOM/reference namespaces unambiguous between PCBAs. Rails, tabs, breakaways, fiducials, tooling and assembly outputs will be chosen at that stage.

Do not edit individual circuits in the panel. No panel PCB or fabrication exports have been created here.
