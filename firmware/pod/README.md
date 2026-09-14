# M2003 haptic pod

This application preserves the music robot's M2003 startup, UART ring transport conventions, application-to-loader mailbox, flash layout, image packager, and LDROM sources. The local application replaces all motor behavior with one local DRV2625 and an LRA.

`ROBOT_ROOT` is an explicit build input. The default points at the adjacent `bl4818-servo-M23_2` checkout used during development. A reproducible release should pin or vendor a reviewed revision before manufacturing.

The current DRV2625 values are conservative first-pass settings for the proposed VLV041235L (240 Hz, 1.8 Vrms rated, 1.85 Vrms operating maximum). Every actuator is auto-calibrated after power-up. The calibration values, thermal behavior, perceived mapping, and drive limit need bench validation before wear testing.

PB2 temperature conversion is not claimed in this first slice. Status reports mark temperature unavailable, and the ESP32 controller never enables charging.
