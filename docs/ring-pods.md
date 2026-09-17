# Ring pods and switched power

Stacked architecture, 2026-09-14: eight identical universal M2003FC1AE/DRV2625/LRA pod PCBAs plus one controller daughterboard. The daughterboard sits above pod 0, which has no battery or external NTC. Pods 1-7 each have a protected cell and NTC. See [project structure](pcba-projects.md). The existing firmware build and loader have not been bench-qualified on this hardware; seven-sensor charge supervision remains firmware work.

## Interconnect

ESP32 GPIO19 TX passes through controller R42 and J101 pin 3 to pod 0 J1 pin 3. Each MCU receives on PF1 and forwards on PF0 through its local R2. Pod 7 selects its TX onto the passive upstream return, which reaches ESP GPIO2 RX through J101 pin 5. The eight point-to-point forwarding stages and logical loader ring are unchanged.

| Pin | Function |
| --- | --- |
| 1 | +3V3_POD, switched electronics supply |
| 2 | GND |
| 3 | DATA: RX at pod IN, TX at pod OUT |
| 4 | VBAT, unswitched protected battery-output bus |
| 5 | Serial return from end pod |

Connect daughterboard J101 to pod 0 J1 pin-for-pin, then each pod J2 to the next J1. Pod 7 J2 is uncabled. There are seven five-wire inter-pod gaps plus the local five-contact stack connection. The eighth mechanical gap stays unwired. Existing pad footprints are retained; the new stacking contact arrangement and enclosure are pending. The v0.11 enclosure describes the superseded larger integrated main board.

JP1 pad 1 is downstream return, pad 2 upstream return, and pad 3 local TX_OUT. Pods 0-6 keep factory 1-2 NORMAL. Pod 7 cuts 1-2 and bridges 2-3 END. Never bridge all three. All eight pod PCBAs have identical components.

Every universal board includes J4/F1 for the protected battery branch and J5 for the optional external NTC. Leave J4 and J5 unwired on pod 0. On pods 1-7, connect factory PACK+ through F1 to VBAT and PACK- to GND, retaining the factory PCM. VBAT remains live when electronics power is off. The controller receives the combined bus through J101, with no local battery connector or fuse branch.

The seven-90 mAh-cell example gives 630 mAh nominal. The proposed 301730/160 mAh alternative would give 1,120 mAh; exact protected dimensions, current ratings and fit are not yet established. F1 remains the existing 250 mA secondary branch-fuse provision; a different battery requires checking its coordination rather than inferring compatibility from capacity.

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

The pin map and support circuit were checked against [Nuvoton's M2003 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_M2003_Series_EN_Rev1.00.pdf), TSSOP20 diagram/table on printed page 18 and application circuits on pages 96–97. Universal pod U1 uses the stock TSSOP-20 4.4 x 6.5 mm, 0.65 mm pitch footprint. Each MCU has 100 nF and 10 uF decoupling. Each ICE pin has a 100k pull-up to +3V3_POD.

The inspected robot loader uses PF0/PF1 at 250 kbaud, 8N1, with the 24 MHz internal oscillator. It drives PB1 high and PB7/8/9/11/12/13 low before entering the loader. Those outputs are now unconnected, including PB13. Each DRV2625 B2 NRST ties directly to C2 VDD. This avoids routing the centre ball out of the WLCSP. Local I2C pull-ups and REG capacitors remain separate for every pod.

Stop haptic playback before entering the loader. Resetting only a pod MCU no longer resets its driver. An unresponsive driver is recovered by the ESP32 cycling U26 and discharging +3V3_POD; this resets all eight MCUs and drivers together. On restart, wait for the supply settling interval, initialize the drivers, and restart ring discovery. TI documents GO=0 as stop/standby, not a register reset; there is no documented software-reset command. Power-off discharge timing remains a bench qualification item.

Source reference: `C:/Users/mmsyl/Documents/bl4818-servo-M23_2/ldrom/platform.c`, `ldrom/uart.c`, `ldrom/bl_internal.h`, `ldrom/main.c`, `include/firmware_image.h`, and `scripts/ring_bootload.py`. Hashes of the inspected files are in `hardware/verification/robot-loader-reference.json`. These are provenance references, not copied or modified firmware.

Retain the existing enumeration/update protocol, 32-byte write chunks, CRC verification and manifest commit. Preserve application space below 0x7A00, manifest at 0x7A00, persistence from 0x7C00, 4 KiB LDROM at 0x00100000 and the 16-byte boot mailbox at 0x20000FF0. A valid application has a 1000 ms loader interception window after reset. Pin compatibility supports reuse; an unchanged loader binary and a bracelet application still need build and bench verification. Never flash the robot motor application as a bracelet application.

For initial flashing or ICE debug, remove **both** the RX 0-ohm link and TX 33-ohm link on the target pod. Satellite J3 exposes VTref, ground, ICE_DAT, ICE_CLK and local reset on the MCU side of those links. There is no separate M2003 ICE connector on the controller daughterboard; pod 0 uses the universal board J3 like all other pods. Restore both links for ring operation. Debug reset affects only the target MCU. VTref is a sense connection: supply the pod normally, and do not power an unpowered ring through a probe or UART adapter.

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

Every universal pod board has a PB2 ADC divider provision: a 10k bias resistor, 10 nF filter and optional external NTC connection. Populate sensors at cell locations; the cell supplier's limits and thermistor curve remain to be selected. Populate external cell sensors on pods 1-7 only; pod 0 has no cell and its unwired NTC input is not a required sensor. The charger has no independent cell thermistor; charger TS/MR instead has fixed 10k R62 to GND, in parallel with SW3. The application must distinguish absent/unrequired sensors from faults and reject stale readings.

Charging that relies on pod temperature reports requires the pod rail and ring application running, with haptic outputs disabled. Disable charging before cutting the rail or entering the loader, and restore it only after fresh required sensor readings and charger checks. Temperature firmware and physical PCM cutoff/recovery validation remain open.

## Verification

Both current projects have zero ERC and schematic/PCB parity issues. The universal pod remains fully routed with zero DRC violations and opens. The controller-only PCB retains historical outline/positions and has 146 opens plus three existing ESP footprint/silkscreen warnings. The schematic migration preserves all retained controller pin groups and the entire universal pod circuit and routing. See `hardware/verification/stacked-controller/checks.json`. These are design-file checks, not stack fit or hardware qualification.
