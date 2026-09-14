#include "hb_ring.h"

#include <string.h>

#include "hb_crc.h"

size_t hb_ring_encode(const uint8_t *payload, uint8_t payload_length,
                      uint8_t *frame, size_t frame_capacity)
{
    size_t total = (size_t)payload_length + 5u;
    uint16_t crc;

    if (payload == NULL || frame == NULL || payload_length == 0u ||
        payload_length > HB_RING_MAX_PAYLOAD || frame_capacity < total)
        return 0u;

    frame[0] = HB_RING_PREAMBLE_0;
    frame[1] = HB_RING_PREAMBLE_1;
    frame[2] = payload_length;
    memcpy(&frame[3], payload, payload_length);
    crc = hb_crc16_ccitt(&frame[2], (size_t)payload_length + 1u);
    frame[3u + payload_length] = (uint8_t)(crc >> 8);
    frame[4u + payload_length] = (uint8_t)crc;
    return total;
}

int hb_ring_decode_exact(const uint8_t *frame, size_t frame_length,
                         uint8_t *payload, uint8_t *payload_length)
{
    uint8_t length;
    uint16_t expected;
    uint16_t received;

    if (frame == NULL || payload_length == NULL || frame_length < 6u ||
        frame[0] != HB_RING_PREAMBLE_0 || frame[1] != HB_RING_PREAMBLE_1)
        return 0;
    length = frame[2];
    if (length == 0u || length > HB_RING_MAX_PAYLOAD ||
        frame_length != (size_t)length + 5u)
        return 0;
    received = (uint16_t)((uint16_t)frame[3u + length] << 8) |
               frame[4u + length];
    expected = hb_crc16_ccitt(&frame[2], (size_t)length + 1u);
    if (received != expected)
        return 0;
    if (payload != NULL)
        memcpy(payload, &frame[3], length);
    *payload_length = length;
    return 1;
}
