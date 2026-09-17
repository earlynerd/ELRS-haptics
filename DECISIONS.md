# Decision Log

Forward-facing, append-only record of architectural and behavioral decisions for this project. Search this file when structural history can affect the task; newer applicable decisions supersede conflicting older statements.

When a decision is reversed or superseded, append a new entry rather than rewriting the old one.

## 2026-09-11 - Eight-channel attitude-feedback wrist unit

- **Decision:** Start one reusable KiCad design for each wrist: ESP32-C6, an eight-channel I2C mux, and eight DRV2625-controlled actuators; receive craft telemetry through the ELRS ESP-NOW backpack path.
- **Why:** The user wants a spatial mechanosensory attitude cue and has selected the mux architecture. Assembly difficulty is not a design constraint. Do not substitute thrust or angular-rate feedback for the user's attitude-feedback goal.
- **Supersedes:** (initial)
- **Affects:** hardware/haptic-bracelet.kicad_sch, hardware/haptics.kicad_sch, README.md.

## 2026-09-11 - Initial schematic implementation choices

- **Decision:** Provisionally use an ESP32-C6-MINI-1, TCA9548APWR at 0x70, and DRV2625 YFF pin maps with no driver footprint assigned. GPIO6/7 provide SDA/SCL; GPIO18 resets the mux; GPIO19 releases the shared driver reset. A common 3V3 rail is assumed pending actuator/power selection.
- **Why:** Establish an editable, connected schematic while keeping package, supply, actuator and mechanical decisions explicit. Module choice and GPIO assignments are starting proposals. TI sources currently inspected identify the YFF pinout only.
- **Supersedes:** (initial implementation)
- **Affects:** hardware/, README.md. The battery/power sheet is reserved; the PCB is initialized without layout.

## 2026-09-11 - Distributed 1S parallel battery pack

- **Decision:** Each wrist uses one series cell group with an open number of parallel pouch cells (1S-NP). Leave capacity, cell dimensions and runtime target open. Cells may occupy separate bracelet segments.
- **Why:** The user explicitly capped the series count at 1S and requested flexibility in the number of parallel cells.
- **Supersedes:** Previously unspecified series/parallel battery topology.
- **Affects:** README.md and docs/power-architecture.md. The proposed charger, buck-boost regulator and protection implementation remain design candidates pending circuit work and cell selection.

## 2026-09-11 - USB-C power and native ESP32-C6 Serial/JTAG

- **Decision:** Use USB-C 5 V input and route USB2 D-/D+ to GPIO12/GPIO13. Implement BQ25186 charging and TPS63802 regulation. TUSB320LAI provides sink-only CC/current detection at 0x47. Add hardware startup current limiting and default-disabled charging; higher input current requires source permission.
- **Why:** The user accepted the power plan and requested native USB data on the charging connector. BQ25186's 500 mA input-limit default alone does not address preconfiguration USB operation. The native C6 interface supplies flashing, console and JTAG.
- **Supersedes:** Candidate-only power implementation and UART-only wired programming.
- **Affects:** hardware/usb.kicad_sch, hardware/power.kicad_sch, controller GPIOs, docs/usb-power-implementation.md. Protected 1S pack construction, cell limits, final footprints, firmware and physical validation remain open.

## 2026-09-11 - M2003 UART ring pods with shared reset

- **Decision:** Use eight M2003FC1AE/DRV2625/LRA pods per wrist, with the ESP32 as master of the music robot's 250 kbaud UART ring. Retain its enumeration, LDROM update protocol, and flash layout. Add a shared active-low M2003 reset; keep each driver's I2C local to its pod. One pod also houses the ESP32 and power electronics. Design pin assignments around the loader's existing startup outputs to minimize loader changes.
- **Why:** The user has these MCUs on hand and reports excellent ring operation and fast, reliable updates on the music robot. Reuse removes interface ICs and reduces each ordinary inter-pod link to power, ground, forwarded data, and reset; battery wiring is additional.
- **Supersedes:** Central I2C fanout in the first two entries; subsequent local-mux, translator, and I2C-loader proposals.
- **Affects:** Pod hardware, ESP32 host, pod application, and update tooling. Native schematics and README still describe the earlier mux circuit; migration and bracelet validation remain pending.

## 2026-09-12 - Switched pod power with firmware-managed UART states

- **Decision:** Switch all eight M2003/DRV2625 pods from 3V3 through TPS22918; leave ESP32 and charging control powered. GPIO3 enables power with a default-off pulldown. GPIO18 asserts shared reset through an NMOS with its reset pull-up on POD_3V3. Use GPIO19 TX and GPIO2 RX directly: assert pod reset, detach UART, drive TX low and disable the RX pull-up before power-off. Preserve PF0/PF1 loader UART pins and use PB13 for local driver reset. Disable charging before losing required pod temperature reports.
- **Why:** The user requested ring power shutdown and proposed GPIO states to avoid unnecessary signal isolators. The loader already drives PB13 low.
- **Supersedes:** Always-powered pod assumption; proposed UART isolation buffers. Implements the earlier M2003 UART ring decision in native schematics.
- **Affects:** Controller and pod schematics, ring firmware contract, docs/ring-pods.md. Firmware and bench validation remain open.

## 2026-09-12 - Fifth conductor for distributed parallel cells

