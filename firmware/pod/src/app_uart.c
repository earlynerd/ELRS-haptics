#include <stdint.h>

#include "M2003.h"
#include "app_uart.h"

#define UART_RX_BUF_SIZE 256u
#define UART_TX_BUF_SIZE 256u

static volatile uint8_t rx_buf[UART_RX_BUF_SIZE];
static volatile uint16_t rx_head;
static volatile uint16_t rx_tail;
static volatile uint8_t rx_overflow;
static volatile uint8_t tx_buf[UART_TX_BUF_SIZE];
static volatile uint16_t tx_head;
static volatile uint16_t tx_tail;
static volatile uint8_t tx_running;
static volatile uint8_t echo_enabled;

static uint32_t irq_save(void)
{
    uint32_t state = __get_PRIMASK();
    __disable_irq();
    return state;
}

static void irq_restore(uint32_t state)
{
    if ((state & 1u) == 0u) __enable_irq();
}

void UART1_IRQHandler(void)
{
    uint32_t status = UART1->INTSTS;
    if (status & UART_INTSTS_RLSINT_Msk) {
        UART1->FIFOSTS = UART_FIFOSTS_BIF_Msk | UART_FIFOSTS_FEF_Msk |
                         UART_FIFOSTS_PEF_Msk | UART_FIFOSTS_ADDRDETF_Msk;
    }
    if (status & UART_INTSTS_BUFERRINT_Msk) {
        rx_overflow = 1u;
        UART1->FIFOSTS = UART_FIFOSTS_RXOVIF_Msk | UART_FIFOSTS_TXOVIF_Msk;
    }
    if (status & (UART_INTSTS_RDAINT_Msk | UART_INTSTS_RXTOINT_Msk)) {
        while (!(UART1->FIFOSTS & UART_FIFOSTS_RXEMPTY_Msk)) {
            uint8_t value = (uint8_t)UART1->DAT;
            uint16_t next;
            if (echo_enabled) {
                while (UART1->FIFOSTS & UART_FIFOSTS_TXFULL_Msk) { }
                UART1->DAT = value;
            }
            next = (uint16_t)((rx_head + 1u) % UART_RX_BUF_SIZE);
            if (next == rx_tail) {
                rx_overflow = 1u;
            } else {
                rx_buf[rx_head] = value;
                rx_head = next;
            }
        }
    }
    if (status & UART_INTSTS_THREINT_Msk) {
        while (!(UART1->FIFOSTS & UART_FIFOSTS_TXFULL_Msk) && tx_head != tx_tail) {
            UART1->DAT = tx_buf[tx_tail];
            tx_tail = (uint16_t)((tx_tail + 1u) % UART_TX_BUF_SIZE);
        }
        if (tx_head == tx_tail) {
            UART1->INTEN &= ~UART_INTEN_THREIEN_Msk;
            tx_running = 0u;
        }
    }
}

void uart_init(uint32_t baudrate)
{
    CLK->APBCLK0 |= CLK_APBCLK0_UART1CKEN_Msk;
    CLK->CLKSEL2 = (CLK->CLKSEL2 & ~CLK_CLKSEL2_UART1SEL_Msk) |
                   CLK_CLKSEL2_UART1SEL_HIRC;
    CLK->CLKDIV0 = (CLK->CLKDIV0 & ~CLK_CLKDIV0_UART1DIV_Msk) |
                   CLK_CLKDIV0_UART1(1);
    SYS_ResetModule(UART1_RST);
    SYS->GPF_MFPL = (SYS->GPF_MFPL &
                     ~(SYS_GPF_MFPL_PF0MFP_Msk | SYS_GPF_MFPL_PF1MFP_Msk)) |
                    SYS_GPF_MFPL_PF0MFP_UART1_TXD |
                    SYS_GPF_MFPL_PF1MFP_UART1_RXD;
    SYS->GPF_MFOS &= ~(SYS_GPF_MFOS_PF0MFOS_Msk | SYS_GPF_MFOS_PF1MFOS_Msk);
    UART_Open(UART1, baudrate);
    UART_SetLine_Config(UART1, baudrate, UART_WORD_LEN_8, UART_PARITY_NONE,
                         UART_STOP_BIT_1);
    rx_head = rx_tail = tx_head = tx_tail = 0u;
    tx_running = rx_overflow = echo_enabled = 0u;
    UART1->FIFO = (UART1->FIFO & ~UART_FIFO_RFITL_Msk) | UART_FIFO_RFITL_1BYTE;
    UART1->FIFO |= UART_FIFO_RXRST_Msk | UART_FIFO_TXRST_Msk;
    UART1->INTEN |= UART_INTEN_RDAIEN_Msk | UART_INTEN_RXTOIEN_Msk |
                    UART_INTEN_RLSIEN_Msk | UART_INTEN_BUFERRIEN_Msk;
    NVIC_SetPriority(UART1_IRQn, 3u);
    NVIC_EnableIRQ(UART1_IRQn);
}

void uart_putc(uint8_t value)
{
    uint16_t next = (uint16_t)((tx_head + 1u) % UART_TX_BUF_SIZE);
    uint32_t state;
    while (next == tx_tail) { }
    state = irq_save();
    tx_buf[tx_head] = value;
    tx_head = next;
    if (!tx_running) {
        tx_running = 1u;
        UART1->DAT = tx_buf[tx_tail];
        tx_tail = (uint16_t)((tx_tail + 1u) % UART_TX_BUF_SIZE);
        UART1->INTEN |= UART_INTEN_THREIEN_Msk;
    }
    irq_restore(state);
}

uint8_t uart_available(void) { return rx_head != rx_tail; }
uint8_t uart_getc(void)
{
    uint8_t value = 0u;
    if (rx_head != rx_tail) {
        value = rx_buf[rx_tail];
        rx_tail = (uint16_t)((rx_tail + 1u) % UART_RX_BUF_SIZE);
    }
    return value;
}
void uart_echo_enable(void) { echo_enabled = 1u; }
void uart_echo_disable(void) { echo_enabled = 0u; }
void uart_tx_flush(void)
{
    while (tx_running || tx_head != tx_tail) { }
    while (!(UART1->FIFOSTS & UART_FIFOSTS_TXEMPTYF_Msk)) { }
}
void uart_rx_flush(void) { rx_tail = rx_head; rx_overflow = 0u; }
uint8_t uart_rx_overflowed(void) { return rx_overflow; }
void uart_rx_clear_overflow(void) { rx_overflow = 0u; }
