> **2026-09-14 architecture:** one controller daughterboard, eight universal haptic pods, seven protected cells and required cell NTCs on pods 1-7. Pod 0 has neither external connection. The 301730/160 mAh suggestion is a candidate pending exact part and protected-pack fit/rating checks; seven would give 1,120 mAh. Firmware charge/load settings must follow the selected seven-cell pack.

# Bracelet power architecture

> Project update (2026-09-13): active sources are `hardware/main/` and `hardware/satellite/`. Main references are unchanged; historical satellite references map to the one universal design in [PCBA projects](pcba-projects.md). Any combined-board placement/count or verification statements below describe the earlier checkpoint; [current routing status](pcb-routing.md) supersedes them.

Status: seven protected 90 mAh batteries, one in each of pods 1-7, connected as **1S7P per wrist**. Native revision 0.5 removes the central protector and adds local bulk capacitance. The YDL301230 protected assembly establishes a 3 x 12 x 32 mm body envelope. Capacity is 630 mAh nominal; runtime and physical load qualification remain open.

## Electrical arrangement

Use one permanently assembled group of seven identical protected pouch batteries per wrist. Keep the factory PCM intact on every battery. Connect PACK+ through its local positive-branch fuse to VBAT; connect PACK- to system GND. Raw cell terminals do not connect directly to the bracelet PCB. There is no central ABLIC protector, shunt or protection FET pair.

```text
Battery 1 (factory PCM) PACK+ -- fuse --+
Battery 2 (factory PCM) PACK+ -- fuse --+-- VBAT <--> BQ25186 BAT
...                                    |
Battery 7 (factory PCM) PACK+ -- fuse --+
All protected PACK- leads ---------------- GND

USB-C --> power-path charger SYS --> buck-boost --> 3V3 (ESP32/control)
                                                   +-- TPS22918 --> POD_3V3
                                                       eight MCU/driver pods
                                                       +22 uF bulk per pod
```

VBAT is harness pin 4, the combined protected battery-output bus. It connects directly to U11 BAT and C36. It remains live when POD_3V3 is off or the charger is in ship mode. J4/F1 on pods 1-7 carry their protected battery outputs. Pod 0 J4 is unwired. The daughterboard has no battery branch; its J101 pin 4 receives VBAT. See [protection implementation](pack-protection-implementation.md).

Each factory PCM monitors its own cell and can disconnect independently. The remaining branches then share the load and charging current. Individual PCMs are not equivalent to the removed aggregate current cutoff; final fuse ratings and charge/load policy must account for branch loss, unequal sharing and actual PCM recovery behavior. PCB connectivity checks cannot verify those external protection functions.

While their PCMs conduct, cells in the permanently connected group share approximately the same voltage, so series-cell balancing is not required. Use the same cell model/chemistry and suitably matched condition; equalize voltage with controlled current before assembling the permanent parallel connections. Do not make independently removable/hot-swappable cells part of this baseline: reconnection would need an additional controlled-current/isolation design.

Plan for 4.20 V-charge, nominal 3.7 V batteries matching the YDL example. Its ratings give 45 mA maximum continuous discharge per cell, **315 mA total with seven equally sharing branches**, or 1.1655 W at nominal voltage. Standard charge is 18 mA per cell (126 mA aggregate), maximum 45 mA (315 mA aggregate). These aggregate values are not safe defaults when branches have disconnected; final charger settings and recovery policy remain firmware work.

## Charger: BQ25186

The TI BQ25186 provides 1S CC/CV charging, power-path load sharing, 5 mA to 1 A programmable fast-charge current, thermistor monitoring, ship mode and button wake. It can sit on the main-board I2C bus at 0x6A with the former TUSB320 CC controller removed. Each pod controls its own DRV2625 at 0x5A on local I2C.

USB supplies SYS when connected, and the battery supplies SYS when unplugged. The power path separates system load from battery charging so continued device operation does not inherently prevent proper charge termination. Available input current is shared with the load; charging can slow or pause when the load consumes the source budget.

For this design retain a 4.5 V SYS regulation setting while externally powered (the register default); battery-only SYS follows the battery through the battery FET. Do not select 5.5 V or pass-through modes with a TPS63802 downstream without rechecking its maximum input voltage, tolerance and transients.