- **Decision:** Add VBAT_RAW as pin 5 on every IN/OUT interface, alongside switched 3V3, GND, DATA and shared reset. Each populated cell branch joins VBAT_RAW through a local positive fuse. Define a high-side bidirectional pack protector interface at the main power board, keeping raw and protected positive rails separate with common GND.
- **Why:** The user explicitly requested the battery conductor needed to parallel distributed cells. Positive-path protection permits one common ground without bypassing a low-side disconnect.
- **Supersedes:** Four-conductor descriptions that excluded battery wiring. The ordinary inter-pod harness now has five conductors.
- **Affects:** Pod interfaces, power sheet J4, docs/ring-pods.md and power architecture. Cell/fuse selection and the actual pack protection circuit remain open.

## 2026-09-12 - VLV041235L flex contact candidate

- **Decision:** Evaluate the user-proposed VLV041235L with direct flex-to-PCB solder pads. Add a contact-only draft footprint with 1.8 mm pitch and separate body retention; leave schematic actuator placeholders until selection and fit are confirmed.
- **Why:** Vybronics explicitly supports direct PCB attachment of the double-sided flex contacts. Body placement remains a mechanical choice.
- **Supersedes:** No actuator candidate or contact geometry.
- **Affects:** hardware/HapticBracelet.pretty and docs/lra-candidate.md. S-821AAAI protector sourcing remains unresolved; other suffixes are not threshold-equivalent substitutes.

## 2026-09-12 - Central actuator opening and flexible pod links

- **Decision:** Use the user's proposed central LRA and housing mounting seat projecting through an opening in each pod PCB as the working packaging concept. Reserve surrounding volume for electronics and optional thin pouch cells; use Myo-inspired flexible links between rigid pods. Dimensions and exact link construction remain open.
- **Why:** Nesting the actuator within the PCB plane can reduce stack height and keeps its mechanical attachment to the wrist-facing housing independent of the board. Cell selection must fit the remaining usable volume, including tabs and clearance.
- **Supersedes:** Previously unspecified PCB/body arrangement; does not select a compliant actuator suspension.
- **Affects:** Pod mechanical layout and eventual PCB outlines. No dimensional CAD or PCB cutout is implemented yet.

## 2026-09-12 - First pod dimensions for a 195 mm wrist

- **Decision:** Record the user's measured wrist circumference as 195 mm. Sketch provisional regular shells at 20 x 34 x 10.5 mm and a main shell at 24 x 52 x 10.5 mm (circumferential x axial x radial), with 7 x 15 mm central board openings. Explore an outer cell compartment supported above the actuator in regular pods; reserve the main pod for electronics.
- **Why:** Establish a concrete packaging study while leaving actual cells and link fit open. Grow the main pod mainly along the arm to preserve circumferential space for all eight actuators.
- **Supersedes:** Unspecified dimensions in the central actuator opening concept; these dimensions remain proposals, not user-approved fabrication geometry.
- **Affects:** mechanical/pod-study, docs/lra-candidate.md and future PCB outlines. No physical fit or component layout qualification is claimed.

## 2026-09-12 - Bond cells directly to pod lids

- **Decision:** Follow the user's direction to bond each optional pouch cell to the lid's inner surface, with no separate cell compartment or supporting shelf. Revise the provisional shell thickness to 10 mm, retaining clearance above the actuator and electronics.
- **Why:** The lid provides the required support without another printed structure. The revised sketch allocates 16 x 28 x 3 mm for the cell envelope plus 0.2 mm lid adhesive; actual cell, adhesive and tolerance allowances remain open.
- **Supersedes:** The supported cell compartment and 10.5 mm thickness in the first dimensional study.
- **Affects:** mechanical/pod-study, docs/lra-candidate.md and README.md. PCB outlines remain unchanged.

## 2026-09-12 - Release reset driver during steady pod power-off

- **Decision:** Assert Q5 during pod power-down, then drive RING_RESET_ASSERT low after POD_3V3 and the reset capacitor discharge. Keep it low throughout steady off and assert it again before enabling the pod rail. Preserve TX-low/RX-no-pull-up states.
- **Why:** The user rejected holding the reset driver high while pods are off. Releasing its gate eliminates about 33 uA through R7; the reset net's pull-up references the discharged pod rail.
- **Supersedes:** Holding reset asserted throughout the off interval in the switched pod power sequencing.
- **Affects:** docs/ring-pods.md and docs/standby-and-controls.md. No circuit change is required; firmware and discharge timing remain unimplemented/unqualified.

## 2026-09-12 - Accessible wake button and RGB status

- **Decision:** Expose existing SW3 as the user wake/off button and add a discrete common-anode RGB D1 on GPIO4/5/15 with separate 2.2k resistors and 100k default-off pullups. Add provisional main-shell side-button and lid-window positions. Keep BOOT/RESET internal.
- **Why:** The user wants a button and RGB indication including charge state. Direct GPIO drive adds no LED-controller standby load. GPIO15 is biased high for native USB JTAG; GPIO4/5 only affect unused SDIO timing straps.
- **Supersedes:** Unallocated user controls and the interim single-color LED addition. GPIO4/5 are no longer spare wake inputs.
- **Affects:** Native controller/support schematics, packaging study C and standby documentation. LED/button MPNs, footprints, brightness and firmware are pending; indication colors are an initial proposal.

## 2026-09-12 - Six-wire chain with passive serial return

