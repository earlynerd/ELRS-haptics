#ifndef HB_RING_H
#define HB_RING_H

#include <stddef.h>
#include <stdint.h>

#define HB_RING_PREAMBLE_0       0xA5u
#define HB_RING_PREAMBLE_1       0x5Au
#define HB_RING_MAX_PAYLOAD      64u
#define HB_RING_MAX_FRAME        (2u + 1u + HB_RING_MAX_PAYLOAD + 2u)
#define HB_RING_POD_COUNT        8u

#define HB_CMD_ENTER_SF          0x01u
#define HB_CMD_ENTER_CT          0x02u
#define HB_CMD_SET_ADDRESS       0x03u
#define HB_CMD_BROADCAST_RTP     0x11u
#define HB_CMD_ALL_STOP          0x12u
#define HB_CMD_ADDR_BASE         0x20u
#define HB_CMD_STATUS_BASE       0x40u
#define HB_CMD_ACK_BASE          0x50u

#define HB_SUBCMD_SET_RTP        0x01u
#define HB_SUBCMD_STOP           0x02u
#define HB_SUBCMD_QUERY_STATUS   0x03u
#define HB_SUBCMD_ENTER_LOADER   0x1Bu

size_t hb_ring_encode(const uint8_t *payload, uint8_t payload_length,
                      uint8_t *frame, size_t frame_capacity);
int hb_ring_decode_exact(const uint8_t *frame, size_t frame_length,
                         uint8_t *payload, uint8_t *payload_length);

#endif
