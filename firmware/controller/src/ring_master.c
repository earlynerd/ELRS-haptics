#include "ring_master.h"

#include <stddef.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

#include "board.h"

#define CONTROL_REPLY_TIMEOUT_MS 15u
#define DIAGNOSTIC_REPLY_TIMEOUT_MS 200u

typedef bool (*payload_matcher_t)(const uint8_t *payload, uint8_t length,
                                  const void *context);

typedef struct {
    const uint8_t *payload;
    uint8_t length;
} exact_match_t;

typedef struct {
    uint8_t address;
    uint8_t subcommand;
} addressed_match_t;

static const char *TAG = "ring";
static const uart_port_t RING_UART = UART_NUM_1;
static StaticSemaphore_t ring_mutex_storage;
static SemaphoreHandle_t ring_mutex;
static bool uart_installed;
static bool ring_started;
static uint8_t enumerated_pods;

static void ensure_mutex(void)
{
    if (ring_mutex == NULL)
        ring_mutex = xSemaphoreCreateMutexStatic(&ring_mutex_storage);
}

static void lock_ring(void)
{
    ensure_mutex();
    (void)xSemaphoreTake(ring_mutex, portMAX_DELAY);
}

static void unlock_ring(void)
{
    (void)xSemaphoreGive(ring_mutex);
}

static bool receive_matching_locked(payload_matcher_t matcher,
                                    const void *context,
                                    uint8_t *matched_payload,
                                    uint8_t *matched_length,
                                    uint32_t timeout_ms)
{
    hb_ring_decoder_t decoder;
    uint8_t bytes[32];
    uint8_t payload[HB_RING_MAX_PAYLOAD];
    uint8_t payload_length = 0u;
    int64_t deadline_us = esp_timer_get_time() + (int64_t)timeout_ms * 1000;

    hb_ring_decoder_init(&decoder);
    while (esp_timer_get_time() < deadline_us) {
        int64_t remaining_us = deadline_us - esp_timer_get_time();
        uint32_t remaining_ms = (uint32_t)((remaining_us + 999) / 1000);
        TickType_t wait_ticks = pdMS_TO_TICKS(remaining_ms);
        int received;
        int i;

        if (wait_ticks == 0u)
            wait_ticks = 1u;
        received = uart_read_bytes(RING_UART, bytes, sizeof(bytes), wait_ticks);
        if (received < 0)
            return false;
        for (i = 0; i < received; ++i) {
            if (hb_ring_decoder_push(&decoder, bytes[i], payload,
                                     &payload_length) &&
                matcher(payload, payload_length, context)) {
                if (matched_payload != NULL)
                    memcpy(matched_payload, payload, payload_length);
                if (matched_length != NULL)
                    *matched_length = payload_length;
                return true;
            }
        }
    }
    return false;
}

static bool send_locked(const uint8_t *payload, uint8_t length)
{
    uint8_t frame[HB_RING_MAX_FRAME];
    size_t frame_length = hb_ring_encode(payload, length, frame, sizeof(frame));

    if (frame_length == 0u)
        return false;
    uart_flush_input(RING_UART);
    return uart_write_bytes(RING_UART, frame, frame_length) == (int)frame_length &&
           uart_wait_tx_done(RING_UART, pdMS_TO_TICKS(10)) == ESP_OK;
}

static bool match_exact(const uint8_t *payload, uint8_t length,
                        const void *context)
{
    const exact_match_t *expected = context;
    return length == expected->length &&
           memcmp(payload, expected->payload, length) == 0;
}

static bool match_count(const uint8_t *payload, uint8_t length,
                        const void *context)
{
    (void)context;
    return length == 2u && payload[0] == HB_CMD_SET_ADDRESS &&
           payload[1] > 0u && payload[1] <= HB_RING_POD_COUNT;
}

static bool match_status(const uint8_t *payload, uint8_t length,
                         const void *context)
{
    const addressed_match_t *expected = context;
    return length == 9u &&
           payload[0] == (uint8_t)(HB_CMD_STATUS_BASE | expected->address);
}

static bool match_ack(const uint8_t *payload, uint8_t length,
                      const void *context)
{
    const addressed_match_t *expected = context;
    return length == 3u &&
           payload[0] == (uint8_t)(HB_CMD_ACK_BASE | expected->address) &&
           payload[1] == expected->subcommand;
}