- **Decision:** Add pin 6 RING_RETURN to both wiring interfaces on all eight pods. Join only the last pod's TX, after its existing 33-ohm resistor, to this return through R53 (0 ohm). Return runs passively through the intermediate boards to ESP GPIO2. Use seven wired links and a purely mechanical clasp between the end and main pods.
- **Why:** The user wants to open the bracelet without an electrical disconnect. This folds the logical UART ring into a physical chain while retaining its enumeration and loader protocol.
- **Supersedes:** Five-conductor wiring and a serial closing connection across the clasp.
- **Affects:** Pod interfaces, main RX, ring overview, connectivity checks and mechanical link planning. Pad footprints, harness signal quality and current capacity remain to be validated physically.

## 2026-09-12 - Select stocked S-821AAAC high-side protector

- **Decision:** Select ABLIC S-821AAAC-H8T7S, with nominal 4.590 V overcharge and 2.500 V overdischarge thresholds, as directed by the user. Preserve the six-wire harness and common ground.
- **Why:** It has the lowest overcharge threshold among the stocked high-side variants in the supplied DigiKey export. The user accepts this threshold while relying on the charger for normal regulation. This does not establish protection within a conventional 4.20 V cell's permitted voltage under charger failure; cell compatibility remains unverified.
- **Supersedes:** The unresolved S-821AAAI sourcing choice and rejection of stocked high-side variants solely on overcharge threshold.
- **Affects:** docs/protection-sourcing.md and subsequent central protection circuit implementation. FETs, sense resistor and native schematic implementation remain pending.

## 2026-09-12 - Implement central pack protector and prototype current cutoff

- **Decision:** Replace J4's placeholder with a protection child sheet: U27 S-821AAAC-H8T7S, common-drain CSD17318Q2 FETs Q6/Q7, a 3 mOhm shunt R54, and the ABLIC reference filter/input network. Keep the six-wire chain and common ground.
- **Why:** Complete the selected prototype circuit using stocked supporting parts. R54 establishes a nominal 1.93 A discharge cutoff; its rating remains adjustable once cells, wire and load are known. The fixed charge-overcurrent threshold is 6.67 A; normal charge current remains the charger's responsibility.
- **Supersedes:** J4's unimplemented protection boundary and pending circuit status in the preceding selection entry.
- **Affects:** Native power/protection sheets, ABLIC footprint, protection/connectivity checks and standby budget. U27 adds 6 uA typical during normal operation and charger ship mode; layout and physical fault/recovery tests remain pending.

## 2026-09-12 - Mark unused DRV2625 trigger pins no-connect

- **Decision:** Per user request, remove the eight A1 TRIG/INTZ ground stubs and place no-connect flags at U3 through U10. No ERC rule suppression.
- **Why:** These pins are unused in the I2C-controlled design; they have internal pull-downs. This is a prototype departure from TI's unused-pin grounding recommendation.
- **Supersedes:** Grounded TRIG/INTZ pins and eight unresolved ERC warnings introduced during this thread.
- **Affects:** Eight pod schematics, connectivity checks and firmware I2C-only control assumptions. ERC now reports zero violations.

## 2026-09-12 - Eight protected batteries and distributed bulk capacitance

- **Decision:** Use eight protected 90 mAh batteries, one per pod, with a 3 x 12 x 32 mm YDL301230-class body. Keep factory PCMs intact; remove U27/Q6/Q7/R54-R56/C44 and connect the fused protected outputs directly to VBAT/U11 BAT. Add 22 uF 10 V X5R 0805 per pod; increase TPS22918 C42 to 4.7 nF.
- **Why:** User chooses off-the-shelf battery protection and additional local energy storage. Slower startup accommodates the added capacitance. Retain branch fuses and six-wire interconnect.
- **Supersedes:** Central S-821AAAC selection/implementation and open battery count. Study D supersedes study C allocations with 20 x 38 x 10.5 regular and 24 x 64 x 10.5 main shells, batteries bonded inside every lid.
- **Affects:** Schematics, checks, power/standby documentation and packaging study. Exact fuse/capacitor parts, PCM behavior, current sharing, firmware and physical fit remain unqualified.

## 2026-09-12 - First native placement and fit coupons

- **Decision:** Populate the PCB with all 269 components on eight unrouted islands, 0.8 mm board thickness. Use 17 x 35 mm satellite boards and a 21 x 61 mm main envelope recessed 5.1 mm under the antenna. Offset each 7 x 15 mm actuator cutout 1 mm left for the flex tail. Keep existing shell and eight-cell allocations.
- **Parts:** DRV2625YFFR and VLV041235L; USB4105-GF-A, EVQPUJ02K, LTST-C19HE1WT, TL3305AF160QG service switches. Assign TI power-package footprints and a DFE201612E-R47M=P2 body/land proposal. Move C3's 10 uF allocation to 0805.
- **Why:** Establish actual board space and hand-wired pod interfaces before routing. New footprints use source drawings; fuse selection and inductor land sign-off remain open.
- **Affects:** Native schematics/PCB, local footprints, net checks and mechanical fit coupons. Prototype copper-edge allowance is 0.25 mm and DRV local copper clearance 0.15 mm; BGA escape/stackup is not yet solved. Coupons use temporary lid retention, with no final PCB supports, TPU links or clasp. No routing/fabrication or physical qualification is claimed.

## 2026-09-12 - Four-layer JLCPCB boards and supply-reset drivers

