#ifndef HB_BRINGUP_CONSOLE_H
#define HB_BRINGUP_CONSOLE_H

#include <stdbool.h>

#include "esp_err.h"

esp_err_t hb_bringup_console_start(void);
bool hb_bringup_console_manual_active(void);

#endif
