#include "backpack_rx.h"

#include <ctype.h>
#include <stddef.h>
#include <string.h>

#include "esp_check.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_now.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "nvs_flash.h"
#include "sdkconfig.h"

#include "hb_telemetry.h"

static const char *TAG = "backpack";
static uint8_t source_mac[ESP_NOW_ETH_ALEN];
static portMUX_TYPE latest_lock = portMUX_INITIALIZER_UNLOCKED;
static hb_attitude_t latest_attitude;
static int64_t latest_time_us;
static bool have_attitude;

static int hex_value(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    c = (char)tolower((unsigned char)c);
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

static bool parse_mac(const char *text, uint8_t mac[ESP_NOW_ETH_ALEN])
{
    size_t count = 0u;
    int high = -1;

    while (*text != '\0') {
        int value = hex_value(*text++);
        if (value < 0) {
            if (text[-1] == ':' || text[-1] == '-') continue;
            return false;
        }
        if (high < 0) {
            high = value;
        } else {
            if (count >= ESP_NOW_ETH_ALEN) return false;
            mac[count++] = (uint8_t)((high << 4) | value);
            high = -1;
        }
    }
    return count == ESP_NOW_ETH_ALEN && high < 0;
}

static bool mac_is_zero(const uint8_t mac[ESP_NOW_ETH_ALEN])
{
    size_t i;
    for (i = 0; i < ESP_NOW_ETH_ALEN; ++i)
        if (mac[i] != 0u) return false;
    return true;
}

static void receive_callback(const esp_now_recv_info_t *info,
                             const uint8_t *data, int data_length)
{
    const uint8_t *crsf;
    size_t crsf_length;
    hb_attitude_t parsed;

    if (info == NULL || data == NULL || data_length <= 0 ||
        memcmp(info->src_addr, source_mac, ESP_NOW_ETH_ALEN) != 0)
        return;
    if (!hb_msp_v2_payload(data, (size_t)data_length, HB_MSP_BACKPACK_CRSF_TLM,
                           &crsf, &crsf_length) ||
        !hb_crsf_parse_attitude(crsf, crsf_length, &parsed))
        return;

    portENTER_CRITICAL(&latest_lock);
    latest_attitude = parsed;
    latest_time_us = esp_timer_get_time();
    have_attitude = true;
    portEXIT_CRITICAL(&latest_lock);
}

esp_err_t hb_backpack_rx_init(void)
{
    wifi_init_config_t wifi_config = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t error;

    if (!parse_mac(CONFIG_HB_BACKPACK_SOURCE_MAC, source_mac)) {
        ESP_LOGE(TAG, "invalid HB_BACKPACK_SOURCE_MAC");
        return ESP_ERR_INVALID_ARG;
    }
    if (mac_is_zero(source_mac)) {
        ESP_LOGW(TAG, "Backpack input disabled: source MAC is all zeroes");
        return ESP_OK;
    }

    error = nvs_flash_init();
    if (error == ESP_ERR_NVS_NO_FREE_PAGES || error == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        error = nvs_flash_init();
    }
    ESP_RETURN_ON_ERROR(error, TAG, "NVS init");
    ESP_RETURN_ON_ERROR(esp_netif_init(), TAG, "netif init");
    error = esp_event_loop_create_default();
    if (error != ESP_OK && error != ESP_ERR_INVALID_STATE)
        return error;
    ESP_RETURN_ON_ERROR(esp_wifi_init(&wifi_config), TAG, "Wi-Fi init");
    ESP_RETURN_ON_ERROR(esp_wifi_set_storage(WIFI_STORAGE_RAM), TAG, "Wi-Fi storage");
    ESP_RETURN_ON_ERROR(esp_wifi_set_mode(WIFI_MODE_STA), TAG, "Wi-Fi mode");
    ESP_RETURN_ON_ERROR(esp_wifi_start(), TAG, "Wi-Fi start");
    ESP_RETURN_ON_ERROR(esp_wifi_set_ps(WIFI_PS_NONE), TAG, "Wi-Fi power save");
    ESP_RETURN_ON_ERROR(esp_wifi_set_channel(CONFIG_HB_BACKPACK_WIFI_CHANNEL,
                                              WIFI_SECOND_CHAN_NONE), TAG, "Wi-Fi channel");
    ESP_RETURN_ON_ERROR(esp_now_init(), TAG, "ESP-NOW init");
    ESP_RETURN_ON_ERROR(esp_now_register_recv_cb(receive_callback), TAG,
                        "ESP-NOW callback");
    ESP_LOGI(TAG, "accepting Backpack telemetry from %02x:%02x:%02x:%02x:%02x:%02x",
             source_mac[0], source_mac[1], source_mac[2], source_mac[3],
             source_mac[4], source_mac[5]);
    return ESP_OK;
}

bool hb_backpack_latest(hb_attitude_t *attitude, uint32_t *age_ms)
{
    bool valid;
    int64_t timestamp;

    if (attitude == NULL || age_ms == NULL)
        return false;
    portENTER_CRITICAL(&latest_lock);
    valid = have_attitude;
    *attitude = latest_attitude;
    timestamp = latest_time_us;
    portEXIT_CRITICAL(&latest_lock);
    if (!valid)
        return false;
    *age_ms = (uint32_t)((esp_timer_get_time() - timestamp) / 1000);
    return true;
}