- **Decision:** Use four copper layers at 0.8 mm nominal thickness, with ordinary 0.20 mm drill / 0.45 mm diameter through vias. JLCPCB is the preferred fabricator. Reserve In1.Cu for ground; satellite In2.Cu carries POD_3V3. Exact production dielectric stack remains to confirm.
- **Reset:** Tie each DRV2625 B2 NRST directly to C2 VDD, remove the eight reset pull-downs, and mark M2003 PB13 no-connect. The ESP32 controls hard recovery through the existing switched pod supply. Stop playback before loader entry; MCU-only reset no longer resets the driver. Power cycling resets all eight pods together.
- **Parts:** Select Littelfuse 0467.250NR 250 mA 0603 branch fuses (DigiKey F1389CT-ND), and replace the proposed Murata inductor lands with the DFE201612E manufacturer land pattern. Factory battery PCMs remain fitted.
- **Why:** User explicitly chooses four layers and existing power control for recovery. Direct B2-C2 routing avoids centre-ball via-in-pad fabrication.
- **Affects:** Revision 0.7 schematics/PCB, reset firmware contract, local footprints and connectivity checks. The count becomes 261 components. Fuse coordination, discharge/restart timing and physical manufacture remain unqualified.

## 2026-09-12 - Satellite routing checkpoint

- **Decision:** Merge locally closed routing for pods 1-7 into the eight-island PCB. Keep In1.Cu free of signal tracks; use In2.Cu primarily for POD_3V3 with reset and end-bridge signal exceptions. A short B.Cu link reconnects pod 7's isolated pull-up supply section.
- **Evidence:** All seven isolated boards have zero native DRC violations and zero opens. After merging, no satellite-local opens reappear; schematic parity is zero, all 947 electrical pads match the netlist, and all 416 vias are ordinary 0.45/0.20 mm through vias without drilled holes overlapping SMD lands.
- **Remaining:** Main pod 0 has 277 local opens and six warnings; 42 additional combined-board ratsnest items cross externally wired islands. Main power/USB/RF routing, final stack selection and fabrication preparation remain pending.
- **Affects:** Native PCB, docs/pcb-routing.md and hardware/verification/routing/. Historical placement evidence remains under verification/placement; the old placement generator is guarded against overwriting revision 0.7.

## 2026-09-13 - User placement repeated across seven satellites

- **Decision:** Use the user's pod-6 functional placement and aligned wire pads for pods 1–7. Complete signals on F.Cu/B.Cu only; retain In1 ground and In2 POD_3V3 with a VBAT perimeter strip. This supersedes the revision-0.7 inner signal exceptions. Place pod 7's R53 bridge in the lower bay.
- **Rules:** Retain the user's current project constraints, including 0.1016 mm minimum track width and 0.50/0.20 mm minimum via diameter/drill. Use 0.60/0.30 mm ordinary through vias and 0.50/0.20 mm constrained escapes. New BGA tracks are 0.11 mm. Eight vias are in hand-soldered wire pads; none overlap component solder lands.
- **Evidence:** All seven isolated satellites pass DRC with zero violations/opens. Combined parity is zero, all 947 pads match the schematic, and no satellite-local opens remain. There are 325 satellite vias. The main-board footprints/tracks and project rules are preserved from the user's starting files.
- **Remaining:** Main routing has 277 local opens, six warnings and a 0.1000 mm driver tie below the current minimum width; 42 other connectivity items cross externally wired islands. Final production stack, fabrication and physical qualification remain pending.
- **Affects:** Native PCB, README, docs/pcb-routing.md and verification/routing-v08/. The user's saved starting files are backed up under hardware/backups/user-placement-20260913/.

## 2026-09-13 - Six-mil satellite template

- **Decision:** Clone the user's cleaned second pod-6 layout to all seven satellites. Require at least 6 mil track width, no drilled vias in solder pads, and horizontal/vertical/45-degree traces. Preserve the pod-7-only return bridge and the inner ground/power planes.
- **Why:** The user's placement and routing remove the need for the narrower escapes, wire-pad vias and arbitrary angles in the earlier automated pass.
- **Supersedes:** Revision-0.8 satellite routing geometry and its via-in-wire-pad allowance. Circuit architecture is unchanged.
- **Affects:** Native PCB, docs/pcb-routing.md and verification/routing-v09/. Main-board placement remains unchanged; docs/main-board-placement.md is a proposed functional allocation rather than an accepted placement.

## 2026-09-13 - Separate PCBA masters and wired schematics

- **Decision:** Maintain `hardware/main/` and `hardware/satellite/` as independent KiCad projects, each with one PCB. One wrist uses one main and seven copies of the same satellite. Any later JLCPCB panel is a derived output under `hardware/panel/`.
- **Selector:** Replace the end-only R53 variant with universal JP1: pad 2 feeds upstream return, pad 1 is downstream return, and pad 3 is local TX after its series resistor. Factory 1–2 is NORMAL; cut 1–2 and solder 2–3 on the last satellite. Never bridge all three. The six-wire chain and mechanical clasp remain unchanged.
- **Drawing convention:** Preserve the user's redrawn top sheet. Redraw child sheets with support parts wired in functional groups, using labels for power and circuit/sheet boundaries. Use canonical `+3V3` and `+3V3_POD` names.
- **Preservation:** No missing components, changed values or changed footprint assignments were found in the user's redraw. Repair its split power aliases and remove the obsolete dangling QOD wire/label. Archive the original combined project intact; retain its starting hashes. Main references and placement are preserved; satellite references are renumbered locally from the user's pod-6 template.
- **Evidence:** Both projects have zero ERC violations and zero schematic/PCB parity issues. The satellite has 223 segments, 45 through vias, zero DRC violations/opens, 6 mil minimum tracks, no via-in-pad and no inner-layer signals. Main retains 277 opens and six silk/library warnings; its existing narrow driver tie is widened to 6 mil. Native files are the editable sources; migration scripts are provenance.
- **Remaining:** Main placement/routing, final production stack and derived panel are pending. This does not establish physical fit, firmware operation or manufacturing qualification.