static bool send_and_match_locked(const uint8_t *payload, uint8_t length,
                                  payload_matcher_t matcher,
                                  const void *context,
                                  uint8_t *matched_payload,
                                  uint8_t *matched_length,
                                  uint32_t timeout_ms)
{
    return send_locked(payload, length) &&
           receive_matching_locked(matcher, context, matched_payload,
                                   matched_length, timeout_ms);
}

static bool echo_command_locked(const uint8_t *payload, uint8_t length,
                                uint32_t timeout_ms)
{
    const exact_match_t expected = { payload, length };
    return send_and_match_locked(payload, length, match_exact, &expected,
                                 NULL, NULL, timeout_ms);
}

static bool enumerate_pods_locked(uint8_t *count)
{
    const uint8_t enter_sf[] = { HB_CMD_ENTER_SF };
    const uint8_t assign[] = { HB_CMD_SET_ADDRESS, 0u };
    const uint8_t enter_ct[] = { HB_CMD_ENTER_CT };
    uint8_t reply[HB_RING_MAX_PAYLOAD];
    uint8_t reply_length = 0u;

    if (!echo_command_locked(enter_sf, sizeof(enter_sf),
                             DIAGNOSTIC_REPLY_TIMEOUT_MS))
        return false;
    if (!send_and_match_locked(assign, sizeof(assign), match_count, NULL,
                               reply, &reply_length,
                               DIAGNOSTIC_REPLY_TIMEOUT_MS))
        return false;
    if (!echo_command_locked(enter_ct, sizeof(enter_ct),
                             DIAGNOSTIC_REPLY_TIMEOUT_MS))
        return false;
    *count = reply[1];
    ESP_LOGI(TAG, "enumerated %u pod%s", *count, *count == 1u ? "" : "s");
    return true;
}

static void shutdown_locked(void)
{
    if (ring_started) {
        const uint8_t stop[] = { HB_CMD_ALL_STOP };
        (void)echo_command_locked(stop, sizeof(stop), CONTROL_REPLY_TIMEOUT_MS);
    }
    ring_started = false;
    enumerated_pods = 0u;
    if (uart_installed) {
        (void)uart_wait_tx_done(RING_UART, pdMS_TO_TICKS(20));
        (void)uart_driver_delete(RING_UART);
        uart_installed = false;
    }
    (void)gpio_set_direction(HB_PIN_RING_TX, GPIO_MODE_OUTPUT);
    (void)gpio_set_level(HB_PIN_RING_TX, 0);
    (void)gpio_set_direction(HB_PIN_RING_RX, GPIO_MODE_INPUT);
    (void)gpio_pulldown_dis(HB_PIN_RING_RX);
    (void)gpio_pullup_dis(HB_PIN_RING_RX);
    (void)gpio_set_level(HB_PIN_POD_POWER_ON, 0);
}

