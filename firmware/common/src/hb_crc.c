#include "hb_crc.h"

uint16_t hb_crc16_ccitt(const uint8_t *data, size_t length)
{
    uint16_t crc = 0xFFFFu;
    size_t i;

    for (i = 0; i < length; ++i) {
        uint8_t bit;
        crc ^= (uint16_t)data[i] << 8;
        for (bit = 0; bit < 8u; ++bit) {
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u)
                                  : (uint16_t)(crc << 1);
        }
    }
    return crc;
}

uint8_t hb_crc8_dvb_s2(const uint8_t *data, size_t length)
{
    uint8_t crc = 0u;
    size_t i;

    for (i = 0; i < length; ++i) {
        uint8_t bit;
        crc ^= data[i];
        for (bit = 0; bit < 8u; ++bit)
            crc = (crc & 0x80u) ? (uint8_t)((crc << 1) ^ 0xD5u)
                                : (uint8_t)(crc << 1);
    }
    return crc;
}
