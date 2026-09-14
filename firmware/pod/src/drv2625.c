#include "drv2625.h"

#include <stddef.h>

#include "M2003.h"

#define DRV_ADDR             0x5Au
#define REG_CHIP_ID          0x00u
#define REG_STATUS           0x01u
#define REG_CONTROL_1        0x07u
#define REG_CONTROL_2        0x08u
#define REG_CONTROL_3        0x09u
#define REG_GO               0x0Cu
#define REG_RTP_INPUT        0x0Eu
#define REG_RATED_VOLTAGE    0x1Fu
#define REG_OD_CLAMP         0x20u
#define REG_CAL_COMP         0x21u
#define REG_CAL_BEMF         0x22u
#define REG_FEEDBACK         0x23u
#define REG_DRIVE_TIME       0x27u
#define REG_BLANKING_IDISS   0x28u
#define REG_SAMPLE_ZC        0x29u
#define REG_CAL_TIME         0x2Au

#define STATUS_FAULTS        0x87u
#define STATUS_PROCESS_DONE  0x08u
#define STOP_SETTLE_MS       51u
#define CAL_TIMEOUT_MS       1500u

static drv2625_snapshot_t current;
static uint32_t state_started_ms;

static uint8_t write_reg(uint8_t reg, uint8_t value)
{
    return I2C_WriteByteOneReg(I2C0, DRV_ADDR, reg, value) == 0u;
}

static uint8_t read_reg(uint8_t reg, uint8_t *value)
{
    uint8_t received;
    if (value == NULL) return 0u;
    if (I2C_ReadMultiBytesOneReg(I2C0, DRV_ADDR, reg, &received, 1u) != 1u)
        return 0u;
    *value = received;
    return 1u;
}

static uint8_t configure_calibration(void)
{
    return write_reg(REG_GO, 0x00u) &&
           write_reg(REG_CONTROL_3, 0x02u) &&
           write_reg(REG_CONTROL_2, 0x88u) &&
           write_reg(REG_DRIVE_TIME, 0x10u) &&
           write_reg(REG_BLANKING_IDISS, 0x11u) &&
           write_reg(REG_SAMPLE_ZC, 0x0Cu) &&
           write_reg(REG_CAL_TIME, 0x02u) &&
           write_reg(REG_RATED_VOLTAGE, 0x46u) &&
           write_reg(REG_OD_CLAMP, 0x7Bu) &&
           write_reg(REG_FEEDBACK, 0x3Au) &&
           write_reg(REG_CONTROL_1, 0x4Bu) &&
           write_reg(REG_GO, 0x01u);
}

void drv2625_init(uint32_t now_ms)
{
    uint8_t id = 0u;
    uint8_t ignored_status = 0u;

    current.state = DRV2625_STATE_FAULT;
    current.status = 0u;
    CLK->APBCLK0 |= CLK_APBCLK0_I2C0CKEN_Msk;
    SYS_ResetModule(I2C0_RST);
    SYS->GPB_MFPL = (SYS->GPB_MFPL &
                     ~(SYS_GPB_MFPL_PB4MFP_Msk | SYS_GPB_MFPL_PB5MFP_Msk)) |
                    SYS_GPB_MFPL_PB4MFP_I2C0_SDA |
                    SYS_GPB_MFPL_PB5MFP_I2C0_SCL;
    I2C_Open(I2C0, 400000u);

    if (!read_reg(REG_CHIP_ID, &id) || (id >> 4) != 1u ||
        !read_reg(REG_STATUS, &ignored_status))
        return;
    current.chip_id = id;
    current.status = ignored_status;
    if (!configure_calibration())
        return;
    current.state = DRV2625_STATE_CALIBRATING;
    state_started_ms = now_ms;
}

void drv2625_poll(uint32_t now_ms)
{
    if (current.state == DRV2625_STATE_CALIBRATING) {
        uint8_t go;
        if ((uint32_t)(now_ms - state_started_ms) > CAL_TIMEOUT_MS ||
            !read_reg(REG_GO, &go)) {
            current.state = DRV2625_STATE_FAULT;
        } else if ((go & 1u) == 0u) {
            uint8_t status;
            if (!read_reg(REG_STATUS, &status)) {
                current.state = DRV2625_STATE_FAULT;
                return;
            }
            current.status = status;
            if ((status & STATUS_PROCESS_DONE) == 0u ||
                (status & STATUS_FAULTS) != 0u ||
                !read_reg(REG_CAL_COMP, &current.cal_comp) ||
                !read_reg(REG_CAL_BEMF, &current.cal_bemf) ||
                !read_reg(REG_FEEDBACK, &current.feedback) ||
                !write_reg(REG_CONTROL_1, 0x48u) ||
                !write_reg(REG_RTP_INPUT, 0x00u)) {
                current.state = DRV2625_STATE_FAULT;
            } else {
                current.state = DRV2625_STATE_READY;
            }
        }
    } else if (current.state == DRV2625_STATE_STOPPING &&
               (uint32_t)(now_ms - state_started_ms) >= STOP_SETTLE_MS) {
        uint8_t status;
        if (!read_reg(REG_STATUS, &status)) {
            current.state = DRV2625_STATE_FAULT;
        } else {
            current.status = status;
            current.state = (status & STATUS_FAULTS) ? DRV2625_STATE_FAULT
                                                     : DRV2625_STATE_READY;
        }
    }
}

uint8_t drv2625_set_rtp(uint8_t amplitude, uint32_t now_ms)
{
    (void)now_ms;
    if (amplitude > 127u) amplitude = 127u;
    if (current.state != DRV2625_STATE_READY &&
        current.state != DRV2625_STATE_PLAYING)
        return 0u;
    if (amplitude == 0u) {
        drv2625_stop(now_ms);
        return 1u;
    }
    if (!write_reg(REG_RTP_INPUT, amplitude)) {
        current.state = DRV2625_STATE_FAULT;
        return 0u;
    }
    if (current.state == DRV2625_STATE_READY && !write_reg(REG_GO, 0x01u)) {
        current.state = DRV2625_STATE_FAULT;
        return 0u;
    }
    current.state = DRV2625_STATE_PLAYING;
    return 1u;
}

void drv2625_stop(uint32_t now_ms)
{
    if (current.state == DRV2625_STATE_PLAYING) {
        if (!write_reg(REG_GO, 0x00u)) {
            current.state = DRV2625_STATE_FAULT;
            return;
        }
        current.state = DRV2625_STATE_STOPPING;
        state_started_ms = now_ms;
    }
}

void drv2625_get_snapshot(drv2625_snapshot_t *snapshot)
{
    if (snapshot != NULL) *snapshot = current;
}
