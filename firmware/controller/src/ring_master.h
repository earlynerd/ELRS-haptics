#ifndef HB_RING_MASTER_H
#define HB_RING_MASTER_H

#include <stdbool.h>
#include <stdint.h>

#include "hb_ring.h"

bool hb_ring_master_start(void);
bool hb_ring_master_send_haptics(uint8_t sequence,
                                 const uint8_t amplitudes[HB_RING_POD_COUNT]);
bool hb_ring_master_all_stop(void);
void hb_ring_master_shutdown(void);

#endif
