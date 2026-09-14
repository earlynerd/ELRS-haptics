#ifndef HB_RING_PROTOCOL_H
#define HB_RING_PROTOCOL_H

#include <stdint.h>

void ring_protocol_init(void);
void ring_protocol_poll(void);
void ring_protocol_tick(uint32_t elapsed_ms, uint32_t now_ms);
uint8_t ring_protocol_address(void);

#endif
