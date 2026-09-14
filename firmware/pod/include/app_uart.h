#ifndef HB_APP_UART_H
#define HB_APP_UART_H

#include <stdint.h>

void uart_init(uint32_t baudrate);
void uart_putc(uint8_t value);
uint8_t uart_available(void);
uint8_t uart_getc(void);
void uart_echo_enable(void);
void uart_echo_disable(void);
void uart_tx_flush(void);
void uart_rx_flush(void);
uint8_t uart_rx_overflowed(void);
void uart_rx_clear_overflow(void);

#endif
