# Ring pods and switched power

Two-PCBA architecture, 2026-09-13. One wrist has eight M2003FC1AE + DRV2625 + LRA pods: one local pod on the main PCBA and seven copies of one universal satellite PCBA. See [project structure and reference mapping](pcba-projects.md). The music robot project was inspected read-only. Initial bracelet firmware now builds against its support and LDROM sources, but has not been flashed or bench-tested.

## Interconnect

ESP32 GPIO19 TX passes through main R42 to the local pod. Every MCU receives on PF1 and forwards on PF0. Each satellite R2 supplies its local TX_OUT. On the last satellite, JP1 connects TX_OUT to the upstream serial return; the other six satellites pass their downstream return upstream. The final return reaches main ESP32 GPIO2 RX. These remain separate point-to-point UART segments, not a multidrop data net. The loader sees the same logical ring.

Satellites have IN and OUT wiring interfaces; main has OUT only. Each harness bank now has five pads numbered consecutively:

| Pin | Connection |
| --- | --- |
| 1 | +3V3_POD, switched supply |
| 2 | GND |
| 3 | DATA: RX on IN, TX on OUT |
| 4 | VBAT, unswitched protected battery-output bus |
| 5 | RING_RETURN, passive serial return from end pod to ESP RX |

Each wired gap now needs **five conductors**, including the cell bus and dedicated return. Physically the boards form an open chain with seven wired gaps and one purely mechanical clasp between the end pod and main pod. Opening the clasp does not disconnect power or data. Connector symbols now use five-pad footprints at 2 mm pitch, with 1.4 x 1.6 mm lands and no paste; flexible wire and housing strain relief complete the interconnect.

Connect main J101 to satellite 1 J1, then each satellite J2 to the next J1, pin-for-pin. Main J100 is removed. The last satellite J2 is not cabled.

**JP1 pads:** 1 = downstream return (J2.5), 2 = upstream return (J1.5), 3 = local TX_OUT (R2.2/J2.3). Leave factory 1-2 on satellites 1-6. On satellite 7, cut 1-2 and solder 2-3. Never bridge all three. This replaces the archived end-only R53 resistor; there is one satellite PCB and assembly configuration. The centre pad selects the upstream return source while isolating the unselected side.

The final return is one longer UART connection through seven harness spans; the last satellite R2 remains its source series resistor. The revised harness needs edge-quality and voltage-drop checks when built, but it does not add software forwarding stages to the return. No power conductor crosses the clasp: size the chain wiring for the resulting current paths from the distributed cells and main regulated supply. Final pad dimensions, wire gauges and strain relief remain open.

Main J200/F100 and satellite J4/F1 provide one protected battery and positive-branch fuse per pod. Connect factory PACK+ through the fuse to VBAT and factory PACK- to GND. Retain each PCM and leave raw cell terminals isolated from the board. This battery bus stays live when pod power is off. The working battery envelope is 3 x 12 x 32 mm, with 90 mAh per pod.

The central protection stage is removed. VBAT directly feeds BQ25186 BAT; protection is inside each battery assembly. Main F100 and each satellite F1 are Littelfuse 0467.250NR, 250 mA fast-blow 0603 secondary branch fuses. Factory PCMs remain the primary cell protection; fuse pulse/fault coordination needs bench validation. The harness now uses five wires; UART return topology is unchanged. See [battery protection](pack-protection-implementation.md).

## Pod pins and loader reuse

| Function | M2003 port | TSSOP20 pin |
| --- | --- | --- |
| Ring receive / ICE clock | PF1 | 18 |
| Ring transmit / ICE data | PF0 | 8 |
| Local ICE reset | PE15 / nRESET | 4 |
| Local DRV2625 SDA | PB4 | 5 |
| Local DRV2625 SCL | PB5 | 6 |
| Unused former driver reset GPIO | PB13 | 13 (NC) |
| Optional cell thermistor ADC | PB2 | 2 |
| Switched supply / ground | VDD / VSS | 9 / 7 |

