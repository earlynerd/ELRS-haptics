# Standby and controls assessment

2026-09-12. Assessment of the native schematic and current manufacturer documentation, subsequently extended with the user's RGB indicator request. The reset driver is released once pod power is off; the sequencing contract in `ring-pods.md` is updated. The RGB circuit is implemented below; firmware is still pending.

## Actuator offset

The regular PCB envelope is 17 mm wide with a 7 mm opening. Centering leaves 5 mm on each side. Moving the opening 2 mm sideways gives 3 mm and 7 mm strips; a 3 mm move gives 2 mm and 8 mm. Total board area is unchanged, but the wider contiguous region is easier to populate. Keep the flex tail facing the wider region. Actual flex landings still occupy some of it. Sidewall, mounting-seat clearance and narrow-web strength remain layout checks. Apply a consistent offset around the wrist if adopted. No offset has been applied to study B yet.

## Existing button and proposed behavior

SW3 already connects BQ25186 TS/MR (PACK_TS) to GND. SW1 and SW2 are ESP reset and boot recovery controls. The packaging sketch omitted these controls; expose SW3 as the normal main-pod button and keep recovery controls accessible internally. The charger can wake SYS from ship mode with the button or valid input power. Its long-press action is programmable, and short-press events reach CHG_nINT. These functions require firmware configuration and pack-NTC/button behavior validation.

Recommend ship mode for user off with USB disconnected: stop the radio, disable charging, shut down the pod rail using the documented UART/reset sequence, then request ship mode. SYS and downstream 3V3 turn off. Distinguish this from charger shutdown mode, whose button cannot wake it; valid input power can. Charging/USB-connected operation needs its own policy and cannot use the unplugged off-current estimate.

C6 deep sleep retains a timer-wake option but is less attractive for long storage with the present always-powered CC controller. CHG_nINT presently goes to GPIO21, which is not one of GPIO0..7 supported for C6 deep-sleep GPIO/EXT1 wake. GPIO4/5 are now assigned to the RGB indicator. If button wake from C6 deep sleep is required, revise pin allocation to provide a suitable wake GPIO rather than treating GPIO21 as deep-sleep capable. Ship-mode button wake does not require that reroute because the charger restores SYS itself.

## Implemented RGB indicator

The user requested RGB for charging status. D1 is a discrete four-terminal common-anode RGB LED, common anode to 3V3. Red/green/blue cathodes connect through R47/R49/R51 (initially 2.2k each) to GPIO4/5/15. R48/R50/R52 are 100k pullups on the GPIO sides, defining off while pins are high-impedance. Drive low to illuminate; drive high before sleep. PWM can tune color and brightness. An active color also draws about 33 uA through its GPIO pullup; no nominal pullup current flows when off. The resistor bounds LED current below 1.6 mA per channel at 3.3 V even with zero forward drop, but actual brightness and blue/green headroom require the selected LED. MPN and footprint remain unassigned until its common-anode pinout is selected.

GPIO4/5 also select unused SDIO timing straps; GPIO15 high preserves native USB JTAG selection. No eFuse changes are needed. These assignments consume the remaining three general-purpose pins identified in the existing allocation. SW1/SW2 remain internal recovery buttons, with SW3 exposed on the main shell. The packaging sketch now shows a provisional side-access button and lid indicator window; actual switch, window and light-pipe dimensions are open.

Initial firmware indication proposal: amber charging, green charge complete, blue radio/link status, blinking red fault. Charge complete must come from charger status with valid pack/temperature state, not merely USB presence or a disabled charge path. Faults take display priority; sleep and user off are dark. USB-connected charging keeps the required temperature-monitoring firmware active as already documented. No indication firmware is implemented yet.

## Battery-only standby contributions