bool hb_ring_master_start(void)
{
    const gpio_config_t power_config = {
        .pin_bit_mask = 1ULL << HB_PIN_POD_POWER_ON,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    const gpio_config_t off_uart_config = {
        .pin_bit_mask = (1ULL << HB_PIN_RING_TX) | (1ULL << HB_PIN_RING_RX),
        .mode = GPIO_MODE_INPUT_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    const uart_config_t uart_config = {
        .baud_rate = HB_RING_UART_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT
    };
    bool ok = false;

    lock_ring();
    if (uart_installed || ring_started)
        shutdown_locked();
    if (gpio_config(&power_config) != ESP_OK ||
        gpio_config(&off_uart_config) != ESP_OK)
        goto done;
    gpio_set_level(HB_PIN_RING_TX, 0);
    gpio_set_direction(HB_PIN_RING_RX, GPIO_MODE_INPUT);
    gpio_set_level(HB_PIN_POD_POWER_ON, 0);
    vTaskDelay(pdMS_TO_TICKS(100));

    gpio_set_level(HB_PIN_POD_POWER_ON, 1);
    vTaskDelay(pdMS_TO_TICKS(HB_POD_STARTUP_SETTLE_MS));
    if (uart_param_config(RING_UART, &uart_config) != ESP_OK ||
        uart_set_pin(RING_UART, HB_PIN_RING_TX, HB_PIN_RING_RX,
                     UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE) != ESP_OK ||
        uart_driver_install(RING_UART, 256, 256, 0, NULL, 0) != ESP_OK)
        goto done;
    uart_installed = true;

    /* Normal boot intentionally lets the LDROM interception window expire. */
    vTaskDelay(pdMS_TO_TICKS(HB_LDROM_WINDOW_MS));
    ring_started = enumerate_pods_locked(&enumerated_pods);
    ok = ring_started;
    if (!ring_started)
        ESP_LOGE(TAG, "pod enumeration failed");

done:
    if (!ok)
        shutdown_locked();
    unlock_ring();
    return ok;
}

bool hb_ring_master_is_started(void)
{
    bool started;
    lock_ring();
    started = ring_started;
    unlock_ring();
    return started;
}

bool hb_ring_master_flight_ready(void)
{
    bool ready;
    lock_ring();
    ready = ring_started && enumerated_pods == HB_RING_POD_COUNT;
    unlock_ring();
    return ready;
}

uint8_t hb_ring_master_pod_count(void)
{
    uint8_t count;
    lock_ring();
    count = enumerated_pods;
    unlock_ring();
    return count;
}

bool hb_ring_master_send_haptics(uint8_t sequence,
                                 const uint8_t amplitudes[HB_RING_POD_COUNT])
{
    uint8_t payload[2u + HB_RING_POD_COUNT];
    bool ok = false;

    lock_ring();
    if (ring_started && enumerated_pods == HB_RING_POD_COUNT &&
        amplitudes != NULL) {
        payload[0] = HB_CMD_BROADCAST_RTP;
        payload[1] = sequence;
        memcpy(&payload[2], amplitudes, HB_RING_POD_COUNT);
        ok = echo_command_locked(payload, sizeof(payload),
                                 CONTROL_REPLY_TIMEOUT_MS);
    }
    unlock_ring();
    return ok;
}

bool hb_ring_master_all_stop(void)
{
    const uint8_t payload[] = { HB_CMD_ALL_STOP };
    bool ok;

    lock_ring();
    ok = ring_started && echo_command_locked(payload, sizeof(payload),
                                             CONTROL_REPLY_TIMEOUT_MS);
    unlock_ring();
    return ok;
}

bool hb_ring_master_query_status(uint8_t address, hb_pod_status_t *status)
{
    uint8_t command[2];
    uint8_t reply[HB_RING_MAX_PAYLOAD];
    uint8_t reply_length = 0u;
    addressed_match_t expected = { address, HB_SUBCMD_QUERY_STATUS };
    bool ok = false;

    if (status == NULL)
        return false;
    lock_ring();
    if (!ring_started || address >= enumerated_pods)
        goto done;
    command[0] = (uint8_t)(HB_CMD_ADDR_BASE | address);
    command[1] = HB_SUBCMD_QUERY_STATUS;
    if (!send_and_match_locked(command, sizeof(command), match_status, &expected,
                               reply, &reply_length,
                               DIAGNOSTIC_REPLY_TIMEOUT_MS))
        goto done;
    status->chip_id = reply[1];
    status->driver_status = reply[2];
    status->driver_state = reply[3];
    status->calibration_compensation = reply[4];
    status->calibration_bemf = reply[5];
    status->feedback = reply[6];
    status->temperature_available = reply[7] != 0xFFu || reply[8] != 0xFFu;
    status->temperature_raw = (int16_t)(((uint16_t)reply[7] << 8) | reply[8]);
    ok = true;

done:
    unlock_ring();
    return ok;
}

static bool addressed_ack_command(uint8_t address, uint8_t subcommand,
                                  const uint8_t *arguments,
                                  uint8_t argument_length)
{
    uint8_t command[3];
    uint8_t reply[HB_RING_MAX_PAYLOAD];
    uint8_t reply_length = 0u;
    addressed_match_t expected = { address, subcommand };
    bool ok = false;

    if (argument_length > 1u)
        return false;
    lock_ring();
    if (!ring_started || address >= enumerated_pods)
        goto done;
    command[0] = (uint8_t)(HB_CMD_ADDR_BASE | address);
    command[1] = subcommand;
    if (argument_length != 0u)
        command[2] = arguments[0];
    if (!send_and_match_locked(command, (uint8_t)(2u + argument_length),
                               match_ack, &expected, reply, &reply_length,
                               DIAGNOSTIC_REPLY_TIMEOUT_MS))
        goto done;
    ok = reply[2] == 0u;

done:
    unlock_ring();
    return ok;
}

bool hb_ring_master_set_rtp(uint8_t address, uint8_t amplitude)
{
    if (amplitude > 127u)
        return false;
    return addressed_ack_command(address, HB_SUBCMD_SET_RTP, &amplitude, 1u);
}

bool hb_ring_master_stop_pod(uint8_t address)
{
    return addressed_ack_command(address, HB_SUBCMD_STOP, NULL, 0u);
}

void hb_ring_master_shutdown(void)
{
    lock_ring();
    shutdown_locked();
    unlock_ring();
}