## 2026-09-13 - Five-wire harness and power-cycle recovery

- **Decision:** Remove the shared MCU reset conductor and ESP32 Q5/R6/R7/R44/C40 reset circuit. GPIO18 becomes spare. Each MCU retains local ICE reset with its internal pull-up; whole-chain recovery uses U26 power cycling. Retain harness numbering 1/2/3/5/6, marking pad 4 NC to preserve existing placement/routing.
- **Why:** The user wants every hand-soldered wire to earn its keep; power control already provides recovery. This removes fourteen solder joints per wrist. Remove redundant main J100 as discussed.
- **Supersedes:** Shared reset and six-wire harness provisions in earlier entries. Host sequencing must now accommodate individual POR timing and full rail discharge.
- **Affects:** Both PCBA schematics/PCBs, ring-pods.md, pinout and preservation checks. Placement is user-owned; the exploratory main placement candidate was not applied. Local internal-pull-up operation and loader timing remain bench checks.


## 2026-09-13 - Compact five-pad harness interfaces

- **Decision:** Use WirePads_5_P2mm for main J101 and satellite J1/J2, with pins 1 switched 3V3, 2 GND, 3 forward UART, 4 VBAT, 5 serial return. Keep 2 mm pitch, 1.4 x 1.6 mm lands and no paste.
- **Why:** User requests removal of the unused physical pad as well as the reset wire. Each bank becomes 2 mm shorter; the first three lands stay fixed. Adjust only VBAT/return connections and legends; other placement stays unchanged.
- **Supersedes:** Five-wire harness on six-position banks with NC pad 4. Old harness VBAT/return pins 5/6 are now 4/5; local ICE pad numbering is unchanged.
- **Affects:** Both schematics/PCBs, shared footprint, harness documentation and checks. Satellite remains fully routed with no new vias.


## 2026-09-13 - Passive USB-C sink and direct charger input

- **Decision:** Replace U13 with independent R60/R61 5.1k CC pull-downs. Remove U16/U17, Q2/Q3, R26-R33 and C31/C33; connect USB_VBUS directly to BQ25186 IN. Retain data/CC ESD, VBUS sensing, bypass capacitors and native USB data.
- **Why:** User accepts ordinary 5 V source compatibility tradeoffs for this prototype; external current-mode selection and CC detection do not justify their size/complexity. Charger input limiting replaces the external current selector, including its former low-current startup clamp.
- **Supersedes:** TUSB320 attachment/current-advertisement handling and the TPS2553/TS5A3159 current-limit architecture. GPIO0/14/22/23 are spare. Firmware uses charger registers and VBUS sensing; startup defaults remain part of the chosen source policy.
- **Affects:** Main schematics/PCB, USB and standby docs, circuit checks. Retained component placement and satellite files are unchanged.


## 2026-09-13 - Symmetric pod cell and thermistor interfaces

- **Decision:** Retain main J200/F100 and J103 as equivalents of satellite J4/F1 and J5. Remove main J3; fit R62 (10k) from charger TS/MR to ground, retaining SW3 in parallel. All eight cell thermistors feed their local M2003 ADCs.
- **Why:** One cell and temperature interface per pod preserves symmetry and removes duplicate main-pod connections. Firmware must gate charging on valid, fresh, in-range readings for every required cell, and disable charging before pod power-off or loader entry. The charger no longer has independent cell-temperature sensing.
- **Also:** Remove R48/R50/R52 LED pull-ups. GPIO4/5 SDIO straps are unused; GPIO15 JTAG selection is ignored with default JTAG_SEL_ENABLE, which we will not burn.
- **Supersedes:** Main J3 charger-thermistor provision and RGB default-off pull-ups.
- **Affects:** Main schematic/PCB, power and standby docs, circuit checks. Retained placement and satellite source files are preserved.


## 2026-09-13 - USB-only ESP service and charger input-status sensing

- **Decision:** Remove main J1 UART service bank without replacement test points. Remove Q4/R34/R35/R36 VBUS detector; leave GPIO1 and UART0 RX/TX NC. Native USB Serial/JTAG handles programming/debug, with SW1/SW2 retained for reset/ROM download.
- **Why:** The small main board benefits from fewer footprints and connections; existing USB and charger I2C cover these functions. Firmware reads charger VIN_PGOOD_STAT for usable input power, rather than a discrete VBUS GPIO.
- **Supersedes:** Main UART service connector and VBUS_nPRESENT firmware interface.
- **Affects:** Main schematic/PCB, USB and standby notes, connectivity checks. Retained placements, satellite design, and charge-enable gating are preserved.


## 2026-09-13 - First controller and pod firmware contract

