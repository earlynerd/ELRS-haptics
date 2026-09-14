#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "backpack_rx.h"
#include "board.h"
#include "bringup_console.h"
#include "hb_attitude_map.h"
#include "ring_master.h"

#define CONTROL_PERIOD_MS 20u
#define ATTITUDE_STALE_MS 250u

static const char *TAG = "bracelet";

static void set_led(bool red, bool green, bool blue)
{
    /* Common-anode LED: GPIO low turns a channel on. */
    gpio_set_level(HB_PIN_LED_RED, red ? 0 : 1);
    gpio_set_level(HB_PIN_LED_GREEN, green ? 0 : 1);
    gpio_set_level(HB_PIN_LED_BLUE, blue ? 0 : 1);
}

static void safe_main_io_init(void)
{
    const gpio_config_t output_config = {
        .pin_bit_mask = (1ULL << HB_PIN_CHG_ALLOW) |
                        (1ULL << HB_PIN_LED_RED) |
                        (1ULL << HB_PIN_LED_GREEN) |
                        (1ULL << HB_PIN_LED_BLUE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&output_config));
    gpio_set_level(HB_PIN_CHG_ALLOW, 0); /* Charging is not enabled in v0.1. */
    set_led(false, false, false);
}

void app_main(void)
{
    bool ring_online;
    bool output_active = false;
    uint8_t sequence = 0u;

    safe_main_io_init();
    set_led(false, false, true);
    ring_online = hb_ring_master_start();
    if (hb_backpack_rx_init() != ESP_OK)
        ESP_LOGE(TAG, "Backpack initialization failed");
    if (hb_bringup_console_start() != ESP_OK)
        ESP_LOGE(TAG, "USB bring-up console initialization failed");

    if (!ring_online) {
        set_led(true, false, false);
        ESP_LOGE(TAG, "safe fault: pod rail disabled");
    } else {
        set_led(false, false, true);
    }

    for (;;) {
        hb_attitude_t attitude;
        uint32_t age_ms = UINT32_MAX;
        bool fresh;

        if (hb_bringup_console_manual_active()) {
            if (output_active) {
                (void)hb_ring_master_all_stop();
                output_active = false;
            }
            set_led(false, false, true);
            vTaskDelay(pdMS_TO_TICKS(CONTROL_PERIOD_MS));
            continue;
        }

        fresh = hb_ring_master_flight_ready() &&
                      hb_backpack_latest(&attitude, &age_ms) &&
                      age_ms <= ATTITUDE_STALE_MS;

        if (fresh) {
            uint8_t amplitudes[HB_RING_POD_COUNT];
            hb_attitude_to_amplitudes(&hb_attitude_map_bringup, &attitude,
                                      amplitudes);
            if (!hb_ring_master_send_haptics(sequence++, amplitudes)) {
                ESP_LOGE(TAG, "ring echo lost; powering pods down");
                hb_ring_master_shutdown();
                output_active = false;
                set_led(true, false, false);
            } else {
                output_active = true;
                set_led(false, true, false);
            }
        } else if (output_active) {
            (void)hb_ring_master_all_stop();
            output_active = false;
            set_led(false, false, true);
        }
        vTaskDelay(pdMS_TO_TICKS(CONTROL_PERIOD_MS));
    }
}
