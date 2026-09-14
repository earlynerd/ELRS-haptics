#include <stdint.h>

#include "M2003.h"
#include "app_uart.h"
#include "boot_control.h"
#include "drv2625.h"
#include "ring_protocol.h"
#include "wdt.h"

#define CORE_CLOCK_HZ 24000000u
#define UART_BAUD 250000u

volatile uint32_t hb_millis;
static volatile uint8_t main_alive;

void Uart0DefaultMPF(void) { }

void SysTick_Handler(void)
{
    ++hb_millis;
    if (main_alive) {
        main_alive = 0u;
        WDT_RESET_COUNTER();
    }
}

void HardFault_Handler(void)
{
    NVIC_SystemReset();
    for (;;) { }
}

void NMI_Handler(void)
{
    NVIC_SystemReset();
    for (;;) { }
}

static void hardware_init(void)
{
    CLK->PWRCTL |= CLK_PWRCTL_HIRCEN_Msk | CLK_PWRCTL_LIRCEN_Msk;
    while ((CLK->STATUS & (CLK_STATUS_HIRCSTB_Msk | CLK_STATUS_LIRCSTB_Msk)) !=
           (CLK_STATUS_HIRCSTB_Msk | CLK_STATUS_LIRCSTB_Msk)) { }
    CLK->CLKSEL0 = (CLK->CLKSEL0 & ~CLK_CLKSEL0_HCLKSEL_Msk) |
                   CLK_CLKSEL0_HCLKSEL_HIRC;
    CLK->CLKDIV0 = (CLK->CLKDIV0 & ~CLK_CLKDIV0_HCLKDIV_Msk) |
                   CLK_CLKDIV0_HCLK(1);
    CLK->AHBCLK |= CLK_AHBCLK_GPBCKEN_Msk | CLK_AHBCLK_GPFCKEN_Msk;
    SystemCoreClock = CORE_CLOCK_HZ;
    SysTick_Config(CORE_CLOCK_HZ / 1000u);
    NVIC_SetPriority(SysTick_IRQn, 2u);

    CLK->CLKSEL1 = (CLK->CLKSEL1 & ~CLK_CLKSEL1_WDTSEL_Msk) |
                   CLK_CLKSEL1_WDTSEL_LIRC;
    CLK->APBCLK0 |= CLK_APBCLK0_WDTCKEN_Msk;
    WDT_Open(WDT_TIMEOUT_2POW14, WDT_RESET_DELAY_18CLK, TRUE, FALSE);
}

static void delay_ms(uint32_t duration)
{
    uint32_t start = hb_millis;
    while ((uint32_t)(hb_millis - start) < duration) main_alive = 1u;
}

int main(void)
{
    uint32_t previous_ms;
    hardware_init();
    uart_init(UART_BAUD);
    ring_protocol_init();
    delay_ms(2u); /* DRV2625 requires NRST high for at least 1 ms. */
    drv2625_init(hb_millis);
    previous_ms = hb_millis;

    for (;;) {
        uint32_t now = hb_millis;
        main_alive = 1u;
        ring_protocol_poll();
        if (now != previous_ms) {
            uint32_t elapsed = now - previous_ms;
            previous_ms = now;
            ring_protocol_tick(elapsed, now);
            drv2625_poll(now);
        }
        if (boot_control_pending()) boot_control_enter();
    }
}
