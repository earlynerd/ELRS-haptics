# Standby and controls assessment

> Project update (2026-09-13): active sources are `hardware/main/` and `hardware/satellite/`. Main references are unchanged; historical satellite references map to the one universal design in [PCBA projects](pcba-projects.md). Any combined-board placement/count or verification statements below describe the earlier checkpoint; [current routing status](pcb-routing.md) supersedes them.

2026-09-12. Assessment of the native schematic and current manufacturer documentation, subsequently extended with the user's RGB indicator request. The shared reset driver and USB CC controller are now removed; the sequencing contract in `ring-pods.md` is updated. The RGB circuit is implemented below; firmware is still pending.

## Actuator offset

The regular PCB envelope is 17 mm wide with a 7 mm opening. Centering leaves 5 mm on each side. Moving the opening 2 mm sideways gives 3 mm and 7 mm strips; a 3 mm move gives 2 mm and 8 mm. Total board area is unchanged, but the wider contiguous region is easier to populate. Keep the flex tail facing the wider region. Actual flex landings still occupy some of it. Sidewall, mounting-seat clearance and narrow-web strength remain layout checks. Apply a consistent offset around the wrist if adopted. No offset has been applied to study B yet.

## Existing button and proposed behavior

SW3 connects BQ25186 TS/MR to GND, in parallel with R62 (10k). The charger has no separate thermistor; all eight cell temperatures are read by their local M2003 ADCs. SW1 and SW2 are ESP reset and boot recovery controls. The packaging sketch omitted these controls; expose SW3 as the normal main-pod button and keep recovery controls accessible internally. The charger can wake SYS from ship mode with the button or valid input power. Its long-press action is programmable, and short-press events reach CHG_nINT. These functions require firmware configuration and button behavior validation.

Recommend ship mode for user off with USB disconnected: stop the radio, disable charging, shut down the pod rail using the documented UART/power sequence, then request ship mode. SYS and downstream 3V3 turn off. Distinguish this from charger shutdown mode, whose button cannot wake it; valid input power can. Charging/USB-connected operation needs its own policy and cannot use the unplugged off-current estimate.

C6 deep sleep retains a timer-wake option. Removing the always-powered CC controller reduces the planned sleep load. CHG_nINT presently goes to GPIO21, which is not one of GPIO0..7 supported for C6 deep-sleep GPIO/EXT1 wake. GPIO4/5 are now assigned to the RGB indicator. If button wake from C6 deep sleep is required, revise pin allocation to provide a suitable wake GPIO rather than treating GPIO21 as deep-sleep capable. Ship-mode button wake does not require that reroute because the charger restores SYS itself.

## Implemented RGB indicator

The user requested RGB for charging status. D1 is a discrete four-terminal common-anode RGB LED, common anode to 3V3. Red/green/blue cathodes connect through R47/R49/R51 (initially 2.2k each) to GPIO4/5/15. R48/R50/R52 have been removed: high-impedance GPIOs do not sink LED current, and these pull-ups are not required by the intended boot configuration. Drive low to illuminate; drive high before sleep. PWM can tune color and brightness. The resistor bounds LED current below 1.6 mA per channel at 3.3 V even with zero forward drop, but actual brightness and blue/green headroom require the selected LED. The selected LED is LTST-C19HE1WT.

GPIO4/5 select unused SDIO timing straps. With JTAG_SEL_ENABLE left at its default zero, GPIO15 is ignored for JTAG selection; native USB JTAG remains selected. No eFuse changes are planned. GPIO0/1/14/18/22/23 are now spare after USB/reset simplification. J1 UART service pads are removed; native USB provides programming, serial and JTAG. SW1/SW2 remain internal recovery buttons, with SW3 exposed on the main shell. The packaging sketch now shows a provisional side-access button and lid indicator window; actual switch, window and light-pipe dimensions are open.

Initial firmware indication proposal: amber charging, green charge complete, blue radio/link status, blinking red fault. Charge complete must come from charger status with valid pack/temperature state, not merely USB presence or a disabled charge path. Faults take display priority; sleep and user off are dark. USB-connected charging keeps the required temperature-monitoring firmware active as already documented. No indication firmware is implemented yet.

## Battery-only standby contributions

