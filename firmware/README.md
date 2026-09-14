# Bracelet firmware

This directory contains the first firmware slice for one wrist:

- `common/` is portable C for ring framing, MSPv2/CRSF attitude decoding, and the configurable eight-pod attitude map.
- `controller/` is the ESP32-C6 ESP-IDF application. It receives ExpressLRS Backpack CRSF telemetry over ESP-NOW and masters the 250 kbaud pod ring.
- `pod/` is the M2003FC1AE application plus a build wrapper around the proven music-robot LDROM and support sources.
- `tests/` exercises the portable protocol core without hardware.

The checked-in defaults are intentionally safe. The charger enable remains low. Pod power starts off. Haptics are sent only after exactly eight applications enumerate and a configured Backpack sender supplies a fresh, valid attitude frame. Loss of telemetry or ring echo requests an all-stop.

This is build evidence, not flashed-hardware evidence. Rail timing, UART signal integrity, loader interception, DRV2625/LRA tuning, temperature conversion, charging policy, and the final wrist-direction map remain bench work.

## Build

Controller (PlatformIO, ESP-IDF):

```powershell
pio run --project-dir firmware/controller
```

Portable tests (CMake plus any desktop C compiler):

```powershell
cmake -S firmware/tests -B firmware/tests/build
cmake --build firmware/tests/build
ctest --test-dir firmware/tests/build --output-on-failure
```

Pod application and unchanged borrowed LDROM:

```powershell
make -C firmware/pod ROBOT_ROOT=C:/Users/mmsyl/Documents/bl4818-servo-M23_2 images
```

The M2003 build fails early if `ROBOT_ROOT` does not contain the expected support tree. This makes the current provenance visible rather than silently copying a second vendor BSP. Pin and image-layout details are in [protocol.md](protocol.md).
