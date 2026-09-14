# Firmware bring-up console

The ESP32-C6 controller provides a native USB Serial/JTAG console for incremental pod and telemetry checks. This is a diagnostic interface, not evidence that the bracelet has been flashed or qualified.

## Safety boundary

- Use a current-limited bench supply for first power and keep the bracelet off-body.
- Charging remains disabled in this firmware.
- Bus and actuator commands latch manual mode and request all-stop before proceeding.
- A diagnostic pulse is limited to amplitude 64 and 250 ms. It is refreshed every 20 ms, followed by addressed stop and broadcast all-stop. The M2003 retains its independent 100 ms command watchdog.
- `hb flight` is the only command that releases manual mode. It is refused unless exactly eight pods are enumerated; fresh valid Backpack telemetry is still required before output.

## Connect

Build and flash the controller, then open its native USB serial port at 115200 baud. Run `help` for the ESP-IDF command list or `hb help` for the bracelet commands.

| Command | Result |
| --- | --- |
| `hb status` | Show manual/flight mode, ring state, enumerated count and telemetry age. |
| `hb telemetry` | Print the latest decoded pitch, roll and yaw in radians times 10000. |
| `hb manual` | Latch manual mode and request all-stop. |
| `hb flight` | Release manual mode only when eight pods are enumerated. |
| `hb stop` | Latch manual mode and request broadcast all-stop. |
| `hb ring restart` | Power-cycle the pod rail, wait through the LDROM window and enumerate one through eight pods. |
| `hb ring off` | Stop output, detach the UART and switch the pod rail off. |
| `hb pod status all` | Stop automatic output and read every enumerated driver's identity, state, status and calibration values. |
| `hb pod status 0` | Read one enumerated pod. |
| `hb pod pulse 0 24 80` | Drive pod 0 at RTP amplitude 24 for 80 ms, then stop. |

## Staged procedure

1. Flash one M2003 with the bracelet application and LDROM through ICE. Restore its UART links after programming.
2. Connect that pod as a complete one-pod ring return. Power the controller from a current-limited supply and run `hb ring restart`.
3. Confirm `hb status` reports one pod. Run `hb pod status 0`; require the expected DRV2625 chip ID, `ready` state, and no fault bits before applying RTP.
4. Begin with `hb pod pulse 0 8 40`. Increase amplitude and duration deliberately while observing rail current, LRA behavior and driver status. Do not increase the checked-in limits from perception alone.
5. Add pods one at a time, repeating enumeration and status checks. On the last satellite, verify JP1 is cut from 1-2 and bridged 2-3 before expecting the full return path.
6. With eight healthy pods, configure the Backpack MAC and Wi-Fi channel, verify `hb telemetry`, then use `hb flight` to allow the provisional mapping.
7. Exercise telemetry loss, ring interruption and pod-power restart while measuring the farthest-pod rail and UART return. Record actual startup and discharge timing before changing the hard-coded delays.

## Expected status fields

`chip_id`, `status`, `state`, `cal_comp`, `cal_bemf`, and `feedback` come directly from the pod's DRV2625 snapshot. Temperature is deliberately reported as unavailable until PB2 conversion and the selected thermistor curve are implemented.
