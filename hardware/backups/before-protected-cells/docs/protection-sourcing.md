# 1S protector sourcing — 2026-09-12

Status: S-821AAAC-H8T7S selected by user direction and implemented as U27 in the native protection sheet. No harness change is required. See [implementation and validation](pack-protection-implementation.md). Historical screening below predates the user's prototype selection.

## Selected part: S-821AAAC-H8T7S

Select ABLIC S-821AAAC-H8T7S, DigiKey cut-tape code `1662-S-821AAAC-H8T7SCT-ND`. The user's export shows 6,000 in stock, minimum quantity 1. [DigiKey product](https://www.digikey.com/en/products/detail/ablic-inc/S-821AAAC-H8T7S/25649783).

- High-side switching and sensing preserve the common ground and six-conductor harness.
- WLP-8V package, 1.08 x 1.52 mm.
- Nominal overcharge detection/release: 4.590 / 4.390 V.
- Nominal overdischarge detection/release: 2.500 / 2.800 V.
- Discharge overcurrent, short-circuit and charge overcurrent sense thresholds: -5.8 mV, -20.5 mV and +20 mV respectively. Current limits require subsequent resistor and FET selection.
- Zero-volt charging inhibited; power-down, power-saving and overheat detection unavailable for this suffix.

The user explicitly chose the lowest overcharge threshold among the stocked high-side variants, accepting reliance on the charger for normal 4.20 V regulation. This supersedes the earlier sourcing rejection below. A 4.590 V fault cutoff does not establish adequate overcharge protection for a conventional 4.20 V cell: a failed charger could hold the cell above its permitted voltage without reaching the protector threshold. Actual cell compatibility remains unverified. Keep the charger set to the selected cell's charging voltage; this IC choice does not authorize increasing it.

Evidence: S821AA Rev.1.3 pp.5-6, cached in `hardware/datasheets/S821AA.pdf`. The native circuit uses two CSD17318Q2 FETs and a 3 mOhm D1MPC0805 shunt, with final current rating subject to cell and load selection.

## Stocked TI candidate requiring a wiring change: BQ298217RUGR

DigiKey's public US product page reports 3,912 available, USD 0.76 at quantity 1 and USD 0.543 at quantity 10. Cut-tape order code: `296-BQ298217RUGRCT-ND`. This is a dated public-page observation, not a reservation or authenticated inventory query.

- Manufacturer: Texas Instruments; active; 8-X2QFN, 1.5 × 1.5 mm.
- Fixed overcharge threshold: 4.250 V, nominal 1.25 s delay.
- Fixed undervoltage threshold: 2.600 V, nominal 125 ms delay.
- Charge/discharge overcurrent thresholds: -36 mV / +60 mV; short-circuit threshold: +200 mV.
- Illustrative 30 milliohm shunt gives nominal 1.2 A charge, 2 A discharge, 6.67 A short-circuit detection. These are examples, not selected pack ratings; tolerances, cell limits, wiring and branch-loss cases remain to assess.
- Normal IC supply current: 4 microamps typical below 3.9 V and 5 microamps typical above 4.0 V under TI's specified test conditions. External leakage is additional.
- Zero-volt charging disabled. This suffix has internal overtemperature protection disabled; distributed cell-temperature charging control remains necessary.
- Requires external back-to-back N-channel MOSFETs, a shunt and support passives.

Evidence: TI BQ2980/BQ2982 datasheet SLUSCS3L, March 2025, page 3 variant table; pages 4–8 pins/electrical characteristics; page 18 reference circuit. Cached as `hardware/datasheets/BQ2980.pdf`, with hash in the manifest.

## Wiring consequence

The FETs switch the positive path, but the current shunt is in the negative path. TI's CS pin senses PACK- relative to the cell-side VSS. It is not a drop-in fit for our existing three-terminal J4 interface.

Our exported netlist currently connects all cell-negative terminals directly to system GND. A single central BQ298217 would require a separate `BAT_NEG_RAW` conductor connecting every cell negative, with only the central shunt connecting that conductor to system GND. That changes the interpod harness from six to seven conductors. Retaining any direct cell-negative-to-GND connection would bypass current sensing.

The return-data conductor and purely mechanical clasp can otherwise remain as designed. The recommendation is conditional on accepting this extra conductor. No such change has been made or treated as approved.

## Other candidates screened

- ABLIC S-821AAAI-I8T1U: positive-path switching and current sensing fit our original architecture; nominal 4.275 V overcharge threshold. Exact DigiKey availability could not be verified.
- Stocked S-821AAAA-I8T1U and S-821AAAB-I8T1U: 4.590 V and 4.620 V overcharge thresholds, respectively. Rejected for the assumed conventional 4.20 V cells.
- DigiKey-listed S-821BAAC-H8T7S and S-821BAAD-H8T7S: also 4.590 V / 4.620 V thresholds; rejected for the same reason.
- Nisshinbo NB7120/NB7123: high-side candidates, but the found DigiKey listings showed zero stock and 5,000-piece ordering quantities. Not prototype-stock solutions.
- BQ298000RUGR: stocked but 4.475 V overcharge threshold; do not substitute for BQ298217.

