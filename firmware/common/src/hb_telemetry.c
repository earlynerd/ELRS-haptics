#include "hb_telemetry.h"

#include "hb_crc.h"

static int16_t read_i16_be(const uint8_t *data)
{
    return (int16_t)(((uint16_t)data[0] << 8) | data[1]);
}

int hb_msp_v2_payload(const uint8_t *frame, size_t frame_length,
                      uint16_t expected_function,
                      const uint8_t **payload, size_t *payload_length)
{
    uint16_t function;
    uint16_t length;
    uint8_t expected_crc;

    if (frame == NULL || payload == NULL || payload_length == NULL ||
        frame_length < 9u || frame[0] != '$' || frame[1] != 'X' ||
        frame[2] != '<')
        return 0;

    function = (uint16_t)frame[4] | ((uint16_t)frame[5] << 8);
    length = (uint16_t)frame[6] | ((uint16_t)frame[7] << 8);
    if (function != expected_function || frame_length != (size_t)length + 9u)
        return 0;
    expected_crc = hb_crc8_dvb_s2(&frame[3], (size_t)length + 5u);
    if (frame[8u + length] != expected_crc)
        return 0;

    *payload = &frame[8];
    *payload_length = length;
    return 1;
}

int hb_crsf_parse_attitude(const uint8_t *frame, size_t frame_length,
                           hb_attitude_t *attitude)
{
    size_t total;
    uint8_t crsf_length;
    uint8_t expected_crc;

    if (frame == NULL || attitude == NULL || frame_length < 10u)
        return 0;
    crsf_length = frame[1];
    total = (size_t)crsf_length + 2u;
    if (crsf_length < 2u || total != frame_length ||
        frame[2] != HB_CRSF_FRAMETYPE_ATTITUDE || crsf_length != 8u)
        return 0;
    expected_crc = hb_crc8_dvb_s2(&frame[2], (size_t)crsf_length - 1u);
    if (frame[frame_length - 1u] != expected_crc)
        return 0;

    attitude->pitch_rad_x10000 = read_i16_be(&frame[3]);
    attitude->roll_rad_x10000 = read_i16_be(&frame[5]);
    attitude->yaw_rad_x10000 = read_i16_be(&frame[7]);
    return 1;
}
