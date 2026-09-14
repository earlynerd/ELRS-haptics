# Ring pods and switched power

Implemented schematic draft, 2026-09-12. One wrist has eight M2003FC1AE + DRV2625 + LRA pods. Pod 0 shares a housing with the ESP32 and main power circuitry; schematic sheet boundaries do not prescribe separate PCBs. The music robot project was inspected read-only. No bracelet firmware has been written or flashed in this revision.

## Interconnect

ESP32 GPIO19 TX passes through R42 (33 ohm) to pod 0. Every pod receives on PF1 and forwards on PF0. Pod 7 TX passes through its existing R171 (33 ohm), then R53 (0 ohm end bridge) onto RING_RETURN, which travels back through pin 6 of every link to ESP32 GPIO2 RX. Nets RING_D0 through RING_D8 are nine distinct UART segments; RING_RETURN is the far side of the final zero-ohm bridge. These are UART links, not a shared multidrop data net. Enumeration and the loader still see the same logical ring.

Every pod has IN and OUT wiring interfaces with the same pin order:

| Pin | Connection |
| --- | --- |
| 1 | POD_3V3, switched supply |
| 2 | GND |
| 3 | DATA: RX on IN, TX on OUT |
| 4 | RING_nRESET, shared active low MCU reset |
| 5 | VBAT_RAW, unswitched parallel-cell positive bus |
| 6 | RING_RETURN, passive serial return from end pod to ESP RX |

Each wired gap now needs **six conductors**, including the cell bus and dedicated return. Physically the boards form an open chain with seven wired gaps and one purely mechanical clasp between the end pod and main pod. Opening the clasp does not disconnect power or data. Connector symbols describe six-pad wiring interfaces with unassigned footprints; soldered flexible wire remains the proposed prototype implementation.

Connect each OUT group to the next IN group pin-for-pin: J101 to J104, J105 to J108, J109 to J112, J113 to J116, J117 to J120, J121 to J124, and J125 to J128. Pod 0 shares the main board, so its RX and return reach the ESP locally. J100 and J129 are not externally cabled across the clasp. Pin 6 connects straight through each intermediate PCB without attaching to its MCU. **Only pod 7 has the TX-to-return bridge R53**; fitting equivalent bridges on other pods would short their TX drivers together. R53 is a local board link, not a plug or wire crossing the clasp.

The final return is one longer UART connection through seven harness spans; R171 remains its source series resistor. The revised harness needs edge-quality and voltage-drop checks when built, but it does not add software forwarding stages to the return. No power conductor crosses the clasp: size the chain wiring for the resulting current paths from the distributed cells and main regulated supply. Final pad dimensions, wire gauges and strain relief remain open.

Each pod has an optional cell connection J200–J207 and a positive-branch fuse F100–F107. Populate these only at cell locations, with the fuse close to the cell. VBAT_RAW joins the fused cell positives; negative terminals share GND. This raw bus stays live when the pod power switch is off.

The `protection.kicad_sch` child sheet replaces J4 with U27 S-821AAAC-H8T7S, R54 and Q6/Q7. This high-side bidirectional disconnect retains one common ground conductor. VBAT_RAW reaches BAT_PROTECTED only through the shunt and two FETs. J3 continues to expose protected terminals and the charger NTC. Prototype trip values and the accepted voltage limitation are documented in [pack protection](pack-protection-implementation.md); cell-branch fuse ratings remain open. A conventional low-side protector cannot be substituted while tying raw and protected negatives to the same ground.

## Pod pins and loader reuse

| Function | M2003 port | TSSOP20 pin |
| --- | --- | --- |
| Ring receive / ICE clock | PF1 | 18 |
| Ring transmit / ICE data | PF0 | 8 |
| Shared reset | PE15 / nRESET | 4 |
| Local DRV2625 SDA | PB4 | 5 |
| Local DRV2625 SCL | PB5 | 6 |
| Local DRV2625 reset | PB13 | 13 |
| Optional cell thermistor ADC | PB2 | 2 |
| Switched supply / ground | VDD / VSS | 9 / 7 |

