#ifndef HB_CRC_H
#define HB_CRC_H

#include <stddef.h>
#include <stdint.h>

uint16_t hb_crc16_ccitt(const uint8_t *data, size_t length);
uint8_t hb_crc8_dvb_s2(const uint8_t *data, size_t length);

#endif
