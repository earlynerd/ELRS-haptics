#ifndef HB_TELEMETRY_H
#define HB_TELEMETRY_H

#include <stddef.h>
#include <stdint.h>

#define HB_MSP_BACKPACK_CRSF_TLM 0x0011u
#define HB_CRSF_FRAMETYPE_ATTITUDE 0x1Eu

typedef struct {
    int16_t pitch_rad_x10000;
    int16_t roll_rad_x10000;
    int16_t yaw_rad_x10000;
} hb_attitude_t;

int hb_msp_v2_payload(const uint8_t *frame, size_t frame_length,
                      uint16_t expected_function,
                      const uint8_t **payload, size_t *payload_length);
int hb_crsf_parse_attitude(const uint8_t *frame, size_t frame_length,
                           hb_attitude_t *attitude);

#endif