The pin map and support circuit were checked against [Nuvoton's M2003 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_M2003_Series_EN_Rev1.00.pdf), TSSOP20 diagram/table on printed page 18 and application circuits on pages 96–97. U18–U25 use the stock TSSOP-20 4.4 x 6.5 mm, 0.65 mm pitch footprint. Each MCU has 100 nF and 10 uF decoupling. Each ICE pin has a 100k pull-up to POD_3V3.

The inspected robot loader uses PF0/PF1 at 250 kbaud, 8N1, with the 24 MHz internal oscillator. It drives PB1 high and PB7/8/9/11/12/13 low before entering the loader. Here PB13 holds the DRV2625 in reset, reinforced by a 10k pull-down; the other forced outputs are unconnected. The pod application must release and configure its driver. Local I2C pull-ups and REG capacitors are separate for every pod.

Source reference: `C:/Users/mmsyl/Documents/bl4818-servo-M23_2/ldrom/platform.c`, `ldrom/uart.c`, `ldrom/bl_internal.h`, `ldrom/main.c`, `include/firmware_image.h`, and `scripts/ring_bootload.py`. Hashes of the inspected files are in `hardware/verification/robot-loader-reference.json`. These are provenance references, not copied or modified firmware.

Retain the existing enumeration/update protocol, 32-byte write chunks, CRC verification and manifest commit. Preserve application space below 0x7A00, manifest at 0x7A00, persistence from 0x7C00, 4 KiB LDROM at 0x00100000 and the 16-byte boot mailbox at 0x20000FF0. A valid application has a 1000 ms loader interception window after reset. Pin compatibility supports reuse; an unchanged loader binary and a bracelet application still need build and bench verification. Never flash the robot motor application as a bracelet application.

For initial flashing or ICE debug, remove **both** the RX 0-ohm link and TX 33-ohm link on the target pod. Its five-pin debug interface exposes VTref, ground, ICE_DAT, ICE_CLK and shared reset on the MCU side of those links. Restore both links for ring operation. Debug reset affects every connected pod. VTref is a sense connection: supply the pod normally, and do not power an unpowered ring through a probe or UART adapter.

## Main-board power and reset

U26 TPS22918 switches the regulated 3V3 rail to POD_3V3, supplying all eight MCUs and drivers. ESP32, USB and charger control remain on 3V3. GPIO3 asserts ON; R45 holds it off when the ESP32 is not driving it. C42 sets a controlled ramp, and R46 connects output discharge. The part is an integrated high-side load switch with a 2 A continuous-current ceiling; the converter, wiring and simultaneous actuator budget still need sizing. It provides neither current limiting nor reverse blocking. See [TI TPS22918 datasheet](https://www.ti.com/lit/ds/symlink/tps22918.pdf), pin table and sections 8.3.2–8.3.3.

GPIO18 drives Q5 to assert the shared MCU reset. R6 pulls reset up to **POD_3V3**, with one common 10 uF capacitor; R44 limits Q5's capacitor discharge pulse. This is distinct from each driver's PB13 reset. The reset network has a nominal 100 ms RC time constant; firmware must account for threshold and tolerance before loader traffic.

There are no UART isolation buffers. Firmware handles the powered/unpowered boundary:

1. At ESP32 startup, keep POD_POWER_ON low. Configure ring TX as GPIO output low, RX as input with pull-up disabled, and assert pod reset.
2. Before every power-on, assert pod reset through Q5 (RING_RESET_ASSERT high). Enable POD_POWER_ON and wait for the supply to settle. Attach the UART only after power is valid, establish idle-high TX, then release reset. Allow the reset RC rise and intercept/enumerate the loader within its boot window.
3. Before shutdown, finish or abort activity cleanly and disable charging if it depends on pod temperature reports. Assert pod reset, detach the UART, drive TX low, and keep RX an input with no pull-up. Then turn POD_POWER_ON off. Keep reset asserted while the rail and reset capacitor discharge; after discharge, drive RING_RESET_ASSERT low to release Q5 and eliminate current through its 100k gate pulldown R7.
4. Throughout the steady off interval, keep POD_POWER_ON low, ring TX low, ring RX an input without pull-up, and RING_RESET_ASSERT low. The shared active-low reset net is referenced through R6 to the discharged POD_3V3 rail; it is not driven high by releasing Q5. Do not drive RX low while the last pod may still be transmitting. Apply the same pin policy to sleep, wake, UART reinstall and ESP32 restart paths.

Startup/settling delays and discharge time are not bench-qualified. The circuit provides no POD_3V3 power-good measurement. Begin with conservative delays and verify the actual rail/reset waveforms, including ESP32-only reset while pods are powered.

## Distributed temperature provision

Every pod has a PB2 ADC divider provision: a 10k bias resistor, 10 nF filter and optional external NTC connection. Populate sensors at cell locations; the cell supplier's limits and thermistor curve remain to be selected. This is separate from the charger's PACK_TS thermistor. The application must distinguish absent/unrequired sensors from faults and reject stale readings.

Charging that relies on pod temperature reports requires the pod rail and ring application running, with haptic outputs disabled. Disable charging before cutting the rail or entering the loader, and restore it only after fresh required sensor readings and charger checks. Temperature firmware and distributed pack protection remain open.

## Verification

KiCad exports all 14 sheets. The exported netlist passes checks for nine ring segments, the final return bridge, six-pad IN/OUT interfaces, zero intermediate MCU connections on the return, eight isolated I2C/reset groups, actuator outputs, shared reset, debug-link isolation, switched supplies and unchanged USB/power connectivity. ERC reports zero errors and zero warnings, with explicit no-connect flags at each unused TRIG/INTZ pin; no exclusions. See `hardware/verification/ring-checks.json` and `erc.rpt`. Pre-migration native files are retained in `hardware/backups/before-serial-return/`. The PCB remains empty; the netlist verifies the intended connectivity, not the physical harness.

## Unused driver trigger pins

U3 through U10 pin A1 (TRIG/INTZ) now has a no-connect flag, as requested. The former ground stub is removed. This pin has an internal pull-down; firmware uses I2C GO/status control and must not select external-trigger operation. TI DRV2625 Rev. C Table 4-1 recommends grounding the unused pin, so leaving it externally unconnected is an explicit prototype choice, not a claim of following that recommendation.