- **Decision:** Start firmware as portable protocol code, an ESP32-C6 ESP-IDF controller, and an M2003 pod application. Borrow the music robot's 250 kbaud framing, store-forward enumeration, boot mailbox, flash geometry, packager, and unchanged LDROM sources by explicit path. Reserve new bracelet opcodes `0x11`/`0x12` for RTP/all-stop; do not reuse motor duty semantics.
- **Safety:** Require exactly eight pods and valid MSPv2-wrapped CRSF attitude from one configured ESP-NOW source. Send at 50 Hz, stop locally after 100 ms without haptic commands, and reject controller attitude older than 250 ms. Keep charging disabled. Use a provisional, documented absolute-attitude matrix.
- **Driver:** Auto-calibrate each DRV2625 for the proposed 240 Hz LRA, limit the first-pass clamp to its stated 1.85 Vrms operating ceiling, and require successful status before RTP.
- **Affects:** `firmware/`, README status, ring behavior, telemetry provisioning, and bench qualification. Builds do not establish flashing, timing, thermal, perceptual, or loader-ring evidence.

## 2026-09-13 - Latched manual USB bring-up console

- **Decision:** Add a native USB `hb` console that accepts partial-ring enumeration and addressed status checks, but latches manual mode before bus or actuator diagnostics. Limit single-pod RTP tests to amplitude 64 and 10-250 ms, refresh every 20 ms, then issue addressed stop and broadcast all-stop. Only explicit `hb flight` releases manual mode, and it still requires exactly eight pods and fresh telemetry for output.
- **Why:** First hardware should be testable one pod at a time without weakening normal-flight interlocks or requiring a complete bracelet to diagnose a single driver.
- **Supersedes:** The first firmware contract's exact-eight restriction for diagnostic enumeration only; its flight-output requirement remains unchanged.
- **Affects:** ESP32-C6 console selection, ring receive/locking, controller modes, `firmware/protocol.md`, and `firmware/BRINGUP.md`.


## 2026-09-13 - Main Tag-Connect and compact placement checkpoint

- **Decision:** Apply the requested placement pass to the main master, preserving U1/J2/J101/J200/J103/M1 positions. Use the user's TC2030 J1 in place of J102 and remove C29/C30 as requested. All 70 footprints remain on F.Cu; functional groups fit around the actuator opening. D1 is beside the ESP32 and SW3 is on the left edge.
- **Schematic:** Preserve the user's latest redraw, ground and C1 junction repairs. Retain the new VBUS/VSYS power names; restore three external-supply PWR_FLAG directives. The Tag-Connect reset output is open drain; keep the selected M2003 internal pull-up and document its one ERC input-driver item rather than adding components.
- **Evidence:** Both PCBA preservation checks pass. Main: zero parity errors, three silk/library warnings, 196 opens. Satellite: zero ERC/DRC/opens, unchanged source. Accepted positions and before-apply backups are documented in docs/main-board-placement.md. Routing and enclosure access remain to be completed.


## 2026-09-13 - One fitted switch and underside ESP recovery pads

- **Decision:** Remove SW1/SW2 and use bare J3 EN/GND/BOOT pads on B.Cu, accessible through an underside service opening clear of the lid-mounted cell. Keep R3/C1 reset bias, R5 boot pull-up and SW3 as the sole side-actuated user button.
- **Why:** Native USB handles normal flashing/JTAG; manual GPIO9-low/reset access remains for firmware recovery without two tall switches. Hold BOOT low, pulse EN low, release EN then BOOT.
- **Placement:** Reorder USB, I2C and boot passives beneath their ESP pins, move R42 to TX, and move D1 into the freed lower-left space. Preserve other functional groups and edge anchors. Enclosure service opening and LED window still need corresponding mechanical updates.


## 2026-09-13 - Routing clearances, drills and direct plane connections

- **Decision:** Use 6 mil copper/zone clearance and minimum track width, via drills at least 0.25 mm, and 0.20 mm copper-edge clearance on both PCBA masters. Use direct plane connections, with solid footprint/pad overrides and solid existing zones.
- **Implementation:** Remove undersized routing presets; increase seven satellite via drills from 0.20 to 0.25 mm. Preserve positions and copper diameters; refill the satellite planes. Default track width remains 0.20 mm, with 6 mil available for tighter routes.
- **Evidence:** Satellite remains DRC-clean and fully connected; main has no new errors. These constraints supersede the earlier 0.20 mm drill and 0.15 mm driver-clearance settings.

## 2026-09-13 - Claspless co-printed Myo-style band

- **Decision:** Join all eight rigid pod shells with paired TPU U-flexures and co-print the aligned rigid and soft volumes as one permanently closed band. Use the same flexure at the unwired end-to-main gap; do not add a clasp, separate strap, pin, screw or modeled TPU interlock. Let the slicer resolve the shared material interface.
- **Why:** The supplied Myo reference and user direction establish the intended mechanism directly: rigid modules connected by integral soft U-loops, with no opening hardware.
- **Supersedes:** The mechanical clasp portion of “Six-wire chain with passive serial return.” The current five-wire electrical chain remains unchanged: seven wired gaps and one unwired TPU seam.
- **Affects:** `mechanical/myo-band-v0.7/`, `tools/build_myo_band.py`, bracelet overview and ring-pod mechanical documentation. Fit, preload, TPU fatigue, slicing, printing and body testing remain open.

## 2026-09-14 - Flat co-printed housing assembled into a ring

