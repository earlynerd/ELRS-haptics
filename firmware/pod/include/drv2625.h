#ifndef HB_DRV2625_H
#define HB_DRV2625_H

#include <stdint.h>

typedef enum {
    DRV2625_STATE_FAULT = 0,
    DRV2625_STATE_CALIBRATING,
    DRV2625_STATE_READY,
    DRV2625_STATE_PLAYING,
    DRV2625_STATE_STOPPING
} drv2625_state_t;

typedef struct {
    uint8_t chip_id;
    uint8_t status;
    uint8_t cal_comp;
    uint8_t cal_bemf;
    uint8_t feedback;
    drv2625_state_t state;
} drv2625_snapshot_t;

void drv2625_init(uint32_t now_ms);
void drv2625_poll(uint32_t now_ms);
uint8_t drv2625_set_rtp(uint8_t amplitude, uint32_t now_ms);
void drv2625_stop(uint32_t now_ms);
void drv2625_get_snapshot(drv2625_snapshot_t *snapshot);

#endif