Use a charge-disable hardware state until the cell-specific settings and temperature conditions are valid. Check cold start, watchdog/register reset and depleted-pack recovery as part of implementation. BQ25186 is a linear charger: the first-order charging loss is (Vin - Vbat) * Icharge, with additional loss from the system power path. As an illustration, 5 V input, 3.7 V battery and 200 mA charging dissipate about 0.26 W from charging alone; 200 mA is not a selected charge setting.

USB-C 5 V is the selected charging interface, with D-/D+ also connected to native ESP32-C6 Serial/JTAG. Two 5.1k CC pull-downs provide sink termination; no CC controller is fitted. USB Power Delivery is not required for this 5 V design. Do not infer permission to draw 1 A from the charger IC rating alone.

## Regulator: TPS63802 at 3.3 V

A buck-boost supplies 3.3 V as the source moves above and below that voltage. It also accepts the charger's higher SYS voltage when externally powered. TI specifies 2 A output at 3.3 V for input >= 2.3 V. This is component capability, not a proven bracelet current budget; inductor, effective capacitance, layout, temperature, battery impedance and protection must all support the intended load.

The regulated 3V3 rail supplies the ESP32 and main-board control. A TPS22918 switches all eight pod MCUs and drivers onto POD_3V3, with local decoupling. Firmware prevents UART back-powering by driving TX low and disabling the RX pull-up before shutdown. See [ring pods](ring-pods.md) for the reset circuit, interconnect and power sequence. Actuator headroom and simultaneous-current budget remain to be checked after LRA selection.

The charger/regulator and supporting circuit are in the native schematic. The former protection child sheet is archived under `hardware/backups/before-protected-cells/`; the active main project has five sheets and the satellite project one. The former charger thermistor connector is removed; controller J3 now denotes ESP recovery pads. Universal pod J5 connects each cell thermistor to its local M2003 ADC; it is unwired on pod 0. R62 (10k) terminates charger TS/MR to GND, with SW3 in parallel; temperature supervision is performed by firmware. Universal J4/F1 provide the protected battery branches on pods 1-7 only. Five-pad harness interfaces and Littelfuse 0467.250NR 250 mA branch fuses are assigned.

## Distributed mechanics and temperature

Treat each pouch location as a supported segment, with flex occurring in the strap/interconnect between segments. Preserve the cell supplier's clearance/expansion allowances, insulate tabs, and provide strain relief so strap motion does not load the cell tabs. Keep actuator forces and sharp PCB edges away from pouch faces. Use short, low-resistance branch wiring; account for branch resistance when evaluating current sharing.

Plan temperature sensing at each separated pouch location. There is no independent charger thermistor. All eight universal pod boards retain their M2003 ADC/NTC input circuitry; pod 0 has no external NTC connected. Firmware must inhibit charging if any required cell reading is missing, stale or outside its specified temperature range. Sensor selection, required-cell configuration and firmware remain open. Charging must be disabled before ring power-off or loader entry when it relies on those readings.

## Sizing method

For N identical cells, nominal pack capacity is N * Ccell; voltage remains one-cell voltage. First estimate runtime from energy:

    runtime_hours ~= N * Ccell_Ah * Vnom * conversion_efficiency / average_load_W

Eight 90 mAh, 3.7 V cells contain 2.664 Wh nominally. With an illustrative 85% usable-energy/conversion factor, this gives about 2.26 hours at 1 W or 4.53 hours at 0.5 W. These are energy scenarios, not runtime predictions; continuous-current limits also apply. Cutoff, aging, rate and temperature affect usable energy.

Check peak current separately: the pack must support coincident ESP32 radio activity and the allowed simultaneous haptic outputs, including at low state of charge. Firmware mapping duty cycle determines average actuator energy. Charge settings and allowed haptic load should follow those measurements and the battery ratings; the planned cell count is seven.

## Sources inspected

- [TI BQ25186 datasheet](https://www.ti.com/lit/ds/symlink/bq25186.pdf): power path, charging, thermistor, modes, address and SYS register.
- [TI TPS63802](https://www.ti.com/product/TPS63802) and [datasheet](https://www.ti.com/lit/ds/symlink/tps63802.pdf): input/output range and specified current capability.
- [TI DRV2625 datasheet](https://www.ti.com/lit/ds/symlink/drv2625.pdf): supply range and I2C pin voltage constraint.
- [TI battery protector overview](https://www.ti.com/product-category/battery-management-ics/battery-protectors/overview.html): voltage, current and short-circuit protection functions.

Pack/interconnect arrangements above are engineering proposals for this device. None of these IC datasheets qualifies the as-yet-unselected distributed pouch pack.
