#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "hb_attitude_map.h"
#include "hb_crc.h"
#include "hb_ring.h"
#include "hb_telemetry.h"

static void test_ring_round_trip(void)
{
    const uint8_t payload[] = { HB_CMD_BROADCAST_RTP, 7u, 1u, 2u, 3u, 4u,
                                5u, 6u, 7u, 8u };
    uint8_t frame[HB_RING_MAX_FRAME];
    uint8_t decoded[HB_RING_MAX_PAYLOAD];
    uint8_t decoded_length = 0u;
    size_t length = hb_ring_encode(payload, (uint8_t)sizeof(payload),
                                   frame, sizeof(frame));
    assert(length == sizeof(payload) + 5u);
    assert(hb_ring_decode_exact(frame, length, decoded, &decoded_length));
    assert(decoded_length == sizeof(payload));
    assert(memcmp(payload, decoded, sizeof(payload)) == 0);
    frame[length - 1u] ^= 1u;
    assert(!hb_ring_decode_exact(frame, length, decoded, &decoded_length));
}

static void test_msp_crsf_attitude(void)
{
    uint8_t crsf[] = { 0xEAu, 8u, HB_CRSF_FRAMETYPE_ATTITUDE,
                       0x04u, 0xD2u, 0xFBu, 0x2Eu, 0x00u, 0x2Au, 0u };
    uint8_t msp[sizeof(crsf) + 9u] = { '$', 'X', '<', 0u, 0x11u, 0u,
                                      (uint8_t)sizeof(crsf), 0u };
    const uint8_t *payload = NULL;
    size_t payload_length = 0u;
    hb_attitude_t attitude;

    crsf[sizeof(crsf) - 1u] = hb_crc8_dvb_s2(&crsf[2], sizeof(crsf) - 3u);
    memcpy(&msp[8], crsf, sizeof(crsf));
    msp[sizeof(msp) - 1u] = hb_crc8_dvb_s2(&msp[3], sizeof(msp) - 4u);
    assert(hb_msp_v2_payload(msp, sizeof(msp), HB_MSP_BACKPACK_CRSF_TLM,
                             &payload, &payload_length));
    assert(hb_crsf_parse_attitude(payload, payload_length, &attitude));
    assert(attitude.pitch_rad_x10000 == 1234);
    assert(attitude.roll_rad_x10000 == -1234);
    assert(attitude.yaw_rad_x10000 == 42);
    msp[sizeof(msp) - 1u] ^= 1u;
    assert(!hb_msp_v2_payload(msp, sizeof(msp), HB_MSP_BACKPACK_CRSF_TLM,
                              &payload, &payload_length));
}

static void test_attitude_map(void)
{
    hb_attitude_t attitude = { 3500, -3500, 0 };
    uint8_t amplitudes[HB_RING_POD_COUNT];
    hb_attitude_to_amplitudes(&hb_attitude_map_bringup, &attitude, amplitudes);
    assert(amplitudes[0] == 96u);
    assert(amplitudes[4] == 0u);
    assert(amplitudes[2] == 0u);
    assert(amplitudes[6] == 96u);
    assert(amplitudes[3] == 0u && amplitudes[7] == 0u);
}

int main(void)
{
    test_ring_round_trip();
    test_msp_crsf_attitude();
    test_attitude_map();
    puts("haptic bracelet core tests passed");
    return 0;
}
