# USB-C and power implementation

Current native sources: `hardware/main/usb.kicad_sch`, `power.kicad_sch` and `main.kicad_pcb`. Updated 2026-09-13 to a passive-CC, 5 V sink. This supersedes the earlier CC-controller and selectable external current-limit circuit.

## Data and CC connections

J2 is the USB4105-GF-A receptacle. A6/B6 join D+; A7/B7 join D-. U14 TPD2EUSB30 protects the data lines. R24/R25 remain 22-ohm series resistors; C29/C30 remain DNP tuning provisions. GPIO12/module pin 17 is D-, GPIO13/module pin 18 is D+. Native Serial/JTAG provides flashing, debug and console access. Paired USB 2.0 contacts support either plug orientation. Main UART service bank J1 is removed with no replacement UART test points. U1 RXD0/TXD0 are NC; SW1 reset and SW2 boot remain for ROM-download recovery through USB.

R60 connects CC1 to GND through 5.1k 1%; R61 independently connects CC2 to GND through 5.1k 1%. Both are 0402. U15 remains the CC ESD array; CC1 and CC2 are separate nets. There is no CC current-advertisement detection or USB PD negotiation.

Removed: U13 TUSB320, U16 TPS2553, U17 TS5A3159, Q2/Q3, R26-R33 and C31/C33. No external input-limit selector remains.

## Power path

All four J2 VBUS contacts connect to `USB_VBUS`, directly supplying BQ25186 U11 IN. C32 remains the 1uF connector bypass and C34 the 1uF charger IN bypass. Q4/R34/R35/R36 are removed. Input-power availability is read from BQ25186 VIN_PGOOD_STAT over the existing I2C interface; there is no discrete VBUS detector.

BQ25186 provides programmable input-current limiting and supplies SYS from USB or BAT. Its reset input-current setting is 500 mA; the separate low-current startup clamp is removed. Firmware sets input and charging limits separately. This prototype accepts source-compatibility limitations rather than guaranteeing pre-enumeration current behavior on every host. Two CC pull-downs alone do not measure the source's advertised current capability.

U12 TPS63802 supplies 3V3. Keep BQ25186 SYS set to 4.5 V when externally powered; do not select 5.5 V/pass-through with this regulator. C35/C36 and Q1/R38/R39 charge-enable gating are retained. SW3 remains the charger wake/ship button, now in parallel with fixed 10k R62; the separate J3 thermistor connector is removed. Charging defaults disabled through /CE until firmware allows it. The protected battery bus and temperature policy remain as described in [power architecture](power-architecture.md) and [ring pods](ring-pods.md).

## GPIOs

| GPIO | Module pin | Function |
| --- | --- | --- |
| 0 | 12 | Spare, NC; former CC interrupt |
| 1 | 13 | Spare, NC; former VBUS detector |
| 12 / 13 | 17 / 18 | USB D- / D+ |
| 14 | 19 | Spare, NC; former USB input disable |
| 20 | 26 | Charging allowed, active high |
| 21 | 27 | Charger interrupt, active low |
| 22 / 23 | 28 / 29 | Spare, NC; former input-limit selection |

GPIO6/7 serve charger I2C. GPIO18 is also spare after reset-wire removal; GPIO19/2 carry ring TX/RX and GPIO3 switches pod power.

## Firmware contract

1. Initialize with pod power and charging disabled. Program and read back input-current, charge-current, voltage and temperature settings before allowing charging.
2. Read BQ25186 VIN_PGOOD_STAT (STAT0, address 0x00, bit 0) at startup and when servicing charger interrupts; refresh periodically as needed. This indicates usable charger input, not mere physical cable presence. There is no VBUS GPIO or TUSB320 to query. Keep charge enable low if charger communication or required temperature readings are unavailable.
3. Budget input current for system operation and charging. Include charger reset defaults and depleted-battery startup in the selected power policy.
4. For USB suspend with a usable battery, SYS_MODE=01 supplies SYS from BAT and stops charging. No independent external USB disconnect remains. Handle battery-unavailable operation separately.
5. Preserve distributed temperature checks; disable charging before pod shutdown or loader entry when charging depends on those readings.

Initial bracelet firmware now keeps charging disabled and exposes its console over native USB Serial/JTAG. It is build-verified but has not been flashed; charger register handling, button behavior and USB/charge bench validation remain open.

## Verification

The main now contains 72 components, after removing J1 and Q4/R34/R35/R36 as well as the earlier pod-interface cleanup (J3 and R48/R50/R52 removed, R62 added). ERC and schematic/PCB parity report zero issues. Checks confirm the VBUS merge, independent CC pull-downs, USB data polarity, MCU thermistor interface, fixed charger TS/MR termination, and every PCB pad/symbol association. All retained component placements are preserved.

Main routing remains unfinished: 200 opens and five silk/library warnings. Satellite source files are unchanged. Current reports are in `hardware/verification/project-split/`; the earlier USB-only snapshot is in `hardware/verification/simple-usb/`; the full updated PDF is `hardware/verification/project-split/main.pdf`.

## References

- [TI USB Type-C guide](https://www.ti.com/lit/SLYY228): passive Rd sink attachment.
- [BQ25186 datasheet](https://www.ti.com/lit/ds/symlink/bq25186.pdf): input-current register, SYS modes and charging control.
- [Espressif native Serial/JTAG](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/usb-serial-jtag-console.html).
- [TPD2EUSB30 datasheet](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf).
