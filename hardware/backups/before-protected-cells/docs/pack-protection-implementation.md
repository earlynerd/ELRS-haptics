# Prototype pack protection

The native `hardware/protection.kicad_sch` child sheet replaces J4's provisional boundary. It implements the selected S-821AAAC-H8T7S as U27, with one central high-side disconnect and common cell/system ground. The interpod harness remains six conductors.

| Reference | Part | Role |
| --- | --- | --- |
| U27 | ABLIC S-821AAAC-H8T7S | Voltage/current detection and charge-pump gate drive |
| Q6, Q7 | TI CSD17318Q2 | Charge and discharge N-channel FETs, common drains |
| R54 | D1MPC0805DR003FF-T5 | 3 mOhm, 1%, 0.5 W, 0805 shunt |
| R55 | 1 kOhm | Filter/protection resistor between U27 VSS and system ground |
| R56 | 22 ohm | Protected-positive input to VM |
| C44 | 100 nF | Decoupling directly across U27 VDD and VSS |

MPNs, manufacturers and DigiKey cut-tape codes are stored on the selected IC, FET and shunt symbols. DigiKey public pages showed stock for both supporting parts on the research date; these are observations, not reserved inventory. Supporting sources: [CSD17318Q2](https://www.digikey.com/en/products/detail/texas-instruments/CSD17318Q2/9462582) and [D1MPC0805DR003FF-T5](https://www.digikey.com/en/products/detail/thin-film-technology-corp/D1MPC0805DR003FF-T5/16735334).

## Connectivity and layout

`VBAT_RAW -> R54 -> Q6 source -> Q6 drain / Q7 drain -> Q7 source -> BAT_PROTECTED -> BQ25186 BAT`.

U27 CO drives Q6 and DO drives Q7. VDD senses the raw side of R54; VINI senses its FET side. Route those traces separately to the respective shunt pads, excluding load-carrying trace resistance from the sensed voltage. Use wide copper for the load path. The two drain pads connect only to each other.

The ABLIC reference circuit places R55 in the IC's negative supply/reference lead. U27 VSS, TH and the bottom of C44 share `PROT_VSS`; only R55 connects that node to GND. No battery/load current flows through R55. TH is tied to VSS because this suffix lacks temperature protection; PS is explicitly left open because it lacks power-saving control. The existing charger and pod temperature provisions remain responsible for temperature supervision.

The ABLIC footprint follows the published 0.18 mm circular lands, 0.40 mm row pitch and 0.76 mm column spacing. The package is 1.08 x 1.52 mm. Bottom-view ball numbering has been mirrored into PCB top view: A1 is upper left and A2 upper right. A 0.025 mm mask expansion is a prototype footprint choice, to be checked against the chosen fabrication process. FETs use the existing `Package_SON:Texas_DQK` footprint; physical pin maps include source pad 7 and drain pad 8.

## Prototype trip settings

The 3 mOhm shunt is a starting value for an approximately 2 A discharge cutoff, not an established cell or harness rating. Final selection depends on the actual cells, number populated, wiring, startup current and simultaneous actuator load.

| Condition | Nominal threshold | Nominal delay |
| --- | ---: | ---: |
| Overcharge | 4.590 V | 512 ms |
| Overdischarge | 2.500 V | 64 ms |
| Discharge overcurrent | 1.933 A | 128 ms |
| Short circuit (shunt comparator) | 6.833 A | 280 us |
| Charge overcurrent | 6.667 A | 32 ms |

These delays precede the additional physical FET turn-off time. The IC also has a VM-based load-short detector. With IC threshold tolerance and a 1% shunt at 25 C, discharge detection spans approximately 1.58 to 2.29 A. Across -40 to +85 C, including shunt TCR, the calculation expands to about 1.41 to 2.47 A. The reproducible calculations and all three current ranges are in `hardware/verification/pack-protection-checks.json`.

The charge and discharge thresholds are coupled by this suffix's fixed comparator values: the charge fault threshold is much higher than the BQ25186's 1 A maximum programmed charge current. Normal charging current must still be programmed for the populated cells. The accepted 4.590 V prototype overcharge limitation is recorded in [sourcing](protection-sourcing.md); review it with the final cell selection before commercialization.

At 2 A, the nominal shunt loss is 12 mW. Using each FET's 30 mOhm maximum at 2.5 V gate drive and 25 C gives 240 mW for the pair at 2 A, before hot-resistance growth. This conservative calculation avoids treating the 4.5 V Rds(on) specification as guaranteed at the protector's nominal 4.2 V gate drive. Each FET is rated for 30 V VDS, +/-10 V VGS and at most 1.2 V gate threshold; the protector drives gates above their source potentials. Physical turn-off, transient stress and copper-dependent temperature rise remain bench/layout checks.

## Standby and recovery

U27 consumes 6 uA typical, 10 uA maximum at 25 C, and 14 uA maximum across -40 to +85 C under the stated 3.4 V test conditions. It remains powered during BQ25186 ship mode. This suffix has no power-down function; its overdischarge current is specified separately (1 uA maximum at 25 C under the 1.5 V test condition).

After initial cell connection, USB charger connection may be needed to enable discharge. Undervoltage recovery occurs at 2.800 V without a charger, or at the detection threshold with an appropriately connected charger as specified by ABLIC. Overcurrent recovery uses the load-disconnection variant; connecting the USB-powered charger can raise the protected terminal to release the condition. Recovery while the charger/regulator remain connected must be tested on the assembled system. Deeply depleted charging is inhibited below nominal 1.550 V; no firmware override is added.

## Evidence and scope

- [ABLIC datasheet](https://www.ablic.com/en/doc/datasheet/battery_protection/S821AA_E.pdf), cached as `hardware/datasheets/S821AA.pdf`: variant pp.5-7; pins p.8; electrical limits pp.10-15; recovery pp.22-25; circuit p.34; package/lands pp.48/51.
- [TI FET datasheet](https://www.ti.com/lit/ds/symlink/csd17318q2.pdf), cached as `CSD17318Q2.pdf`: pinout p.1; electrical limits p.3; package pp.9-11.
- [TFT resistor datasheet](https://media.digikey.com/pdf/Data%20Sheets/Thin%20Film%20Tech%20PDFs/D1MPC%20Series.pdf), cached as `D1MPC.pdf`: order code p.1; 0805 electrical specifications p.3.

`tools/check_pack_protection.py` checks exported topology against independently transcribed pin maps, checks physical footprint pad numbers, and calculates tolerance ranges. Ring and USB connectivity checks remain applicable. These checks do not establish physical protection performance, transient behavior, final pack compatibility or fabrication readiness. Board layout and cell-branch fuse ratings remain open.
