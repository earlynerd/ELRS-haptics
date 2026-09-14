# Bracelet power architecture

Status: accepted architecture with initial USB-C/charger/regulator circuit and switched ring-pod circuit implemented, 2026-09-12. The user has chosen **1S with an unspecified number of parallel cells per wrist**. Cell capacity, count, and runtime remain open. See [USB/power implementation](usb-power-implementation.md) for the native schematic connections and outstanding work.

## Electrical arrangement

Use one permanently assembled 1S-NP pack per wrist, with matched pouch cells distributed mechanically around the strap. Each cell branch receives local fault-current protection before joining the common battery bus. A pack protector with a high-side bidirectional disconnect separates the assembled pack from the charger/load. Its voltage/current thresholds and branch fuse behavior must be selected against the actual cells and interconnect.

```text
Pouch 1 -- branch fuse --+
Pouch 2 -- branch fuse --+-- 1S pack protection <--> Charger BAT
Pouch N -- branch fuse --+

5 V charging input --> power-path charger SYS --> buck-boost --> regulated 3V3
                                                              |-- ESP32-C6
                                                              |-- USB/charger control
                                                              +-- TPS22918 switch --> 8 MCU + driver pods
```

VBAT_RAW is the fifth conductor around the ring. Each pod has an optional cell connection and fuse provision. The `protection.kicad_sch` child sheet now connects this raw positive bus to BAT_PROTECTED through the shunt and two high-side FETs, replacing the J4 placeholder. All cell negatives retain common GND.

This is a functional diagram, not a completed protection schematic. Both pack terminals and the disconnect arrangement need explicit wiring in the circuit design. The charger and pack protection have distinct jobs. A shared disconnect alone cannot interrupt current circulating between parallel cells; branch protection belongs near each cell. A fuse can limit externally supplied fault current, but does not stop a cell's internal failure. Charge/discharge limits must also account for loss of a branch and unequal current sharing.

Cells in the permanently connected group share voltage, so series-cell balancing is not required. Use the same cell model/chemistry and suitably matched condition; equalize voltage with controlled current before assembling the permanent parallel connections. Do not make independently removable/hot-swappable cells part of this baseline: reconnection would need an additional controlled-current/isolation design.

Assume conventional 4.20 V-charge LiPo for candidate evaluation only. Final voltage, termination, precharge, current and temperature settings come from the chosen cell datasheet; the user has not selected a chemistry variant or cell MPN.

## Charger: BQ25186

The TI BQ25186 provides 1S CC/CV charging, power-path load sharing, 5 mA to 1 A programmable fast-charge current, thermistor monitoring, ship mode and button wake. It can sit on the main-board I2C bus at 0x6A alongside TUSB320LAI at 0x47. Each pod controls its own DRV2625 at 0x5A on local I2C.

USB supplies SYS when connected, and the battery supplies SYS when unplugged. The power path separates system load from battery charging so continued device operation does not inherently prevent proper charge termination. Available input current is shared with the load; charging can slow or pause when the load consumes the source budget.

For this design retain a 4.5 V SYS regulation setting while externally powered (the register default); battery-only SYS follows the battery through the battery FET. Do not select 5.5 V or pass-through modes with a TPS63802 downstream without rechecking its maximum input voltage, tolerance and transients.

Use a charge-disable hardware state until the cell-specific settings and temperature conditions are valid. Check cold start, watchdog/register reset and depleted-pack recovery as part of implementation. BQ25186 is a linear charger: the first-order charging loss is (Vin - Vbat) * Icharge, with additional loss from the system power path. As an illustration, 5 V input, 3.7 V battery and 200 mA charging dissipate about 0.26 W from charging alone; 200 mA is not a selected charge setting.

USB-C 5 V is the selected charging interface, with D-/D+ also connected to native ESP32-C6 Serial/JTAG. TUSB320LAI provides internal CC sink termination and current-advertisement sensing. USB Power Delivery is not required for this 5 V design. Do not infer permission to draw 1 A from the charger IC rating alone.

## Regulator: TPS63802 at 3.3 V

A buck-boost supplies 3.3 V as the source moves above and below that voltage. It also accepts the charger's higher SYS voltage when externally powered. TI specifies 2 A output at 3.3 V for input >= 2.3 V. This is component capability, not a proven bracelet current budget; inductor, effective capacitance, layout, temperature, battery impedance and protection must all support the intended load.

The regulated 3V3 rail supplies the ESP32 and main-board control. A TPS22918 switches all eight pod MCUs and drivers onto POD_3V3, with local decoupling. Firmware prevents UART back-powering by driving TX low and disabling the RX pull-up before shutdown. See [ring pods](ring-pods.md) for the reset circuit, interconnect and power sequence. Actuator headroom and simultaneous-current budget remain to be checked after LRA selection.

The charger/regulator and supporting circuit are now in the native schematic. The power-source ERC errors are resolved. J3 carries protected pack terminals and the charger thermistor; U27 S-821AAAC-H8T7S, Q6/Q7 and R54 now implement the central high-side pack protector in `protection.kicad_sch`, replacing provisional J4. See [pack protection implementation](pack-protection-implementation.md). Cell/fuse provisions are drawn on the pod sheets, with parts and ratings pending.

## Distributed mechanics and temperature

Treat each pouch location as a supported segment, with flex occurring in the strap/interconnect between segments. Preserve the cell supplier's clearance/expansion allowances, insulate tabs, and provide strain relief so strap motion does not load the cell tabs. Keep actuator forces and sharp PCB edges away from pouch faces. Use short, low-resistance branch wiring; account for branch resistance when evaluating current sharing.

Plan temperature sensing at each separated pouch location. One charger thermistor cannot independently monitor several distant cells. The final design needs a means of inhibiting charge if any cell is outside its specified temperature range; do not combine thermistors into a network that can mask a hot cell. Each pod now includes a local ADC/NTC provision; sensor selection, required-cell configuration and firmware remain open. Charging must be disabled before ring power-off or loader entry when it relies on those readings.

## Sizing method

For N identical cells, nominal pack capacity is N * Ccell; voltage remains one-cell voltage. First estimate runtime from energy:

    runtime_hours ~= N * Ccell_Ah * Vnom * conversion_efficiency / average_load_W

For illustration only, three 150 mAh, 3.7 V cells contain about 1.67 Wh nominally. With an assumed 90% usable conversion factor, that corresponds to about 1.5 hours at 1 W average load or 3 hours at 0.5 W. These are not runtime predictions. Cutoff, aging, discharge rate and temperature affect usable energy.

Check peak current separately: the pack must support coincident ESP32 radio activity and the allowed simultaneous haptic outputs, including at low state of charge. Firmware mapping duty cycle determines average actuator energy. Cell count and charge current should follow those measurements and the selected cells' ratings.

## Sources inspected

- [TI BQ25186 datasheet](https://www.ti.com/lit/ds/symlink/bq25186.pdf): power path, charging, thermistor, modes, address and SYS register.
- [TI TPS63802](https://www.ti.com/product/TPS63802) and [datasheet](https://www.ti.com/lit/ds/symlink/tps63802.pdf): input/output range and specified current capability.
- [TI DRV2625 datasheet](https://www.ti.com/lit/ds/symlink/drv2625.pdf): supply range and I2C pin voltage constraint.
- [TI battery protector overview](https://www.ti.com/product-category/battery-management-ics/battery-protectors/overview.html): voltage, current and short-circuit protection functions.

Pack/interconnect arrangements above are engineering proposals for this device. None of these IC datasheets qualifies the as-yet-unselected distributed pouch pack.
