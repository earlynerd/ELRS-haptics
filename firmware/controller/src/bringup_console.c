#include "bringup_console.h"

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "esp_console.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "backpack_rx.h"
#include "hb_ring.h"
#include "ring_master.h"

#define BRINGUP_MAX_AMPLITUDE 64u
#define BRINGUP_MIN_PULSE_MS 10u
#define BRINGUP_MAX_PULSE_MS 250u
#define BRINGUP_REFRESH_MS 20u

static const char *TAG = "bringup";
static portMUX_TYPE state_lock = portMUX_INITIALIZER_UNLOCKED;
static bool manual_active;
static esp_console_repl_t *console_repl;

static const char *driver_state_name(uint8_t state)
{
    switch (state) {
    case 0u: return "fault";
    case 1u: return "calibrating";
    case 2u: return "ready";
    case 3u: return "playing";
    case 4u: return "stopping";
    default: return "unknown";
    }
}

static bool parse_u32(const char *text, uint32_t minimum, uint32_t maximum,
                      uint32_t *value)
{
    char *end;
    unsigned long parsed;

    if (text == NULL || *text == '\0' || value == NULL)
        return false;
    errno = 0;
    parsed = strtoul(text, &end, 10);
    if (errno != 0 || *end != '\0' || parsed < minimum || parsed > maximum)
        return false;
    *value = (uint32_t)parsed;
    return true;
}

bool hb_bringup_console_manual_active(void)
{
    bool active;
    portENTER_CRITICAL(&state_lock);
    active = manual_active;
    portEXIT_CRITICAL(&state_lock);
    return active;
}

static void set_manual_active(bool active)
{
    portENTER_CRITICAL(&state_lock);
    manual_active = active;
    portEXIT_CRITICAL(&state_lock);
}

static void enter_manual_mode(void)
{
    set_manual_active(true);
    if (hb_ring_master_is_started())
        (void)hb_ring_master_all_stop();
}

static void print_usage(void)
{
    printf("Haptic bracelet bring-up commands:\n"
           "  hb status\n"
           "  hb telemetry\n"
           "  hb manual\n"
           "  hb flight\n"
           "  hb stop\n"
           "  hb ring restart|off\n"
           "  hb pod status <0-7|all>\n"
           "  hb pod pulse <0-7> <1-64> [10-250 ms]\n"
           "Bus and actuator diagnostics latch manual mode. Use 'hb flight'\n"
           "to restore telemetry control after diagnostics.\n");
}

static int command_status(void)
{
    hb_attitude_t attitude;
    uint32_t age_ms = 0u;
    bool have_telemetry = hb_backpack_latest(&attitude, &age_ms);
    bool started = hb_ring_master_is_started();
    uint8_t count = hb_ring_master_pod_count();

    printf("mode=%s ring=%s pods=%u flight_ready=%s telemetry=%s",
           hb_bringup_console_manual_active() ? "manual" : "flight",
           started ? "online" : "off", count,
           hb_ring_master_flight_ready() ? "yes" : "no",
           have_telemetry ? "valid" : "none");
    if (have_telemetry)
        printf(" age_ms=%" PRIu32, age_ms);
    printf("\n");
    return 0;
}

static int command_telemetry(void)
{
    hb_attitude_t attitude;
    uint32_t age_ms;

    if (!hb_backpack_latest(&attitude, &age_ms)) {
        printf("No valid Backpack attitude frame has been received.\n");
        return 1;
    }
    printf("pitch=%d roll=%d yaw=%d rad_x10000 age_ms=%" PRIu32 "\n",
           attitude.pitch_rad_x10000, attitude.roll_rad_x10000,
           attitude.yaw_rad_x10000, age_ms);
    return 0;
}

static void print_pod_status(uint8_t address, const hb_pod_status_t *status)
{
    printf("pod=%u chip_id=0x%02X status=0x%02X state=%s(%u) "
           "cal_comp=0x%02X cal_bemf=0x%02X feedback=0x%02X temp=",
           address, status->chip_id, status->driver_status,
           driver_state_name(status->driver_state), status->driver_state,
           status->calibration_compensation, status->calibration_bemf,
           status->feedback);
    if (status->temperature_available)
        printf("%d_raw\n", status->temperature_raw);
    else
        printf("unavailable\n");
}

static int command_pod_status(const char *target)
{
    uint8_t count;
    uint32_t parsed_address;
    uint8_t first;
    uint8_t last;
    uint8_t address;
    int result = 0;

    enter_manual_mode();
    count = hb_ring_master_pod_count();
    if (count == 0u) {
        printf("No enumerated ring. Use 'hb ring restart'.\n");
        return 1;
    }
    if (strcmp(target, "all") == 0) {
        first = 0u;
        last = count;
    } else {
        if (!parse_u32(target, 0u, HB_RING_POD_COUNT - 1u, &parsed_address) ||
            parsed_address >= count) {
            printf("Pod must be within the enumerated range 0-%u.\n", count - 1u);
            return 1;
        }
        first = (uint8_t)parsed_address;
        last = (uint8_t)(first + 1u);
    }

    for (address = first; address < last; ++address) {
        hb_pod_status_t status;
        if (hb_ring_master_query_status(address, &status)) {
            print_pod_status(address, &status);
        } else {
            printf("pod=%u status_query=timeout_or_invalid\n", address);
            result = 1;
        }
    }
    return result;
}

