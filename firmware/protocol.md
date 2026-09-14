# Firmware interfaces

## Pod ring

The bracelet preserves the music robot's 250000 baud, 8N1, point-to-point ring and frame format:

```
A5 5A LEN PAYLOAD[LEN] CRC16_HI CRC16_LO
```

CRC-16/CCITT uses polynomial `0x1021` and initial value `0xFFFF` over `LEN` and `PAYLOAD`. Enumeration also remains compatible: `ENTER_SF=0x01`, `ENTER_CT=0x02`, and `SET_ADDRESS=0x03`. In store-and-forward mode an unassigned pod accepts the incoming counter and forwards the incremented value. Exactly eight pods are required before haptic output is enabled.

Diagnostic enumeration accepts a physically complete partial ring of one through eight pods so boards can be brought up incrementally. This does not weaken flight mode: broadcast attitude haptics and `hb flight` still require exactly eight. Addressed diagnostic transactions scan past the command frame returning through the cut-through ring and wait for the matching status or acknowledgement frame.

Bracelet-only application commands do not reuse the robot's motor-duty opcode:

| Command | Value | Payload after command |
| --- | ---: | --- |
| Broadcast RTP | `0x11` | sequence, amplitudes for pod 0 through 7 |
| All stop | `0x12` | none |
| Addressed | `0x20 + address` | subcommand and arguments |

Addressed subcommands are `SET_RTP=0x01`, `STOP=0x02`, `QUERY_STATUS=0x03`, and `ENTER_BOOTLOADER=0x1B`. Replies retain the robot ranges: status `0x40 + address`, acknowledgement `0x50 + address`. A pod stops locally if no RTP broadcast or addressed update arrives for 100 ms. The controller sends at 50 Hz and treats attitude older than 250 ms as stale.

## ExpressLRS Backpack input

The controller accepts MSPv2 function `0x0011` (`MSP_ELRS_BACKPACK_CRSF_TLM`) only from the six-byte source MAC configured at build time. Its payload must be a valid CRSF attitude frame (`0x1E`) with a valid CRSF CRC. Pitch, roll, and yaw are signed big-endian radians multiplied by 10000.

Configure `HB_BACKPACK_SOURCE_MAC` through `menuconfig` or `sdkconfig.defaults`. All-zero disables radio input. The starter attitude map is a transparent bring-up map, not the final perceptual mapping: opposing pod pairs encode signed pitch, roll, and yaw; pods 3 and 7 are unused. The matrix, deadband, and full-scale values live in `common/src/hb_attitude_map.c` and should be tuned on a safe current-limited bench setup.

## M2003 image layout

The pod build reuses the robot project's startup, vendor support, application-to-loader mailbox, linker geometry, packaging tool, and LDROM sources without changing their wire format:

- application below `0x00007A00`
- manifest page at `0x00007A00`
- persistence reservation at `0x00007C00`
- 4 KiB LDROM at `0x00100000`
- 16-byte mailbox at `0x20000FF0`
- 32-byte update write chunks and the existing manifest commit flow

Only the bracelet application is new. Never program the music robot motor application onto a bracelet pod.

## Native USB bring-up console

The controller exposes one `hb` command family through ESP32-C6 native USB Serial/JTAG. `hb status` and `hb telemetry` are read-only. `hb manual`, `hb stop`, `hb ring ...`, and `hb pod ...` latch manual mode and suppress automatic attitude output until `hb flight` is explicitly accepted.

Individual diagnostic pulses accept pod addresses 0 through 7, amplitudes 1 through 64, and durations 10 through 250 ms. The controller refreshes the addressed RTP command every 20 ms, sends addressed stop plus broadcast all-stop at completion, and retains the pod's independent 100 ms command watchdog as the final stop path.

See [BRINGUP.md](BRINGUP.md) for the command list and staged bench procedure.