- **Decision:** Print the eight shells as an open flat strip with paired bed-level TPU hinges, then close the unwired joint using flexible tabs over main-lid retaining buttons. Target the user's H2D and proposed PET-GF15/TPU combination. Leave material bonding to the slicer. Retain the 195 mm wrist reference and existing pod body footprints.
- **Why:** The user requests flat printing followed by ring assembly. The TPU grade remains open; 1 mm hinges and tab fit are provisional parameters. The tab/button closure is the first implementation choice, not a user-qualified permanent joint.
- **Also:** Add native-outline-referenced PCB support ledges, external lid screw bosses and 1.2 mm lids (10.7 mm closed body depth). Refresh main service openings from current native footprint positions. Preserve board and battery sources; check bare-board/battery allocations, USB opening and lid clearance in CAD.
- **Supersedes:** The upright-print, permanently closed mechanical architecture in "Claspless co-printed Myo-style band" for the new v0.8 prototype. Keep v0.7 files intact. The five-wire, seven-gap electrical chain is unchanged.
- **Affects:** `mechanical/flat-band-v0.8/`, `tools/build_flat_band.py`, `tools/render_flat_band.py`, project overview and ring-pod mechanical description. CAD/mesh checks do not establish slicing, printed fit, populated-board retention, wire strain relief, closure fatigue or operating qualification.


## 2026-09-14 - Planar Myo end rails and a main-shell assembly seam

- **Decision:** Follow the user's red/blue sketch: two continuous TPU rails along the axial pod ends, turning inward in the flat XY plane as paired U-folds at all eight inter-pod gaps. The upper and lower folds can change shape independently; the taller main pod has longer end transitions. Keep PET-GF15/TPU, H2D flat printing and slicer-managed material bonding.
- **Assembly:** Split the main shell at local X=7 mm so its portions print at the two strip ends. Two floor keys locate them; one 2 mm main lid and four screws close the housing. This preserves eight compliant joints and removes inter-pod closure straps/buttons. Satellite bodies, lids and the electrical chain are retained.
- **Why:** The user wants stretch and angular compliance to follow noncylindrical wrists/forearms. Their sketch explicitly establishes planar end folds; neither straight bed-level links nor radial upright U-loops satisfy that geometry.
- **Supersedes:** The straight hinges and tab closure in "Flat co-printed housing assembled into a ring" for the new v0.9 prototype. Earlier revisions remain intact.
- **Evidence:** Sixteen spring-to-neighbor contact checks, valid STEP reimports, bare-board/battery allocations, sampled main seam/lid assembly motion, USB aperture and exported mesh checks pass. The 195 mm circular reference and illustrated oval/taper pose are layout aids, not force/strain or physical fit qualification.
- **Affects:** `mechanical/myo-flat-v0.9/`, `tools/build_myo_flat_v09.py`, `tools/render_myo_flat_v09.py`, README and ring-pod description. TPU selection, usable travel, stiffness, seam strength, populated-board retention and harness motion remain physical design work.

## 2026-09-14 - Full-height ribbons and stepped main clamshell

- **Decision:** Implement the user's tape-like TPU ribbons at the full 9.5 mm shell-wall height. Retain paired inward plan-view folds at every gap. Replace projecting screw ears with rounded full-width shoulders and recessed countersunk heads.
- **Closure:** Place the whole wrist-facing main floor at one strip end and the whole outer face at the other. Complementary full-height wall portions form the stepped seam shown in the user's latest drawing. Ribbon ends stop at their wall edges and butt together when the clamshell closes. Neither free ribbons nor closure joints taper or change Z datum. The local X=18 mm wall handoff avoids the USB opening; a service relief in the embedded rail preserves USB access.
- **Why:** The user explicitly requires constant ribbon height and joining ribbon ends through housing assembly. This supersedes v0.9's left/right division through the main floor and its 1.2 mm-tall TPU geometry. The stepped seam follows the latest drawing rather than a uniform horizontal half-height wall split.
- **Printing:** The 239.2 x 72 x 11.5 mm strip includes the main roof; seven satellite lids remain separate. Local support is required beneath the terminal roof. Four recessed main screws retain the halves using lower-floor posts. Material bonding remains slicer-managed.
- **Evidence:** Valid CAD/STEP, electronics/USB clearance, full-height ribbon-joint gauges and sampled clamshell closing checks pass. Exported mesh and package evidence are in `mechanical/myo-flat-v0.10/`. These checks do not establish printing, fatigue, comfort, seam strength or harness qualification.
- **Affects:** `tools/build_myo_flat_v010.py`, `tools/render_myo_flat_v010.py`, v0.10 delivery files and project mechanical descriptions. Previous releases and native hardware sources remain unchanged.


## 2026-09-14 - Supported main ribbons and subtractive main case

- **Decision:** Bond the long main TPU runs to the outside walls down to the satellite end positions. Use identical free U-fold geometry at all eight gaps. Preserve satellite geometry.
- **Main case:** Cut the cavity, ports and mating seats from one rounded rectangular envelope. Retain whole wrist/outer faces, stepped closure and constant-height ribbon butt joints. Replace isolated posts with integrated end walls, using recessed M2 x 8 mm main screws. Main end inlays narrow to 1.2 mm to retain material around the pilots.
- **Why:** The user's slicer screenshot identified extra free main-leg length and requested a coherent rectangular housing with two hollow mating halves.
- **Supersedes:** Main transition and standoff details in “Full-height ribbons and stepped main clamshell.”
- **Affects:** v0.11 CAD, coupons and mechanical descriptions. The v0.10 screenshot is slice evidence; v0.11 physical fit and stiffness remain unverified.


## 2026-09-14 - Universal haptic pods with a stacked controller