| Contribution | Reference typical current | Basis |
| --- | ---: | --- |
| C6 deep sleep | 7 uA on 3V3 | RTC timer and LP memory on; datasheet table is excerpted from SoC data |
| C6 light sleep, alternative to deep sleep | 35 or 180 uA on 3V3 | Different peripheral power configurations; not additive |
| BQ25186 battery-only | 4 uA at battery | Push-button enabled, 3.6 V battery |
| TPS63802 operating IQ | 11 uA at SYS | 3.6 V input, 3.3 V output, not switching; excludes output load and switching losses |
| TUSB320LAI unattached sink | 70 uA at its VDD | Specified at 4.5 V and ADDR floating; our 3.3 V/I2C connection differs, so use only as a planning reference |
| TPS22918 off | 0.5 uA on 3V3 | 3.3 V input, output zero; datasheet max 3.5 uA over temperature |
| R40 + R41 feedback divider | 5.50 uA on 3V3 | 3.308 V / (511k + 91k) |
| R7 reset gate pulldown | Zero nominal in steady off; 33.08 uA during reset assertion | Updated sequence drives GPIO18 low after rail/reset discharge |
| S-821AAAC protector U27 | 6 uA at battery | 3.4 V normal-state test; 10 uA max at 25 C, 14 uA max over -40 to +85 C |

The eight pod MCUs, drivers and NTC bias circuits sit downstream of the off switch, so their ordinary standby currents are not added. Pin-state control is necessary to prevent backpower. TPS2553 and TS5A3159 are powered from USB VBUS, not the battery rail; with VBUS absent their normal operating IQ is not a battery load. GPIOs into the unpowered selector must remain low. Other leakage and actual module flash behavior are not fully budgeted here.

Illustrative calculation at 3.7 V battery, 3.308 V rail and an assumed 85% incremental conversion efficiency: `6 + 4 + 11 + (7 + 70 + 0.5 + 5.50) * 3.308 / (3.7 * 0.85) = 108 uA`. This includes the selected protector and the user's correction to release the reset driver after discharge. It is an order-of-magnitude estimate, **not a measured standby figure or guaranteed limit**. Other leakage is excluded. The converter's no-switching IQ plus an assumed conversion factor is only a budgeting model.

Leaving an interrupt low adds about 331 uA through each 10k pull-up. Holding either main I2C line low adds about 704 uA through its 4.7k pull-up. Clear/handle interrupt status, leave I2C idle and preserve sleep GPIO states. R7's former steady-off load is removed by the updated sequencing contract: assert during power-down, release after discharge, and assert again before power-up. Discharge timing remains to be established on hardware.

With USB absent, **BQ25186 ship current is 3.2 uA typical, 5 uA maximum under the specified conditions**, with downstream SYS disconnected. Adding U27's 6 uA typical gives approximately **9.2 uA plus residual leakage** as a planning estimate; do not claim 3.2 uA for the complete bracelet. U27 stays powered in charger ship mode, and this suffix has no power-down function. Charger shutdown is 15 nA typical but loses button wake. Neither current describes charging operation. For comparison, the charger input IQ at 5 V, 4.5 V SYS and zero charge current is 0.75 mA typical.

## During flying

Deep sleep powers the radio off. The C6 datasheet lists a 78 mA Wi-Fi RX operating point (peak table), so active telemetry operation is a tens-of-mA problem before actuator loads, not a microamp standby problem. ESP-NOW supports station-mode wake windows and intervals, but missed packets and latency must be tested with the actual backpack sender. No duty-cycle savings are assumed in the runtime budget yet.

## Evidence

- Native power/USB/controller symbols and `hardware/verification/netlist.xml`: SW3, U11/U12/U13/U26, R7/R40/R41, GPIO21 interrupt routing and GPIO4/5/15 RGB channels. RGB/button checks are in `hardware/verification/status-controls-checks.json`.
- [ESP32-C6-MINI-1 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf), tables 6-4 and 6-8.
- [ESP-IDF C6 sleep guidance](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/system/sleep_modes.html).
- [ESP-NOW power saving](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/network/esp_now.html).
- [BQ25186](https://www.ti.com/lit/ds/symlink/bq25186.pdf), electrical table and sections 6.3.9 and 6.5.1.10.
- [TPS63802](https://www.ti.com/lit/ds/symlink/tps63802.pdf), electrical table.
- [TUSB320LAI](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf), section 6.5.
- [TPS22918](https://www.ti.com/lit/ds/symlink/tps22918.pdf), section 6.5.

Confidence: high for the quoted specification conditions and inspected connections; provisional for complete-board current and physical packaging. The reset sequencing documentation and native RGB circuit are updated; firmware code and PCB remain unimplemented.
