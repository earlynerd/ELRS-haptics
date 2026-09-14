#include "hb_attitude_map.h"

#include <stddef.h>

#define Q15_ONE 32767

/* Bring-up geometry only: opposing pairs represent signed pitch, roll, yaw. */
const hb_attitude_map_config_t hb_attitude_map_bringup = {
    {
        { Q15_ONE, 0, 0 },
        { 0, 0, Q15_ONE },
        { 0, Q15_ONE, 0 },
        { 0, 0, 0 },
        { -Q15_ONE, 0, 0 },
        { 0, 0, -Q15_ONE },
        { 0, -Q15_ONE, 0 },
        { 0, 0, 0 }
    },
    350u,  /* 0.035 rad, about 2 degrees */
    3500u, /* 0.35 rad, about 20 degrees */
    96u
};

static int32_t normalize_axis(int16_t value, uint16_t deadband, uint16_t full_scale)
{
    int32_t sign = 1;
    int32_t magnitude = value;
    uint32_t span;

    if (magnitude < 0) {
        sign = -1;
        magnitude = -magnitude;
    }
    if ((uint32_t)magnitude <= deadband || full_scale <= deadband)
        return 0;
    if ((uint32_t)magnitude >= full_scale)
        return sign * Q15_ONE;
    span = (uint32_t)full_scale - deadband;
    return sign * (int32_t)(((uint32_t)magnitude - deadband) * Q15_ONE / span);
}

void hb_attitude_to_amplitudes(const hb_attitude_map_config_t *config,
                               const hb_attitude_t *attitude,
                               uint8_t amplitudes[HB_RING_POD_COUNT])
{
    int32_t axes[3];
    size_t pod;

    if (config == NULL || attitude == NULL || amplitudes == NULL)
        return;
    axes[0] = normalize_axis(attitude->pitch_rad_x10000,
                             config->deadband_rad_x10000,
                             config->full_scale_rad_x10000);
    axes[1] = normalize_axis(attitude->roll_rad_x10000,
                             config->deadband_rad_x10000,
                             config->full_scale_rad_x10000);
    axes[2] = normalize_axis(attitude->yaw_rad_x10000,
                             config->deadband_rad_x10000,
                             config->full_scale_rad_x10000);

    for (pod = 0; pod < HB_RING_POD_COUNT; ++pod) {
        int64_t mixed = 0;
        size_t axis;
        for (axis = 0; axis < 3u; ++axis)
            mixed += (int64_t)config->weights_q15[pod][axis] * axes[axis];
        mixed /= Q15_ONE;
        if (mixed <= 0) {
            amplitudes[pod] = 0u;
        } else {
            uint32_t scaled = (uint32_t)mixed * config->maximum_amplitude / Q15_ONE;
            amplitudes[pod] = (uint8_t)((scaled > config->maximum_amplitude)
                                             ? config->maximum_amplitude : scaled);
        }
    }
}