If six conductors are mandatory, alternatives are sourcing an appropriate true high-side-sensing protector elsewhere or putting local protection at each populated cell. Neither topology change is selected here.

## Broader ABLIC review following user correction

The user reports 75 stocked ABLIC 1S parts on DigiKey. The earlier search did not exhaustively inspect that filtered list; it must not be represented as ruling out every stocked ABLIC part. Public catalog access exposes some rows, but direct automated catalog retrieval was blocked by DigiKey's browser challenge. The filtered-list URL has been requested to reconcile the exact list.

Several stocked ABLIC parts have plausible conventional 4.20 V cell thresholds:

| Exact MPN | Overcharge / overdischarge thresholds | Native protection topology | Evidence |
| --- | --- | --- | --- |
| S-8240ADQ-M6T1U | 4.280 / 2.800 V | Low-side FETs, FET resistance sensing | S8240A Rev.3.3, p.4 variant table; DigiKey product 16187176 |
| S-82N1AAA-I6T1U7 | 4.280 / 2.900 V | Low-side FETs, FET resistance sensing | S82N1A Rev.1.2, p.3 variant table, p.24 Figure 14; DigiKey product 14664151 |
| S-82D1AAD-A8T2U7 | 4.280 / 3.000 V | Low-side protection with separate sense resistor | S82D1A variant table; DigiKey product 13183030 |

S-82N1AAA is an attractive low-power alternative: 600 nA typical / 990 nA maximum IC operating current at 25 C, SNT-6A package. Its public DigiKey product page reports 3,669 in stock and USD 1.54 each, while the more recently crawled catalog reports 3,653 and USD 1.85. Treat availability as supported but exact price/quantity as unconfirmed until ordering. Datasheet saved to `hardware/datasheets/S82N1A.pdf`; reference circuit rendered in `hardware/verification/S82N1A-application.png` and visually checked.

These parts cannot be inserted as one central protector while retaining direct connections between every cell negative and system GND: that would bypass their disconnect path. They could be used with a separate raw battery-negative bus, or locally at each populated cell before joining the shared rails. Local protection preserves the six-conductor harness, but changes the previously chosen single-protector architecture. Threshold/current/FET selection and parallel-branch behavior would still need checking against the selected cells.

ABLIC's [current 1-cell product-lineup table](https://www.ablic.com/en/semicon/products/power-management-ic/lithium-ion-battery-protection-ic/intro-1cell/) explicitly distinguishes ordinary FET-resistance/sense-resistor protectors from the S-821A/B high-side families. A 1-cell filter alone does not impose high-side switching and sensing. No topology change or final IC commitment is recorded by this review.

## Sources

### User-supplied S-821 export: all 18 rows reconciled

Read-only source: `C:/Users/mmsyl/Downloads/battery_management.csv`, received 2026-09-12. SHA256: `ab5aa471e1afcff4904a20d6f38fe28612f71e806f0ab0181eb43aefbeda045a`. The source contains 18 distinct MPNs: eleven S-8215A variants explicitly marked 3–5 cells, one S-8211CAA-I6T1U low-side 1-cell protector, and six S-821AA/BA high-side 1-cell protectors. This resolves the supplied 18-row list, not the previously mentioned 75-row 1S list.

| High-side MPN in supplied export | Stock in supplied export | Overcharge threshold |
| --- | ---: | ---: |
| S-821AAAC-H8T7S | 6000 | 4.590 V |
| S-821AAAB-I8T1U | 95 | 4.620 V |
| S-821AAAD-H8T7S | 75 | 4.620 V |
| S-821AAAA-I8T1U | 67 | 4.590 V |
| S-821BAAD-H8T7S | 90 | 4.620 V |
| S-821BAAC-H8T7S | 88 | 4.590 V |

Threshold evidence: cached S821AA Rev.1.3 pp.4–5 and manufacturer S821BA Rev.1.3 p.4. S-8211C low-side topology: manufacturer S8211C Rev.7.7_03 p.28, Figure 14, https://www.ablic.com/en/doc/material/old_product/S8211C_E_NRND.pdf. The suitable-threshold high-side candidate S-821AAAI-I8T1U is absent from this export. None of the supplied six high-side variants is selected as the primary overcharge protector for the assumed conventional 4.20 V cells.

- [DigiKey BQ298217RUGR](https://www.digikey.com/en/products/detail/texas-instruments/BQ298217RUGR/18111336)
- [TI BQ2980/BQ2982 datasheet](https://www.ti.com/lit/ds/symlink/bq2980.pdf)
- [ABLIC S-821AA datasheet](https://www.ablic.com/en/doc/datasheet/battery_protection/S821AA_E.pdf)
- [ABLIC S-821BA datasheet](https://www.ablic.com/en/doc/datasheet/battery_protection/S821BA_E.pdf)
- [DigiKey S-821AAAA-I8T1U](https://www.digikey.com/en/products/detail/ablic-inc/S-821AAAA-I8T1U/25649782)
