#include "ring_master.h"

#include <string.h>

#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "board.h"

static const char *TAG = "ring";
static const uart_port_t RING_UART = UART_NUM_1;
static bool uart_installed;
static bool ring_started;

static bool exchange(const uint8_t *out_payload, uint8_t out_length,
                     uint8_t *in_payload, uint8_t *in_length)
{
    uint8_t tx[HB_RING_MAX_FRAME];
    uint8_t rx[HB_RING_MAX_FRAME];
    size_t tx_length = hb_ring_encode(out_payload, out_length, tx, sizeof(tx));
    int received;

    if (tx_length == 0u)
        return false;
    uart_flush_input(RING_UART);
    if (uart_write_bytes(RING_UART, tx, tx_length) != (int)tx_length ||
        uart_wait_tx_done(RING_UART, pdMS_TO_TICKS(10)) != ESP_OK)
        return false;
    received = uart_read_bytes(RING_UART, rx, sizeof(rx), pdMS_TO_TICKS(15));
    return received > 0 && hb_ring_decode_exact(rx, (size_t)received,
                                                in_payload, in_length);
}

static bool echo_command(const uint8_t *payload, uint8_t length)
{
    uint8_t reply[HB_RING_MAX_PAYLOAD];
    uint8_t reply_length = 0u;
    return exchange(payload, length, reply, &reply_length) &&
           reply_length == length && memcmp(reply, payload, length) == 0;
}

static bool enumerate_pods(void)
{
    const uint8_t enter_sf[] = { HB_CMD_ENTER_SF };
    const uint8_t assign[] = { HB_CMD_SET_ADDRESS, 0u };
    const uint8_t enter_ct[] = { HB_CMD_ENTER_CT };
    uint8_t reply[HB_RING_MAX_PAYLOAD];
    uint8_t reply_length = 0u;

    if (!echo_command(enter_sf, sizeof(enter_sf)))
        return false;
    if (!exchange(assign, sizeof(assign), reply, &reply_length) ||
        reply_length != 2u || reply[0] != HB_CMD_SET_ADDRESS ||
        reply[1] != HB_RING_POD_COUNT)
        return false;
    if (!echo_command(enter_ct, sizeof(enter_ct)))
        return false;
    ESP_LOGI(TAG, "enumerated %u pods", HB_RING_POD_COUNT);
    return true;
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

    ESP_ERROR_CHECK(gpio_config(&power_config));
    ESP_ERROR_CHECK(gpio_config(&off_uart_config));
    gpio_set_level(HB_PIN_RING_TX, 0);
    gpio_set_direction(HB_PIN_RING_RX, GPIO_MODE_INPUT);
    gpio_set_level(HB_PIN_POD_POWER_ON, 0);
    vTaskDelay(pdMS_TO_TICKS(100));

    gpio_set_level(HB_PIN_POD_POWER_ON, 1);
    vTaskDelay(pdMS_TO_TICKS(HB_POD_STARTUP_SETTLE_MS));
    ESP_ERROR_CHECK(uart_param_config(RING_UART, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(RING_UART, HB_PIN_RING_TX, HB_PIN_RING_RX,
                                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_ERROR_CHECK(uart_driver_install(RING_UART, 256, 256, 0, NULL, 0));
    uart_installed = true;

    /* Normal boot intentionally lets the LDROM interception window expire. */
    vTaskDelay(pdMS_TO_TICKS(HB_LDROM_WINDOW_MS));
    ring_started = enumerate_pods();
    if (!ring_started) {
        ESP_LOGE(TAG, "pod enumeration failed");
        hb_ring_master_shutdown();
    }
    return ring_started;
}

bool hb_ring_master_send_haptics(uint8_t sequence,
                                 const uint8_t amplitudes[HB_RING_POD_COUNT])
{
    uint8_t payload[2u + HB_RING_POD_COUNT];
    if (!ring_started || amplitudes == NULL)
        return false;
    payload[0] = HB_CMD_BROADCAST_RTP;
    payload[1] = sequence;
    memcpy(&payload[2], amplitudes, HB_RING_POD_COUNT);
    return echo_command(payload, sizeof(payload));
}

bool hb_ring_master_all_stop(void)
{
    const uint8_t payload[] = { HB_CMD_ALL_STOP };
    return ring_started && echo_command(payload, sizeof(payload));
}

void hb_ring_master_shutdown(void)
{
    if (ring_started)
        (void)hb_ring_master_all_stop();
    ring_started = false;
    if (uart_installed) {
        (void)uart_wait_tx_done(RING_UART, pdMS_TO_TICKS(20));
        (void)uart_driver_delete(RING_UART);
        uart_installed = false;
    }
    gpio_set_direction(HB_PIN_RING_TX, GPIO_MODE_OUTPUT);
    gpio_set_level(HB_PIN_RING_TX, 0);
    gpio_set_direction(HB_PIN_RING_RX, GPIO_MODE_INPUT);
    gpio_pulldown_dis(HB_PIN_RING_RX);
    gpio_pullup_dis(HB_PIN_RING_RX);
    gpio_set_level(HB_PIN_POD_POWER_ON, 0);
}
