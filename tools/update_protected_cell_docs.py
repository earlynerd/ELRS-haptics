"""One-time documentation reconciliation for protected-cell revision 0.5."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
backup=ROOT/'hardware/backups/before-protected-cells/docs'
assert not backup.exists()
backup.mkdir()
for p in (ROOT/'docs').glob('*.md'):shutil.copy2(p,backup/p.name)
shutil.copy2(ROOT/'README.md',backup/'root-README.md')
shutil.copy2(ROOT/'mechanical/pod-study/README.md',backup/'mechanical-README.md')
def read(p):return (ROOT/p).read_text(encoding='utf-8')
def write(p,s):(ROOT/p).write_text(s,encoding='utf-8')
def replace_paragraph(s,start,new):
    paragraphs=s.split('\n\n')
    hits=[i for i,p in enumerate(paragraphs) if p.startswith(start)]
    assert len(hits)==1,(start,hits)
    paragraphs[hits[0]]=new
    return '\n\n'.join(paragraphs)

p='docs/power-architecture.md';s=read(p)
s=replace_paragraph(s,'Status:', 'Status: eight protected 90 mAh batteries, one per pod, connected as **1S8P per wrist**. Native revision 0.5 removes the central protector and adds local bulk capacitance. The YDL301230 protected assembly establishes a 3 x 12 x 32 mm body envelope. Capacity is 720 mAh nominal; runtime and physical load qualification remain open.')
s=replace_paragraph(s,'Use one permanently', 'Use one permanently assembled group of eight identical protected pouch batteries per wrist. Keep the factory PCM intact on every battery. Connect PACK+ through its local positive-branch fuse to VBAT; connect PACK- to system GND. Raw cell terminals do not connect directly to the bracelet PCB. There is no central ABLIC protector, shunt or protection FET pair.')
a=s.index('```text');b=s.index('```',a+7)+3
s=s[:a]+'''```text
Battery 0 (factory PCM) PACK+ -- fuse --+
Battery 1 (factory PCM) PACK+ -- fuse --+-- VBAT <--> BQ25186 BAT
...                                    |
Battery 7 (factory PCM) PACK+ -- fuse --+
All protected PACK- leads ---------------- GND

USB-C --> power-path charger SYS --> buck-boost --> 3V3 (ESP32/control)
                                                   +-- TPS22918 --> POD_3V3
                                                       eight MCU/driver pods
                                                       +22 uF bulk per pod
```'''+s[b:]
s=replace_paragraph(s,'VBAT_RAW is', 'VBAT is conductor 5, the combined protected battery-output bus. It connects directly to U11 BAT, C36 and J3 pin 1. It remains live when POD_3V3 is off or the charger is in ship mode. J200-J207 each represent the protected two-wire output of the battery installed in that pod; F100-F107 remain local fuse provisions. See [protection implementation](pack-protection-implementation.md).')
s=replace_paragraph(s,'This is a functional', 'Each factory PCM monitors its own cell and can disconnect independently. The remaining branches then share the load and charging current. Individual PCMs are not equivalent to the removed aggregate current cutoff; final fuse ratings and charge/load policy must account for branch loss, unequal sharing and actual PCM recovery behavior. PCB connectivity checks cannot verify those external protection functions.')
s=s.replace('Cells in the permanently connected group share voltage, so series-cell balancing is not required.', 'While their PCMs conduct, cells in the permanently connected group share approximately the same voltage, so series-cell balancing is not required.')
s=replace_paragraph(s,'Assume conventional', 'Plan for 4.20 V-charge, nominal 3.7 V batteries matching the YDL example. Its ratings give 45 mA maximum continuous discharge per cell, **360 mA total with eight equally sharing branches**, or 1.332 W at nominal voltage. Standard charge is 18 mA per cell (144 mA aggregate), maximum 45 mA (360 mA aggregate). These aggregate values are not safe defaults when branches have disconnected; final charger settings and recovery policy remain firmware work.')
s=replace_paragraph(s,'The charger/regulator and supporting', 'The charger/regulator and supporting circuit are in the native schematic. The former protection child sheet is archived under `hardware/backups/before-protected-cells/`; the active hierarchy has 13 sheets. J3 exposes VBAT, GND and the charger thermistor. Battery/fuse interfaces are present on all eight pod sheets; actual pad footprints and fuse ratings remain open.')
s=replace_paragraph(s,'For illustration only,', 'Eight 90 mAh, 3.7 V cells contain 2.664 Wh nominally. With an illustrative 85% usable-energy/conversion factor, this gives about 2.26 hours at 1 W or 4.53 hours at 0.5 W. These are energy scenarios, not runtime predictions; continuous-current limits also apply. Cutoff, aging, rate and temperature affect usable energy.')
s=s.replace('Cell count and charge current should follow those measurements and the selected cells\' ratings.', 'Charge settings and allowed haptic load should follow those measurements and the battery ratings; the planned count is eight.')
write(p,s)

p='docs/ring-pods.md';s=read(p).replace('VBAT_RAW','VBAT').replace('unswitched parallel-cell positive bus','unswitched protected battery-output bus')
s=replace_paragraph(s,'Each pod has an optional cell connection', 'Each pod has one protected battery at J200-J207 and a positive-branch fuse F100-F107. Connect factory PACK+ through the fuse to VBAT and factory PACK- to GND. Retain each PCM and leave raw cell terminals isolated from the board. This battery bus stays live when pod power is off. The working battery envelope is 3 x 12 x 32 mm, with 90 mAh per pod.')
s=replace_paragraph(s,'The `protection.kicad_sch`', 'The central protection stage is removed. VBAT directly feeds BQ25186 BAT and J3; protection is inside each battery assembly. Per-cell fuses remain, with ratings pending. The six-wire harness and UART return topology are unchanged. See [battery protection](pack-protection-implementation.md).')
s=s.replace('Temperature firmware and distributed pack protection remain open.', 'Temperature firmware and physical PCM cutoff/recovery validation remain open.')
s=s.replace('C42 sets a controlled ramp,', 'C42 is now 4.7 nF and sets a controlled ramp,')
s += '''
## Added pod bulk and ramp budget

C103/C113/C123/C133/C143/C153/C163/C173 add 22 uF, 10 V X5R in 0805 from POD_3V3 to GND, near each driver supply/power entry. Keep the existing 10 uF, 1 uF and 100 nF local capacitors. Final MPN selection must check effective capacitance at 3.3 V; the 22 uF value is nominal, not guaranteed under DC bias.

The exported netlist totals 266.6 uF nominal on POD_3V3. With C42=4.7 nF, TPS22918 Equation 3 gives about 8.65 ms typical 10-90% rise at 3.308 V and 81.6 mA capacitor-only ramp current. This excludes dynamic load, tolerance and DC-bias effects. Hold reset through supply settling. The added capacitance also lengthens output discharge through R46 and U26 QOD: firmware must not reuse an unverified old shutdown delay. Actual startup, discharge and rail excursions remain bench checks. Calculations are in `hardware/verification/pack-protection-checks.json`.
'''
write(p,s)

p='docs/standby-and-controls.md';s=read(p)
s=s.replace('| S-821AAAC protector U27 | 6 uA at battery | 3.4 V normal-state test; 10 uA max at 25 C, 14 uA max over -40 to +85 C |','| Eight factory battery PCMs | Approximately 8 uA total typical, 56 uA maximum from the example PCM table | YDL table lists 1 uA typical / 7 uA maximum per PCM; exact supplied PCM and conditions require confirmation |')
s=s.replace('`6 + 4 + 11 + (7 + 70 + 0.5 + 5.50) * 3.308 / (3.7 * 0.85) = 108 uA`','`8 + 4 + 11 + (7 + 70 + 0.5 + 5.50) * 3.308 / (3.7 * 0.85) = approximately 110 uA`').replace('This includes the selected protector','This includes eight illustrative 1 uA battery PCMs')
s=replace_paragraph(s,'With USB absent, **BQ25186 ship', 'With USB absent, **BQ25186 ship current is 3.2 uA typical, 5 uA maximum under its specified conditions**, with downstream SYS disconnected. Eight factory PCMs at the YDL example\'s 1 uA typical each give approximately **11.2 uA plus residual leakage** for the complete bracelet. All eight PCMs remain attached to their cells in ship mode; confirm the actual shipped PCM specification. The central U27 no longer exists. Charger shutdown is 15 nA typical but loses button wake. Neither figure describes charging; charger input IQ at 5 V, 4.5 V SYS and zero charge current is 0.75 mA typical.')
write(p,s)

p='docs/usb-power-implementation.md';s=read(p).replace('BAT_PROTECTED','VBAT')
s=s.replace('J3 is the **protected 1S-NP pack interface**, not an unprotected pouch connection:', 'J3 is the **shared protected-battery bus and charger NTC interface**:')
s=replace_paragraph(s,'Pack protection, branch fuses', 'Battery protection now comes from the intact factory PCM on each of eight batteries. J200-J207 connect only their protected outputs; the central protector has been removed. Per-cell fuse ratings and monitoring of all distributed battery temperatures remain to be completed. There is no dummy onboard NTC permitting charging with missing sensing. The firmware must leave CHG_ALLOW low until charging settings and the complete temperature policy are implemented.')
write(p,s)

write('docs/pack-protection-implementation.md','''# Eight batteries with built-in protection

Native revision 0.5 follows the user's choice to use eight protected 90 mAh pouch batteries, one per pod, with their factory PCMs intact. The YDL301230 protected assembly is the working example: 3 x 12 x 32 mm excluding leads/connector. This supersedes the central S-821AAAC circuit.

## Implemented connectivity

- J200-J207 pin 1: protected PACK+ through F100-F107 to shared VBAT.
- J200-J207 pin 2: protected PACK- to system GND. Never connect raw cell negative to GND around a low-side PCM.
- VBAT directly reaches BQ25186 U11 BAT pin 2, C36 and J3 pin 1. It is conductor 5 of the existing six-wire harness.
- U27, Q6, Q7, R54-R56 and C44 are removed. The old child sheet and checks are archived in `hardware/backups/before-protected-cells/`. Unused library assets and source datasheets are historical, not populated parts.
- BQ25186 charging/ship mode, TPS63802 regulation, TPS22918 pod power control, button and RGB remain.

The factory PCMs are external to the PCB schematic, represented at the battery interface. No raw-cell bypass connection is provided. All eight branches are planned populated; fuse part/rating and solder-pad footprints remain open. The battery itself is an off-board assembly, not the MPN of the J200-J207 PCB interface.

## Capacity, current and recovery

Eight 90 mAh batteries give 720 mAh / 2.664 Wh nominal. The YDL example permits 45 mA continuous discharge per cell, giving 360 mA aggregate with equal sharing. Its 18 mA standard and 45 mA maximum charging currents correspond to 144/360 mA with eight equal branches. Charger settings remain unimplemented; these are not defaults for an unknown active branch count.

Each PCM can disconnect and reconnect independently. Remaining branches carry the load/charge current. Individual PCM overcurrent protection does not reproduce the former shared 1.93 A cutoff. Retain local fuse provisions; finalize their ratings against the wiring, battery PCM and actual loads. Check depleted-cell charging, independent cutoff, reconnection and sharing with physical samples. The YDL PDF and listing contain conflicting PCM current figures, so those thresholds are not treated as a verified system cutoff.

## Additional bulk capacitance

Each pod adds a 22 uF 10 V X5R 0805 capacitor on POD_3V3 (C103 through C173 in increments of 10), alongside its existing local capacitors. The total switched-rail capacitance is 266.6 uF nominal. C42 changes from 1 nF to 4.7 nF for approximately 8.65 ms typical 10-90% rise and 81.6 mA capacitor-only startup current, using TPS22918 Equation 3. Effective capacitance/DC bias, startup load and discharge timing need physical checks; capacitor MPNs remain open.

## Evidence

`tools/check_connectivity.py`, `tools/check_usb_power.py` and `tools/check_protected_cells.py` pass against the fresh 269-component XML netlist. `tools/check_pack_protection.py` remains a compatibility entry point to the new checks. ERC: zero errors and zero warnings across 13 active sheets. Reports are in `hardware/verification/`; current previews are in `hardware/preview/protected-cells/`.

Sources: [YDL datasheet](https://ydlbattery.com/cdn/shop/files/YDL-301230-90mAh-specification.pdf?v=17344537468879431347), cached as `hardware/datasheets/YDL301230.pdf`; [TI TPS22918](https://www.ti.com/lit/ds/symlink/tps22918.pdf), section 8.3.2. Verification covers the PCB interfaces and nominal calculations, not external PCM functionality, firmware, PCB layout or physical qualification.
''')
p='docs/protection-sourcing.md';s=read(p);write(p,'> **Superseded in revision 0.5:** the user chose protected batteries with intact factory PCMs. No central ABLIC stage is populated. This document retains the earlier sourcing history; see [current implementation](pack-protection-implementation.md).\n\n'+s)
p='docs/cell-candidate-301230.md';s=read(p)
s='''> **Adopted packaging baseline, revision 0.5:** eight protected 90 mAh batteries, one per pod, using the YDL301230 3 x 12 x 32 mm assembly as the example. Keep factory PCMs intact; remove the central protector. Study D allocates a battery in every lid. The earlier study-C fit and alternative sourcing discussion below are historical comparisons, not the current count/protection decision.

'''+s
s=s.replace('Candidates remain unselected;', 'The exact purchase remains open, but protected assemblies of this size are the adopted baseline;')
s=s.replace("The current prototype protector's 1.93 A nominal discharge trip", "The retired central prototype protector's 1.93 A nominal discharge trip")
write(p,s)

p='README.md';s=read(p)
s=s.replace('one 1S pack with an open number of parallel pouch cells distributed around the bracelet.', 'one 1S8P battery group: eight protected 90 mAh pouch batteries, one per pod (720 mAh nominal).')
s=s.replace('The 14 sheets','The 13 sheets').replace('the charger/regulator, high-side pack protection, USB-C','the charger/regulator, USB-C')
s=s.replace('VBAT_RAW','VBAT').replace('Optional cell connections retain local positive-branch fuses and feed the central S-821AAAC high-side pack protector.', 'Each battery retains its factory PCM and feeds VBAT through a local positive-branch fuse provision. No central protector remains.')
s=s.replace('Every pod has removable UART links', 'Every pod adds 22 uF bulk on its switched rail and has removable UART links')
s=s.replace('all 14 sheets','all 13 sheets').replace('268-component','269-component').replace('new pack-protection connectivity checks','protected-battery/bulk-capacitance checks').replace('hardware/preview/pack-protection/','hardware/preview/protected-cells/')
s=s.replace('The prototype protector circuit and its footprint are implemented; see [pack protection](docs/pack-protection-implementation.md) for selected parts, trip values and validation scope.', 'Factory PCMs provide battery protection; see [battery interfaces](docs/pack-protection-implementation.md) for the wiring and validation scope.')
s=s.replace('Battery count, capacity and runtime target remain open.', 'Eight 90 mAh batteries are the working baseline; exact purchase, fuse ratings and runtime qualification remain open.')
s=replace_paragraph(s,'The [dimensional pod study]', 'The [dimensional pod study](mechanical/pod-study/README.md) uses the measured 195 mm wrist. Revision D proposes 20 x 38 x 10.5 mm regular shells and a 24 x 64 x 10.5 mm main shell, with one protected 3 x 12 x 32 mm battery bonded inside every lid. The main battery is allocated away from the antenna and USB/button/RGB end. Width around the wrist stays unchanged. These are packaging envelopes, not finished PCB outlines or proven fit.')
s=replace_paragraph(s,'The proposed [301230', 'The [YDL301230-class battery baseline](docs/cell-candidate-301230.md) provides 720 mAh and 360 mA continuous aggregate current with equal sharing. Factory PCMs stay intact. New 22 uF pod capacitors and C42=4.7 nF ramp control are documented in [ring power](docs/ring-pods.md).')
write(p,s)

p='mechanical/pod-study/README.md';s=read(p)
s=s.replace('study C','study D').replace('| 20 | 34 | 10 |','| 20 | 38 | 10.5 |').replace('| 24 | 52 | 10 |','| 24 | 64 | 10.5 |').replace('| 17 | 31 | 0.8 |','| 17 | 35 | 0.8 |').replace('| 21 | 49 | 0.8 |','| 21 | 61 | 0.8 |').replace('| Regular optional cell envelope, excluding lid adhesive | 16 | 28 | 3.0 |','| Battery body, each of eight pods | 12 | 32 | 3.0 |\n| Lid battery allocation, excluding adhesive | 14 | 34 | 3.5 |')
s=s.replace('The optional cell envelope occupies z=5.8..8.8','The battery allocation occupies z=5.8..9.3').replace('z=8.8..9','z=9.3..9.5').replace('ends at z=10.', 'ends at z=10.5.').replace('The 10 mm thickness', 'The 10.5 mm thickness')
s=replace_paragraph(s,"Per the user's correction,", "Bond one protected 3 x 12 x 32 mm battery inside every lid; keep its factory PCM. The 14 x 34 x 3.5 mm allocation gives 1 mm around the body in plan and 0.5 mm additional radial allowance, plus 0.2 mm lid adhesive. These are provisional clearances, not supplier-qualified expansion or wire-bend allowances. Plan soldered protected-output leads, with the external connector removed; no pocket is allocated for the stock PH2.0 plug. Leave lead slack to open the lid, and keep PCM/tabs insulated and strain relieved. There is no separate compartment or shelf.")
s=s.replace('Revision C adds', 'Revision D retains').replace('not all 254 schematic components placed','not all 269 schematic components placed')
s += '''
## Revision D battery placement

Each regular shell grows 4 mm along the arm. The main shell grows 12 mm along the arm so its lid can carry the eighth battery between the antenna end and USB end. Circumferential widths stay 20/24 mm; radial height grows 0.5 mm for additional battery allowance.

Coordinates below use the shell's left/antenna-side end as x/y=0 in the plan drawing. Regular battery allocation: x=3..17, y=2..36; main allocation: x=5..19, y=22..56. The body fits centered inside each allocation. The main USB block starts at y=57; the antenna body ends at approximately y=6.6, leaving over 15 mm to the battery allocation. This is a conservative packaging separation, not an RF qualification. Module height outside the battery region is not constrained by the regular-pod 4.8 mm component ceiling. The eight LRAs/link anchors retain a common axial centerline when the pods are worn.

Dashed overlays in the plan show the lid-mounted batteries above the board, not PCB cutouts. The capacitor 0805 footprint fits the component height allocation in principle; full board placement, capacitor MPN, lid closure, lead exit and wrist curvature remain unresolved. `dimensions.json` records these allocations and eight-cell intent; no fabrication PCB outlines have been generated.
'''
write(p,s)

with (ROOT/'DECISIONS.md').open('a',encoding='utf-8') as f:f.write('''
## 2026-09-12 - Eight protected batteries and distributed bulk capacitance

- **Decision:** Use eight protected 90 mAh batteries, one per pod, with a 3 x 12 x 32 mm YDL301230-class body. Keep factory PCMs intact; remove U27/Q6/Q7/R54-R56/C44 and connect the fused protected outputs directly to VBAT/U11 BAT. Add 22 uF 10 V X5R 0805 per pod; increase TPS22918 C42 to 4.7 nF.
- **Why:** User chooses off-the-shelf battery protection and additional local energy storage. Slower startup accommodates the added capacitance. Retain branch fuses and six-wire interconnect.
- **Supersedes:** Central S-821AAAC selection/implementation and open battery count. Study D supersedes study C allocations with 20 x 38 x 10.5 regular and 24 x 64 x 10.5 main shells, batteries bonded inside every lid.
- **Affects:** Schematics, checks, power/standby documentation and packaging study. Exact fuse/capacitor parts, PCM behavior, current sharing, firmware and physical fit remain unqualified.
''')
print('Updated current documentation and appended decision; previous docs backed up.')