static int command_pod_pulse(const char *address_text,
                             const char *amplitude_text,
                             const char *duration_text)
{
    uint32_t address;
    uint32_t amplitude;
    uint32_t duration_ms = 100u;
    uint32_t elapsed_ms = 0u;
    uint8_t count;
    bool drive_ok = true;
    bool stop_ok;

    if (!parse_u32(address_text, 0u, HB_RING_POD_COUNT - 1u, &address) ||
        !parse_u32(amplitude_text, 1u, BRINGUP_MAX_AMPLITUDE, &amplitude) ||
        (duration_text != NULL &&
         !parse_u32(duration_text, BRINGUP_MIN_PULSE_MS,
                    BRINGUP_MAX_PULSE_MS, &duration_ms))) {
        printf("Usage: hb pod pulse <0-7> <1-64> [10-250 ms]\n");
        return 1;
    }

    enter_manual_mode();
    count = hb_ring_master_pod_count();
    if (address >= count) {
        printf("Pod %" PRIu32 " is not enumerated; current count is %u.\n",
               address, count);
        return 1;
    }

    printf("Pulsing pod=%" PRIu32 " amplitude=%" PRIu32
           " duration_ms=%" PRIu32 "\n", address, amplitude, duration_ms);
    while (elapsed_ms < duration_ms) {
        uint32_t remaining_ms = duration_ms - elapsed_ms;
        uint32_t wait_ms = remaining_ms < BRINGUP_REFRESH_MS
                               ? remaining_ms : BRINGUP_REFRESH_MS;
        if (!hb_ring_master_set_rtp((uint8_t)address, (uint8_t)amplitude)) {
            drive_ok = false;
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(wait_ms));
        elapsed_ms += wait_ms;
    }

    stop_ok = hb_ring_master_stop_pod((uint8_t)address);
    (void)hb_ring_master_all_stop();
    if (!drive_ok || !stop_ok) {
        printf("Pulse failed; all-stop requested and the pod watchdog remains active.\n");
        return 1;
    }
    printf("Pulse complete; controller remains in manual mode.\n");
    return 0;
}

static int hb_command(int argc, char **argv)
{
    if (argc < 2 || strcmp(argv[1], "help") == 0) {
        print_usage();
        return 0;
    }
    if (strcmp(argv[1], "status") == 0 && argc == 2)
        return command_status();
    if (strcmp(argv[1], "telemetry") == 0 && argc == 2)
        return command_telemetry();
    if (strcmp(argv[1], "manual") == 0 && argc == 2) {
        enter_manual_mode();
        printf("Manual mode latched; automatic haptics are stopped.\n");
        return 0;
    }
    if (strcmp(argv[1], "flight") == 0 && argc == 2) {
        if (!hb_ring_master_flight_ready()) {
            printf("Flight mode requires exactly %u enumerated pods.\n",
                   HB_RING_POD_COUNT);
            return 1;
        }
        set_manual_active(false);
        printf("Flight mode armed; output still requires fresh valid telemetry.\n");
        return 0;
    }
    if (strcmp(argv[1], "stop") == 0 && argc == 2) {
        enter_manual_mode();
        printf(hb_ring_master_all_stop()
                   ? "All-stop confirmed; manual mode latched.\n"
                   : "All-stop was not echoed; manual mode remains latched.\n");
        return 0;
    }
    if (strcmp(argv[1], "ring") == 0 && argc == 3) {
        enter_manual_mode();
        if (strcmp(argv[2], "off") == 0) {
            hb_ring_master_shutdown();
            printf("Pod rail off; manual mode latched.\n");
            return 0;
        }
        if (strcmp(argv[2], "restart") == 0) {
            hb_ring_master_shutdown();
            if (!hb_ring_master_start()) {
                printf("Ring restart failed; pod rail is off.\n");
                return 1;
            }
            printf("Ring online with %u enumerated pod%s; manual mode latched.\n",
                   hb_ring_master_pod_count(),
                   hb_ring_master_pod_count() == 1u ? "" : "s");
            return 0;
        }
    }
    if (strcmp(argv[1], "pod") == 0 && argc >= 4) {
        if (strcmp(argv[2], "status") == 0 && argc == 4)
            return command_pod_status(argv[3]);
        if (strcmp(argv[2], "pulse") == 0 && (argc == 5 || argc == 6))
            return command_pod_pulse(argv[3], argv[4],
                                     argc == 6 ? argv[5] : NULL);
    }

    print_usage();
    return 1;
}

esp_err_t hb_bringup_console_start(void)
{
    const esp_console_dev_usb_serial_jtag_config_t device_config =
        ESP_CONSOLE_DEV_USB_SERIAL_JTAG_CONFIG_DEFAULT();
    esp_console_repl_config_t repl_config = ESP_CONSOLE_REPL_CONFIG_DEFAULT();
    const esp_console_cmd_t command = {
        .command = "hb",
        .help = "Safe haptic-bracelet bring-up and diagnostics",
        .hint = "<status|telemetry|manual|flight|stop|ring|pod>",
        .func = hb_command
    };
    esp_err_t error;

    repl_config.prompt = "hb> ";
    repl_config.max_cmdline_length = 96u;
    error = esp_console_new_repl_usb_serial_jtag(&device_config, &repl_config,
                                                 &console_repl);
    if (error != ESP_OK)
        return error;
    error = esp_console_cmd_register(&command);
    if (error != ESP_OK)
        return error;
    error = esp_console_start_repl(console_repl);
    if (error == ESP_OK)
        ESP_LOGI(TAG, "USB bring-up console ready; run 'hb help'");
    return error;
}