The pin map and support circuit were checked against [Nuvoton's M2003 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_M2003_Series_EN_Rev1.00.pdf), TSSOP20 diagram/table on printed page 18 and application circuits on pages 96–97. Main U18 and satellite U1 use the stock TSSOP-20 4.4 x 6.5 mm, 0.65 mm pitch footprint. Each MCU has 100 nF and 10 uF decoupling. Each ICE pin has a 100k pull-up to +3V3_POD.

The inspected robot loader uses PF0/PF1 at 250 kbaud, 8N1, with the 24 MHz internal oscillator. It drives PB1 high and PB7/8/9/11/12/13 low before entering the loader. Those outputs are now unconnected, including PB13. Each DRV2625 B2 NRST ties directly to C2 VDD; R104/R114/R124/R134/R144/R154/R164/R174 are removed. This avoids routing the centre ball out of the WLCSP. Local I2C pull-ups and REG capacitors remain separate for every pod.

Stop haptic playback before entering the loader. Resetting only a pod MCU no longer resets its driver. An unresponsive driver is recovered by the ESP32 cycling U26 and discharging +3V3_POD; this resets all eight MCUs and drivers together. On restart, wait for the supply settling interval, initialize the drivers, and restart ring discovery. TI documents GO=0 as stop/standby, not a register reset; there is no documented software-reset command. Power-off discharge timing remains a bench qualification item.

Source reference: `C:/Users/mmsyl/Documents/bl4818-servo-M23_2/ldrom/platform.c`, `ldrom/uart.c`, `ldrom/bl_internal.h`, `ldrom/main.c`, `include/firmware_image.h`, and `scripts/ring_bootload.py`. Hashes of the inspected files are in `hardware/verification/robot-loader-reference.json`. These are provenance references, not copied or modified firmware.

Retain the existing enumeration/update protocol, 32-byte write chunks, CRC verification and manifest commit. Preserve application space below 0x7A00, manifest at 0x7A00, persistence from 0x7C00, 4 KiB LDROM at 0x00100000 and the 16-byte boot mailbox at 0x20000FF0. A valid application has a 1000 ms loader interception window after reset. Pin compatibility supports reuse; an unchanged loader binary and a bracelet application still need build and bench verification. Never flash the robot motor application as a bracelet application.

For initial flashing or ICE debug, remove **both** the RX 0-ohm link and TX 33-ohm link on the target pod. Satellite J3 exposes VTref, ground, ICE_DAT, ICE_CLK and local reset on the MCU side of those links. Main J1 is TC2030: pin 1 VTref, 2 ICE_DAT, 3 local reset, 4 ICE_CLK, 5 GND and 6 unused/SWO NC. Restore both links for ring operation. Debug reset affects only the target MCU. VTref is a sense connection: supply the pod normally, and do not power an unpowered ring through a probe or UART adapter.

## Main-board power and reset

U26 TPS22918 switches the regulated 3V3 rail to +3V3_POD, supplying all eight MCUs and drivers. ESP32, USB and charger control remain on 3V3. GPIO3 asserts ON; R45 holds it off when the ESP32 is not driving it. C42 is now 4.7 nF and sets a controlled ramp, and R46 connects output discharge. The part is an integrated high-side load switch with a 2 A continuous-current ceiling; the converter, wiring and simultaneous actuator budget still need sizing. It provides neither current limiting nor reverse blocking. See [TI TPS22918 datasheet](https://www.ti.com/lit/ds/symlink/tps22918.pdf), pin table and sections 8.3.2–8.3.3.

GPIO18 is now spare/no-connect. Q5, R7 and R44 are removed along with the former shared R6/C40 reset network. Each MCU nRESET pin connects only to its local ICE reset pad. The M2003 internal reset pull-up biases this short local net; its power-on reset handles rail startup. Nuvoton documents the internal pull-up in Table 8.3-8 (page 110) and POR in section 6.2.2. The same datasheet recommends an external 10k/10u network for reset stability; the prototype now uses the internal pull-up without that external RC. No harness reset conductor remains.

There are no UART isolation buffers. Firmware handles the powered/unpowered boundary:

1. At ESP32 startup, keep POD_POWER_ON low. Configure ring TX as GPIO output low and RX as input with pull-up disabled. If restarting while pods were powered, allow a full discharge before enabling them again.
2. Before power-on, prepare the host UART and loader state while keeping TX low. Enable POD_POWER_ON and wait for the supply to settle. Then attach the UART, establish idle-high TX, and intercept/enumerate within the loader window. Each MCU starts from its own POR; there is no shared reset release edge or external 100 ms RC delay.
3. Before shutdown, finish or abort activity and disable charging if it depends on pod temperature reports. Detach the UART, drive TX low, keep RX as input with no pull-up, then turn POD_POWER_ON off.
4. Keep these pin states throughout the off interval. Allow U26/R46 to discharge the entire distributed rail sufficiently for every MCU and driver to reset before the next power-on. Do not drive RX low while the last pod may still be transmitting. Apply this policy to sleep, wake, UART reinstall and ESP32 restart paths.

Startup/settling delays and discharge time remain bench checks. The circuit has no +3V3_POD power-good measurement. Validate the rail at the farthest pod, reset recovery and loader interception with all eight loads connected. The loader protocol is unchanged; the host reset sequence changes to power cycling.

## Distributed temperature provision

Every pod has a PB2 ADC divider provision: a 10k bias resistor, 10 nF filter and optional external NTC connection. Populate sensors at cell locations; the cell supplier's limits and thermistor curve remain to be selected. This is the temperature-sensing arrangement for all eight pods. The separate charger thermistor connector J3 is removed; charger TS/MR instead has fixed 10k R62 to GND, in parallel with SW3. The application must distinguish absent/unrequired sensors from faults and reject stale readings.

Charging that relies on pod temperature reports requires the pod rail and ring application running, with haptic outputs disabled. Disable charging before cutting the rail or entering the loader, and restore it only after fresh required sensor readings and charger checks. Temperature firmware and physical PCM cutoff/recovery validation remain open.

## Verification

The main project exports five sheets and the satellite one. Both have zero schematic/PCB parity issues. Main has one documented reset-input ERC item; satellite ERC is clean. Pin-set comparison preserves the prior verified power, USB, MCU and haptic circuits, with the intentional return selector, main service-bank removal and reset changes. Satellite routing has zero DRC violations and opens; main routing remains pending. Current reports are under `hardware/verification/project-split/`. Electrical connectivity checks do not qualify the physical harness.

## Unused driver trigger pins

Main U3 and satellite U2 pin A1 (TRIG/INTZ) now has a no-connect flag, as requested. The former ground stub is removed. This pin has an internal pull-down; firmware uses I2C GO/status control and must not select external-trigger operation. TI DRV2625 Rev. C Table 4-1 recommends grounding the unused pin, so leaving it externally unconnected is an explicit prototype choice, not a claim of following that recommendation.

## Added pod bulk and ramp budget

Main C103 and each satellite C3 add 22 uF, 10 V X5R in 0805 from +3V3_POD to GND, near each driver supply/power entry. Keep the existing 10 uF, 1 uF and 100 nF local capacitors. Final MPN selection must check effective capacitance at 3.3 V; the 22 uF value is nominal, not guaranteed under DC bias.

The exported netlist totals 266.6 uF nominal on +3V3_POD. With C42=4.7 nF, TPS22918 Equation 3 gives about 8.65 ms typical 10-90% rise at 3.308 V and 81.6 mA capacitor-only ramp current. This excludes dynamic load, tolerance and DC-bias effects. Wait for supply settling before sending loader traffic. The added capacitance also lengthens output discharge through R46 and U26 QOD: firmware must not reuse an unverified old shutdown delay. Actual startup, discharge and rail excursions remain bench checks. Calculations are in `hardware/verification/pack-protection-checks.json`.
