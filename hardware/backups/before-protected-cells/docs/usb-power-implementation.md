# USB-C and power implementation, revision 0.2

Implemented in the native KiCad schematic. This is a first circuit pass; PCB placement/routing and firmware are not implemented.

## Native data connection

J2 is a USB-C USB2 16-contact receptacle symbol; its mechanical part/footprint remains to select. A6/B6 join D+, A7/B7 join D-. TPD2EUSB30 provides data-line ESD protection. R24/R25 are initial 22-ohm series resistors near the MCU; C29/C30 are DNP tuning-capacitor footprints.

- ESP32-C6-MINI-1 pin 17 / GPIO12: USB D-.
- ESP32-C6-MINI-1 pin 18 / GPIO13: USB D+.
- Native function: USB 2.0 full-speed Serial/JTAG, including flashing and serial console. This is not a general USB OTG/HID/MIDI controller.
- J1 UART and the existing BOOT/RESET buttons remain available for recovery.
- Join duplicate contacts near J2; keep the differential pair short, 90-ohm controlled impedance, and away from buck-boost switching nodes. Final routing has not been done.

## USB-C attachment and input limits

U13 TUSB320LAI is strapped sink-only (PORT low) and I2C address 0x47 (ADDR low). Its internal Rd resistors also provide dead-battery termination; no extra external 5.1k CC resistors are fitted. It reports attach/detach, orientation and advertised current class. R26 is 887k 1% from raw VBUS to VBUS_DET, within TI's updated specified 855-920k range. U15 protects CC against ESD, not a sustained short to a higher-voltage VBUS.

Q4 provides inverted VBUS presence to the MCU without a 5 V GPIO connection. The TUSB320 remains powered from the common regulated 3V3 rail, matching the I2C pull-up domain.

U16 TPS2553 is ahead of U11's input. U17 TS5A3159 selects the startup limit or a resistor-programmed limit. U17 is powered from VBUS; 3.3 V GPIO control exceeds its 2.4 V VIH requirement at a 5 V supply.

| USB_LIMIT_ENABLE | USB_LIMIT_HIGH | Hardware path | Calculated limit |
| --- | --- | --- | --- |
| 0 | either | ILIM to IN via normally closed analog switch | 75 mA typical; TI specifies 50-100 mA for direct ILIM-to-IN |
| 1 | 0 | 62k to GND | about 377-479 mA including 1% resistor tolerance |
| 1 | 1 | 62k in parallel with 43k through Q3 | about 934-1109 mA including 1% resistor tolerance |

The calculated ranges use TPS2553 datasheet section 9.5.1. Switch resistance/leakage and switching dynamics are not included. The startup maximum is a device output-current limit: USB-side housekeeping adds current. Inrush, exact USB current-budget compliance, unpowered transitions and reliable battery-free boot are still bench/design checks; these calculations do not establish a compliant port.

USB_INPUT_OFF drives Q2 to disable U16. It defaults low, allowing startup power. USB_LIMIT_ENABLE and USB_LIMIT_HIGH both default low. C32 is 1uF on raw VBUS, C33 is local 100nF for the selector. Larger system capacitance is downstream of the input switch/charger.

Do not raise the limit just because a USB-C plug is present. A legacy/default-current attachment needs actual host configuration and its granted current budget. Only use the high mode with a valid sufficient Type-C advertisement. This design does not implement BC1.2 charger detection. A default-current wall adapter may consequently charge slowly.

## Charger and regulator

U11 BQ25186DLHR is at 0x6A on the upstream bus. It supplies SYS from USB or BAT. U12 TPS63802DLAR converts SYS to 3V3. R40=511k and R41=91k give 3.308 V nominal using the 0.500 V reference. L1 is 0.47uH, with its exact current-rated part and land pattern still open. C37 is 10uF input capacitance; C38/C39 provide nominal 44uF output capacitance. Choose actual capacitors based on effective capacitance at bias, not just the labels.

U12 MODE is low for power-save operation and EN follows SYS. Ship/wake control belongs to U11; SW3 connects TS/MR to GND as a momentary button. U11's SYS setting must remain at 4.5 V while externally powered; do not select 5.5 V/pass-through with this downstream regulator.

R38 pulls /CE to SYS and Q1 pulls it down only when CHG_ALLOW is asserted. R39 defaults that GPIO path off. No firmware has been written to enable charging. The cell voltage, current, temperature thresholds and timeout policy must be set for the selected pack. Register-reset/watchdog behavior must not silently restore unsuitable charging settings.