| Contribution | Reference typical current | Basis |
| --- | ---: | --- |
| C6 deep sleep | 7 uA on 3V3 | RTC timer and LP memory on; datasheet table is excerpted from SoC data |
| C6 light sleep, alternative to deep sleep | 35 or 180 uA on 3V3 | Different peripheral power configurations; not additive |
| BQ25186 battery-only | 4 uA at battery | Push-button enabled, 3.6 V battery |
| TPS63802 operating IQ | 11 uA at SYS | 3.6 V input, 3.3 V output, not switching; excludes output load and switching losses |
| TPS22918 off | 0.5 uA on 3V3 | 3.3 V input, output zero; datasheet max 3.5 uA over temperature |
| R40 + R41 feedback divider | 5.50 uA on 3V3 | 3.308 V / (511k + 91k) |
| Eight factory battery PCMs | Approximately 8 uA total typical, 56 uA maximum from the example PCM table | YDL table lists 1 uA typical / 7 uA maximum per PCM; exact supplied PCM and conditions require confirmation |

The eight pod MCUs, drivers and NTC bias circuits sit downstream of the off switch, so their ordinary standby currents are not added. Pin-state control is necessary to prevent backpower. TUSB320, TPS2553 and TS5A3159 are removed; their supply and control-pin loads no longer apply. Other leakage and actual module flash behavior are not fully budgeted here.

Illustrative calculation at 3.7 V battery, 3.308 V rail and an assumed 85% incremental conversion efficiency: `8 + 4 + 11 + (7 + 0.5 + 5.50) * 3.308 / (3.7 * 0.85) = approximately 37 uA`. This includes eight illustrative 1 uA battery PCMs and excludes the removed USB CC controller/reset drive. It is an order-of-magnitude estimate, **not a measured standby figure or guaranteed limit**. Other leakage is excluded. The converter's no-switching IQ plus an assumed conversion factor is only a budgeting model.

Leaving an interrupt low adds about 331 uA through each 10k pull-up. Holding either main I2C line low adds about 704 uA through its 4.7k pull-up. Clear/handle interrupt status, leave I2C idle and preserve sleep GPIO states. R7 and the shared reset drive are removed entirely. Discharge timing remains to be established on hardware.

With USB absent, **BQ25186 ship current is 3.2 uA typical, 5 uA maximum under its specified conditions**, with downstream SYS disconnected. Eight factory PCMs at the YDL example's 1 uA typical each give approximately **11.2 uA plus residual leakage** for the complete bracelet. All eight PCMs remain attached to their cells in ship mode; confirm the actual shipped PCM specification. The central U27 no longer exists. Charger shutdown is 15 nA typical but loses button wake. Neither figure describes charging; charger input IQ at 5 V, 4.5 V SYS and zero charge current is 0.75 mA typical.

## During flying

Deep sleep powers the radio off. The C6 datasheet lists a 78 mA Wi-Fi RX operating point (peak table), so active telemetry operation is a tens-of-mA problem before actuator loads, not a microamp standby problem. ESP-NOW supports station-mode wake windows and intervals, but missed packets and latency must be tested with the actual backpack sender. No duty-cycle savings are assumed in the runtime budget yet.

## Evidence

- Native power/USB/controller symbols and `hardware/verification/netlist.xml`: SW3, U11/U12/U13/U26, R7/R40/R41, GPIO21 interrupt routing and GPIO4/5/15 RGB channels. RGB/button checks are in `hardware/verification/status-controls-checks.json`.
- [ESP32-C6-MINI-1 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf), tables 6-4 and 6-8.
- [ESP-IDF C6 sleep guidance](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/system/sleep_modes.html).
- [ESP-NOW power saving](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/network/esp_now.html).
- [BQ25186](https://www.ti.com/lit/ds/symlink/bq25186.pdf), electrical table and sections 6.3.9 and 6.5.1.10.
- [TPS63802](https://www.ti.com/lit/ds/symlink/tps63802.pdf), electrical table.
- [TPS22918](https://www.ti.com/lit/ds/symlink/tps22918.pdf), section 6.5.

Confidence: high for the quoted specification conditions and inspected connections; provisional for complete-board current and physical packaging. Initial firmware implements safe startup states and basic RGB status, but ship mode, button handling, charging, sleep current and all physical behavior remain unverified.
