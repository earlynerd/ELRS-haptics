#ifndef HB_RING_MASTER_H
#define HB_RING_MASTER_H

#include <stdbool.h>
#include <stdint.h>

#include "hb_ring.h"

typedef struct {
    uint8_t chip_id;
    uint8_t driver_status;
    uint8_t driver_state;
    uint8_t calibration_compensation;
    uint8_t calibration_bemf;
    uint8_t feedback;
    bool temperature_available;
    int16_t temperature_raw;
} hb_pod_status_t;

bool hb_ring_master_start(void);
bool hb_ring_master_is_started(void);
bool hb_ring_master_flight_ready(void);
uint8_t hb_ring_master_pod_count(void);
bool hb_ring_master_send_haptics(uint8_t sequence,
                                 const uint8_t amplitudes[HB_RING_POD_COUNT]);
bool hb_ring_master_all_stop(void);
bool hb_ring_master_query_status(uint8_t address, hb_pod_status_t *status);
bool hb_ring_master_set_rtp(uint8_t address, uint8_t amplitude);
bool hb_ring_master_stop_pod(uint8_t address);
void hb_ring_master_shutdown(void);

#endif