- **Decision:** Build eight identical universal pod PCBAs and one controller daughterboard. Pod 0 sits beneath the controller without a battery or external NTC; pods 1-7 each carry both. Retain all universal-board components, local ICE and the existing JP1 selector.
- **Interface:** Controller J101 connects pin-for-pin to pod 0 J1: switched 3V3, GND, ESP TX, protected VBAT and UART return. Pods 0-6 use NORMAL; pod 7 uses END. Eight-node loader topology and power-cycle reset remain unchanged.
- **Why:** Additional main-pod height is preferable to the larger integrated board footprint. Seven 160 mAh 301730 cells are a candidate for 1,120 mAh; exact part, protected dimensions and ratings remain unverified.
- **Supersedes:** The integrated main haptic/battery circuit and eight-cell packaging baseline. Previous routing and mechanical files remain historical references.
- **Affects:** Main schematic/PCB inventory, assembly instructions, panel quantities and pending seven-sensor firmware policy. Daughterboard mechanics and placement remain open.

## 2026-09-14 - Matching board outlines and diagonal locating holes

- **Decision:** Match the controller to the universal pod's 17 × 35 mm, R1 outer contour, with no actuator cutout on the controller. Add matching 2 mm NPTH H1/H2 holes at local (15, 1.8) and (2.5, 32.5) mm on both PCBAs.
- **Why:** The user prefers the smaller stacked footprint and explicitly requires mounting positions on opposite sides. Printed locating pins with lid/ledge retention are provisional; VHB remains an option.
- **Placement:** Preserve all existing electrical parts and routes. The user will reshuffle them around the holes and smaller controller perimeter; clearance conflicts remain visible rather than excluded.
- **Affects:** Both native schematics/PCBs, library tables and geometry checks. The pre-edit sources are in `hardware/backups/pre-matched-outlines-20260914/`. Enclosure and stack-height work remain open.

## 2026-09-15 - PCB faces clamp a TPU spacer using four corner fasteners

- **Decision:** Expand both active boards to the regular pod's 20 × 46 mm, R2.5 outside contour. Use the universal board as the skin-facing plate and the controller as pod 0's outer plate. Retain VLV041235L with its supplied adhesive; remove the lower-board actuator cutout.
- **Mounting:** Four shared corners at local (3.5, 3.5), (16.5, 3.5), (3.5, 42.5), (16.5, 42.5) mm. Lower: M1.6 closed-base SMT standoff family, Ø3.3 body/Ø4 land. Upper: Ø1.8 screw clearance. Final standoff height and screw length remain open.
- **TPU:** Draw a 1.2 mm contact band and a 1.5 mm placement inset, with Ø4.6 corner relief. Preserve user electrical placement/routing for rearrangement.
- **Supersedes:** Two locating holes, 17 × 35 mm internal-board outlines and the separate rigid skin-contact shell. Blank upper-plate fabrication files, spacer CAD and thinner-board trials remain future work; active stackups stay 0.8 mm/four layers.

## 2026-09-15 - Move corner mounts into the TPU contact band

- **Decision:** Move all four mounting centres outward by 0.75 mm on both axes: local (2.75, 2.75), (17.25, 2.75), (2.75, 43.25), (17.25, 43.25) mm. Matching upper screw holes and lower standoff lands retain the same shared pattern.
- **TPU:** Move the matching diameter 4.6 mm relief circles with the mounts. Intentional overlap with the contact band allows the standoffs to pass through the TPU frame; spacer CAD must account for the corner reliefs.
- **Validation:** Electrical placements, pads, routes and project settings preserved. Satellite DRC/open count remains zero; controller has 20 DRC findings and 146 opens during placement. Sources before this move are in `hardware/backups/pre-outward-mounts-20260915/`.

## 2026-09-17 - Outward top-push user switch

- **Decision:** Replace SW3's EVQPUJ02K side switch with Panasonic EVPAWBD4A, 1.6 N and 0.6 mm high, on outward B.Cu at its saved centre. Preserve TS/MR/GND connectivity and other placement/routing.
- **Why:** The controller PCB is also the outer shell, so the button must press through its outer face.
- **Supersedes:** Side-actuated SW3 in the one-fitted-switch decision of 2026-09-13.
- **Affects:** Main power schematic, PCB and project footprint. Attach a clearly labeled datasheet-derived nominal STEP body because a downloadable exact model was not found. Protective cover and physical feel remain pending; see `docs/pcb-sandwich.md`.

## 2026-09-17 - Functional-group placement refinement

- **Decision:** Place R4/R5, R24/R25, C2 and R42/R43 on B.Cu beside their U1 pins. Consolidate U26 control passives and LED resistor R51 on F.Cu, move U14 toward USB data pads, and clear C41 from the connector courtyard.
- **Why:** Prefer short local same-layer terminations within functional groups, while preserving fixed mechanical anchors and the coherent charger/regulator groups.
- **Preservation:** Circuit, connectors, module, switch, recovery pads, mounting pattern and project rules remain unchanged. Keep the U1 antenna courtyard and its mounting warnings; RF/fastener resolution is still open.
- **Affects:** Main PCB placement; details and before/after evidence in `hardware/verification/main-group-refinement/README.md`. Routing remains pending.

## 2026-09-17 - Restore user's main-board placement

- **Decision:** Revert the entire assistant functional-group placement pass to the exact pre-pass PCB backup, retaining the accepted SW3 replacement.
- **Why:** The PCB is the housing: internal components belong on F.Cu; B.Cu is for deliberately exposed parts. The assistant's support-passive layer changes violated this constraint.
- **Supersedes:** Functional-group placement refinement above. Candidate reports remain historical only.
