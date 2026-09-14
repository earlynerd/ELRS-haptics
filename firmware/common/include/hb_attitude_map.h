#ifndef HB_ATTITUDE_MAP_H
#define HB_ATTITUDE_MAP_H

#include <stdint.h>

#include "hb_ring.h"
#include "hb_telemetry.h"

typedef struct {
    int16_t weights_q15[HB_RING_POD_COUNT][3];
    uint16_t deadband_rad_x10000;
    uint16_t full_scale_rad_x10000;
    uint8_t maximum_amplitude;
} hb_attitude_map_config_t;

extern const hb_attitude_map_config_t hb_attitude_map_bringup;

void hb_attitude_to_amplitudes(const hb_attitude_map_config_t *config,
                               const hb_attitude_t *attitude,
                               uint8_t amplitudes[HB_RING_POD_COUNT]);

#endif
