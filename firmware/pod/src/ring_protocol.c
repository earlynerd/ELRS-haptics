#include "ring_protocol.h"

#include "app_uart.h"
#include "boot_control.h"
#include "drv2625.h"

#define PREAMBLE_0 0xA5u
#define PREAMBLE_1 0x5Au
#define MAX_PAYLOAD 64u
#define ADDRESS_UNASSIGNED 0xFFu
#define POD_COUNT 8u
#define CMD_ENTER_SF 0x01u
#define CMD_ENTER_CT 0x02u
#define CMD_SET_ADDRESS 0x03u
#define CMD_BROADCAST_RTP 0x11u
#define CMD_ALL_STOP 0x12u
#define CMD_ADDR_BASE 0x20u
#define CMD_STATUS_BASE 0x40u
#define CMD_ACK_BASE 0x50u
#define SUBCMD_SET_RTP 0x01u
#define SUBCMD_STOP 0x02u
#define SUBCMD_QUERY_STATUS 0x03u
#define SUBCMD_ENTER_LOADER 0x1Bu
#define COMMAND_WATCHDOG_MS 100u
#define FRAME_TIMEOUT_MS 20u

typedef enum { MODE_CUT_THROUGH, MODE_STORE_FORWARD } forward_mode_t;
typedef enum { SCAN_A5, SCAN_5A, BUFFER_FRAME } receive_phase_t;

static uint8_t address;
static forward_mode_t forward_mode;
static forward_mode_t frame_start_mode;
static receive_phase_t receive_phase;
static uint8_t frame[1u + MAX_PAYLOAD + 2u];
static uint8_t frame_position;
static uint8_t frame_expected;
static uint32_t receive_age_ms;
static uint32_t command_age_ms;

static uint16_t crc16(const uint8_t *data, uint8_t length)
{
    uint16_t crc = 0xFFFFu;
    uint8_t i;
    for (i = 0u; i < length; ++i) {
        uint8_t bit;
        crc ^= (uint16_t)data[i] << 8;
        for (bit = 0u; bit < 8u; ++bit)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u)
                                  : (uint16_t)(crc << 1);
    }
    return crc;
}

static void send_body(const uint8_t *body, uint8_t length)
{
    uint8_t i;
    uart_putc(PREAMBLE_0);
    uart_putc(PREAMBLE_1);
    for (i = 0u; i < length; ++i) uart_putc(body[i]);
}

static void send_payload(const uint8_t *payload, uint8_t length)
{
    uint8_t body[1u + MAX_PAYLOAD + 2u];
    uint16_t crc;
    uint8_t i;
    body[0] = length;
    for (i = 0u; i < length; ++i) body[1u + i] = payload[i];
    crc = crc16(body, (uint8_t)(length + 1u));
    body[1u + length] = (uint8_t)(crc >> 8);
    body[2u + length] = (uint8_t)crc;
    send_body(body, (uint8_t)(length + 3u));
}

static void forward_verbatim(void)
{
    send_body(frame, (uint8_t)(frame[0] + 3u));
}

static void send_status(void)
{
    drv2625_snapshot_t snapshot;
    uint8_t payload[9];
    drv2625_get_snapshot(&snapshot);
    payload[0] = (uint8_t)(CMD_STATUS_BASE | address);
    payload[1] = snapshot.chip_id;
    payload[2] = snapshot.status;
    payload[3] = (uint8_t)snapshot.state;
    payload[4] = snapshot.cal_comp;
    payload[5] = snapshot.cal_bemf;
    payload[6] = snapshot.feedback;
    payload[7] = 0xFFu; /* Temperature unavailable in this first slice. */
    payload[8] = 0xFFu;
    send_payload(payload, sizeof(payload));
}

static void send_ack(uint8_t subcommand, uint8_t result)
{
    uint8_t payload[3] = { (uint8_t)(CMD_ACK_BASE | address), subcommand, result };
    send_payload(payload, sizeof(payload));
}

