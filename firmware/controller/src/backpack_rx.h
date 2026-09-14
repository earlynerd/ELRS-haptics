#ifndef HB_BACKPACK_RX_H
#define HB_BACKPACK_RX_H

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "hb_telemetry.h"

esp_err_t hb_backpack_rx_init(void);
bool hb_backpack_latest(hb_attitude_t *attitude, uint32_t *age_ms);

#endif
