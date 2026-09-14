> **Adopted packaging baseline, revision 0.5:** eight protected 90 mAh batteries, one per pod, using the YDL301230 3 x 12 x 32 mm assembly as the example. Keep factory PCMs intact; remove the central protector. Study D allocates a battery in every lid. The earlier study-C fit and alternative sourcing discussion below are historical comparisons, not the current count/protection decision.

# 301230 cell packaging candidate

2026-09-12: the user proposes one approximately 90 mAh cell in each of eight pods, with YDL301230 as an example, and is open to other bare-cell part numbers. The exact purchase remains open, but protected assemblies of this size are the adopted baseline; the numeric size code does not identify a unique electrical specification.

## Exact YDL example and bare-cell sourcing

[YDL's product](https://ydlbattery.com/products/ydl-301230-90mah-3-7v-lithium-polymer-battery-3x12x32mm-with-ph2-0-connector) is a protected 3 x 12 x 32 mm finished assembly, with leads and a PH2.0 connector outside that body envelope. Its [manufacturer datasheet](https://ydlbattery.com/cdn/shop/files/YDL-301230-90mAh-specification.pdf?v=17344537468879431347), cached at `hardware/datasheets/YDL301230.pdf`, specifies 90 mAh rated capacity, 18 mA standard charge, 45 mA maximum charge, and 45 mA maximum continuous discharge. The bare-cell drawing specifies 12 x 30 mm maximum body dimensions, initially 2.7 mm maximum thickness and 3.0 mm after 300 cycles; tabs need additional accommodation.

Eight cells in parallel therefore provide **720 mAh and 360 mA maximum continuous discharge in aggregate**, assuming equal sharing. At 3.7 V this is 1.332 W battery power, approximately 1.20 W after an illustrative 90% conversion efficiency. This is a plausible candidate, not a rejection on current capability: actual haptic/radio load remains to be established. Standard aggregate charge is 144 mA; maximum aggregate charge is 360 mA under the same sharing assumption. Some datasheet test/PCM values conflict with other sections; they do not establish a higher cell discharge rating.

Sources checked 2026-09-12:

| Source and model | Catalog cell body, T x W x L | Capacity | Purchase route / qualification remaining |
| --- | --- | --- | --- |
| [YDL301230, factory direct](https://ydlbattery.com/pages/custom-3-7v-lipo-battery) | Bare body up to 3 x 12 x 30 mm after cycling | 90 mAh | Preferred first inquiry. YDL explicitly offers bare cells for OEM integration and stock-model samples from five pieces. Confirm whether a small bare-cell order qualifies; custom configurations can have a 500-piece minimum. Request attached leads or solderable tabs, no PCM and no connector. |
| [PowerStream GM301030, without -PCB suffix](https://www.powerstream.com/li-pol.htm) | 3 x 10 x 30 mm nominal | Catalog 62 mAh; linked datasheet rated 60 mAh | Catalog offers sample ordering at $10.80 each. Linked protected-assembly datasheet specifies 1C maximum discharge; confirm supplied bare-cell drawing and rating. Lower capacity than YDL. |
| [PowerStream PGEB-A331030, without -PCB suffix](https://www.powerstream.com/li-pol.htm) | 3.3 x 10 x 30 mm nominal | 70 mAh | Catalog offers sample ordering at $4.25 each. Slightly thicker; exact current specification still needed. |
| [PowerStream GM251534 / GM261534, without -PCB suffix](https://www.powerstream.com/li-pol.htm) | 2.5 / 2.6 x 15 x 34 mm nominal | 100 mAh | Catalog offers samples at $10 each. Longer pod required. Linked protected-assembly datasheet specifies 2C maximum discharge but larger finished dimensions; confirm exact bare-cell drawing before layout. |
| [Akyga LP301230 / Ropla AKY0836](https://elektronik.ropla.eu/es/magazyn/magazyn/?ic=AKY0836) | 3 x 12 x 30 mm | 60 mAh | Explicitly unprotected, electrode tabs, 1C maximum discharge. Product page showed zero stock; not an immediate prototype purchase recommendation. |

PowerStream explicitly makes protection optional and uses the -PCB suffix for protected variants. Its catalog says an Add to Cart entry indicates sample stock; this was checked in the retrieved HTML, not through a completed order. Its dimensional tolerances and termination details still need to be included in any revised lid allocation. No supplier has been contacted and no order placed.

## Fit against study C

- The reserved regular-pod envelope is 16 x 28 x 3 mm (width x length x thickness), excluding 0.2 mm lid adhesive. A nominal 12 x 30 x 3 mm cell is 4 mm narrower and 2 mm longer; it does not fit the existing envelope unchanged.
- The regular shell is 20 x 34 x 10 mm, with a 17 x 31 mm PCB envelope. The proposed cell length is plausible if the lid allocation is revised, but end-wall, tab/lead exit, tolerance and closure clearances have not been resolved. The existing 3 mm thickness allocation leaves no additional thickness allowance for a nominal 3 mm cell.
- Keep the accepted mounting method: bond the cell to the inner lid surface, with no separate cell compartment. Leave the LRA mounted to the inner housing and independently clear of the pouch.
- The 24 x 52 mm main pod currently has no cell allocation. An eighth cell requires a new lid allocation clear of the ESP32 antenna, USB receptacle, button and RGB window. Do not assume a cell can cover the antenna because it is on a different Z plane.

No dimensional drawing or PCB outline has been changed by this assessment.

## Capacity and energy per wrist

Assume 90 mAh per cell at 3.7 V nominal, all parallel:

| Populated cells | Capacity | Nominal energy |
| --- | ---: | ---: |
| Seven regular pods | 630 mAh | 2.331 Wh |
| All eight pods | 720 mAh | 2.664 Wh |

The main-pod cell adds 14.3% capacity over seven cells. For eight cells, using a purely illustrative 85% factor for conversion and usable energy gives 2.264 Wh at the electronics: approximately 4.5 hours at 0.5 W average or 2.3 hours at 1 W. These are energy-only scenarios, not measured runtime predictions; actual radio and haptic duty cycles are unknown. A continuous 2 W electronics load exceeds the YDL eight-cell continuous-current rating, so the previous generic 2 W scenario does not apply to this candidate.

Use the YDL-specific 0.5C aggregate ratings above for this candidate, rather than a hypothetical 1C rating. The retired central prototype protector's 1.93 A nominal discharge trip corresponds to roughly 241 mA per cell with eight equally sharing cells (2.68C), so it is not a continuous-current rating for this pack. Final shunt and branch-fuse choices follow actual ratings, current sharing and pulse/load measurements. Normal charge-current settings likewise remain open.

## Source distinction

The proposed 90 mAh rating and nominal dimensions come from the user. Manufacturer listings demonstrate that the same size code has different implementations: [LithoTop](https://lithotop.com/wearable-devices/animal-tracker-battery-solutions) lists a 90 mAh 3 x 12 x 30 mm model, while [LP Power's 301230 datasheet](https://www.fpbattery.com/wp-content/uploads/2023/10/301230-3.7V-75mAh-Specification.pdf) describes a 75 mAh assembly measuring 32 x 12 x 3 mm including its protection arrangement. Neither is assumed to be the user's exact cell.