static void dispatch(const uint8_t *payload, uint8_t length, uint32_t now_ms)
{
    uint8_t command = payload[0];
    if (command == CMD_ENTER_SF) {
        forward_mode = MODE_STORE_FORWARD;
        uart_echo_disable();
        if (frame_start_mode == MODE_STORE_FORWARD) forward_verbatim();
    } else if (command == CMD_ENTER_CT) {
        forward_mode = MODE_CUT_THROUGH;
        uart_echo_enable();
        if (frame_start_mode == MODE_STORE_FORWARD) forward_verbatim();
    } else if (command == CMD_SET_ADDRESS && length >= 2u) {
        uint8_t reply[2];
        if (payload[1] >= POD_COUNT) return;
        if (address == ADDRESS_UNASSIGNED) address = payload[1];
        reply[0] = CMD_SET_ADDRESS;
        reply[1] = (uint8_t)(payload[1] + 1u);
        send_payload(reply, sizeof(reply));
    } else if (command == CMD_BROADCAST_RTP && length == 10u &&
               address < POD_COUNT) {
        (void)drv2625_set_rtp(payload[2u + address], now_ms);
        command_age_ms = 0u;
    } else if (command == CMD_ALL_STOP) {
        drv2625_stop(now_ms);
        command_age_ms = COMMAND_WATCHDOG_MS;
    } else if (command >= CMD_ADDR_BASE && command < CMD_ADDR_BASE + POD_COUNT &&
               (command & 0x0Fu) == address && length >= 2u) {
        uint8_t subcommand = payload[1];
        uint8_t result = 1u;
        if (subcommand == SUBCMD_SET_RTP && length == 3u) {
            result = drv2625_set_rtp(payload[2], now_ms) ? 0u : 2u;
            command_age_ms = 0u;
        } else if (subcommand == SUBCMD_STOP) {
            drv2625_stop(now_ms);
            result = 0u;
        } else if (subcommand == SUBCMD_QUERY_STATUS) {
            send_status();
            return;
        } else if (subcommand == SUBCMD_ENTER_LOADER) {
            drv2625_stop(now_ms);
            boot_control_request(address);
            result = 0u;
        }
        send_ack(subcommand, result);
    } else if (forward_mode == MODE_STORE_FORWARD) {
        forward_verbatim();
    }
}

static void reset_receiver(void)
{
    receive_phase = SCAN_A5;
    frame_position = frame_expected = 0u;
    receive_age_ms = 0u;
}

static void process_frame(uint32_t now_ms)
{
    uint8_t length = frame[0];
    uint16_t received = ((uint16_t)frame[1u + length] << 8) |
                         frame[2u + length];
    if (crc16(frame, (uint8_t)(length + 1u)) == received)
        dispatch(&frame[1], length, now_ms);
    reset_receiver();
}

void ring_protocol_init(void)
{
    address = ADDRESS_UNASSIGNED;
    forward_mode = MODE_CUT_THROUGH;
    command_age_ms = COMMAND_WATCHDOG_MS;
    uart_echo_enable();
    uart_rx_flush();
    reset_receiver();
}

void ring_protocol_poll(void)
{
    uint8_t budget = 128u;
    extern volatile uint32_t hb_millis;
    if (uart_rx_overflowed()) {
        uart_rx_flush();
        uart_rx_clear_overflow();
        reset_receiver();
        return;
    }
    while (budget-- != 0u && uart_available()) {
        uint8_t value = uart_getc();
        if (receive_phase == SCAN_A5) {
            if (value == PREAMBLE_0) receive_phase = SCAN_5A;
        } else if (receive_phase == SCAN_5A) {
            if (value == PREAMBLE_1) {
                receive_phase = BUFFER_FRAME;
                frame_position = frame_expected = 0u;
                frame_start_mode = forward_mode;
            } else if (value != PREAMBLE_0) {
                receive_phase = SCAN_A5;
            }
        } else {
            if (frame_position < sizeof(frame)) frame[frame_position] = value;
            ++frame_position;
            if (frame_position == 1u) {
                if (frame[0] == 0u || frame[0] > MAX_PAYLOAD) {
                    reset_receiver();
                    continue;
                }
                frame_expected = (uint8_t)(frame[0] + 3u);
            }
            if (frame_expected != 0u && frame_position >= frame_expected)
                process_frame(hb_millis);
        }
    }
}

void ring_protocol_tick(uint32_t elapsed_ms, uint32_t now_ms)
{
    if (receive_phase != SCAN_A5) {
        receive_age_ms += elapsed_ms;
        if (receive_age_ms >= FRAME_TIMEOUT_MS) reset_receiver();
    }
    if (command_age_ms < COMMAND_WATCHDOG_MS) {
        command_age_ms += elapsed_ms;
        if (command_age_ms >= COMMAND_WATCHDOG_MS) drv2625_stop(now_ms);
    }
}

uint8_t ring_protocol_address(void) { return address; }