J3 is the **protected 1S-NP pack interface**, not an unprotected pouch connection:

| Pin | Function |
| --- | --- |
| 1 | Protected pack positive |
| 2 | Protected pack negative / system GND |
| 3 | Charger TS/MR connection to a suitable pack NTC |
| 4 | NTC return / system GND |

Pack protection, branch fuses and monitoring of the other distributed pouch temperatures still need circuit/mechanical design. There is no dummy onboard NTC that permits charging with missing pack sensing. A single NTC at J3 does not substitute for the agreed distributed-temperature coverage. The firmware must leave CHG_ALLOW low until the complete temperature policy is implemented.

## Added GPIO assignments

| GPIO | MINI-1 pin | Function |
| --- | --- | --- |
| 0 | 12 | CC controller interrupt, active low |
| 1 | 13 | VBUS present, active low |
| 12 | 17 | USB D- |
| 13 | 18 | USB D+ |
| 14 | 19 | USB input off, active high |
| 20 | 26 | Charging allowed, active high |
| 21 | 27 | Charger interrupt, active low |
| 22 | 28 | Select programmed USB input limit |
| 23 | 29 | Select higher programmed input limit |

GPIO6/7 remain main-board I2C. GPIO18 now asserts shared pod reset through Q5; GPIO19/2 provide ring TX/RX and GPIO3 controls switched pod power. See [ring pods](ring-pods.md). These assignments are recorded in the schematic but have no firmware implementation yet.

## Required firmware behavior

1. Boot with pod power off and UART pins in their unpowered states, charging off, higher current modes off, and radio activity deferred until the available supply budget is known. Check reliable minimum-current boot with depleted/absent battery.
2. Read VBUS and TUSB320 attachment/current state. Configure the BQ25186 input budget and select only a hardware limit permitted by the source. Inspect the native Serial/JTAG descriptors and configuration state before assuming a host granted 500 mA.
3. Validate the pack and all required temperature sensors before enabling cell-specific charging. Program and verify charging settings; handle register resets/watchdog faults.
4. On detach/reset/reduced-current advertisement, revoke high-current permission promptly. Disable charging before reducing the source budget. Check limit-switch transition behavior under load.
5. On USB suspend, stop charging and meet the applicable suspended-device power budget. With a usable battery, force U11's SYS_MODE=01 (battery supply) and optionally disconnect the USB input. With no usable battery, maintain a verified low-power USB-supplied state: blindly disconnecting input would brown out the MCU and reset the input-enable GPIO, potentially making a restart loop. Firmware and measured suspend-current validation are required.
6. Gate native USB attachment using valid VBUS state as required for self-powered operation; verify unplug/replug while the battery keeps the MCU running. Resume must restore valid source/battery settings, not blindly restore prior charge current.

## Verification and open work

- KiCad loads and exports all 13 sheets.
- Existing haptic and new USB/power netlist checks pass. Power rails are distinct; both orientations and D+/D- polarity reach the correct MCU pins.
- Five custom IC pin tables were compared with primary TI sources. Datasheets are cached with hashes in hardware/datasheets.
- ERC: 0 errors, 0 warnings after placing no-connect flags on the eight unused DRV2625 TRIG/INTZ pins; no exclusions added.
- Divider/current-limit calculations are in hardware/verification/usb-power-checks.json. No SPICE simulator was found on PATH; these are calculations and connectivity checks, not transient simulation.
- Power IC, USB connector, inductor and pack footprints/parts remain partly unassigned. FET MPNs must be finalized with suitable 3.3 V gate performance. No PCB layout or physical USB, charging, thermal, pack or radio-load tests have been performed.

## Primary references

- [Espressif native Serial/JTAG](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/usb-serial-jtag-console.html).
- [Espressif schematic guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/schematic-checklist.html#usb).
- [BQ25186 datasheet](https://www.ti.com/lit/ds/symlink/bq25186.pdf), pin table p.3 and charging/power-path registers.
- [TPS63802 datasheet](https://www.ti.com/lit/ds/symlink/tps63802.pdf), pin table p.4, reference p.6 and application pp.17-20.
- [TUSB320LAI datasheet](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf), pp.3-6 pin/bias requirements and sink/dead-battery operation.
- [TPS2553 datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf), pp.5-7 pin/electrical requirements and p.15 limit formula.
- [TS5A3159 datasheet](https://www.ti.com/lit/ds/symlink/ts5a3159.pdf), pp.3-4 pin table and control thresholds.
- [TPD2EUSB30 datasheet](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf), p.3 pin table.
