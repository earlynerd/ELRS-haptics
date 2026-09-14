CC      := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy
SIZE    := arm-none-eabi-size
PYTHON  ?= py

ROBOT_ROOT ?= ../../../bl4818-servo-M23_2
BUILD_DIR := build
PROJECT := m2003-haptic-pod
LDROM_PROJECT := m2003-ldrom
FIRMWARE_IMAGE_VERSION ?= 1

ifeq ($(OS),Windows_NT)
define MAKE_DIR
if not exist "$(subst /,\,$(1))" mkdir "$(subst /,\,$(1))"
endef
else
define MAKE_DIR
mkdir -p "$(1)"
endef
endif

CPU_FLAGS := -mcpu=cortex-m23 -mthumb -mfloat-abi=soft
INCLUDES := -Iinclude -I$(ROBOT_ROOT)/include -I$(ROBOT_ROOT)/CMSIS \
            -I$(ROBOT_ROOT)/Library/StdDriver/inc
CFLAGS := $(CPU_FLAGS) -O2 -Wall -Wextra -Werror=return-type -g \
          -ffunction-sections -fdata-sections -MMD -MP $(INCLUDES)
LDFLAGS := $(CPU_FLAGS) -Wl,--gc-sections \
           -Wl,-Map,$(BUILD_DIR)/$(PROJECT).map -T $(ROBOT_ROOT)/m2003.ld
LDROM_CFLAGS := $(CPU_FLAGS) -Os -flto -Wall -Wextra -g -ffreestanding \
                -ffunction-sections -fdata-sections -fno-unwind-tables \
                -fno-asynchronous-unwind-tables -fno-delete-null-pointer-checks \
                -fno-jump-tables -MMD -MP $(INCLUDES)
LDROM_LDFLAGS := $(CPU_FLAGS) -flto -nostdlib -Wl,--gc-sections \
                 -Wl,-Map,$(BUILD_DIR)/$(LDROM_PROJECT).map \
                 -T $(ROBOT_ROOT)/ldrom/m2003_ldrom.ld

LOCAL_SRCS := src/main.c src/app_uart.c src/drv2625.c src/ring_protocol.c
BORROWED_APP_SRCS := $(ROBOT_ROOT)/src/startup_m2003.c \
                     $(ROBOT_ROOT)/src/system_M2003.c \
                     $(ROBOT_ROOT)/src/boot_control.c
BSP_SRCS := $(wildcard $(ROBOT_ROOT)/Library/StdDriver/src/*.c)
LDROM_SRCS := $(ROBOT_ROOT)/ldrom/startup.c \
              $(ROBOT_ROOT)/ldrom/platform.c \
              $(ROBOT_ROOT)/ldrom/main.c \
              $(ROBOT_ROOT)/ldrom/uart.c \
              $(ROBOT_ROOT)/ldrom/flash.c \
              $(ROBOT_ROOT)/ldrom/crc32.c \
              $(ROBOT_ROOT)/ldrom/protocol.c

LOCAL_OBJS := $(patsubst src/%.c,$(BUILD_DIR)/local/%.o,$(LOCAL_SRCS))
BORROWED_APP_OBJS := $(patsubst $(ROBOT_ROOT)/%.c,$(BUILD_DIR)/borrowed/%.o,$(BORROWED_APP_SRCS))
BSP_OBJS := $(patsubst $(ROBOT_ROOT)/%.c,$(BUILD_DIR)/borrowed/%.o,$(BSP_SRCS))
LDROM_OBJS := $(patsubst $(ROBOT_ROOT)/%.c,$(BUILD_DIR)/ldrom/%.o,$(LDROM_SRCS))
APP_OBJS := $(LOCAL_OBJS) $(BORROWED_APP_OBJS) $(BSP_OBJS)
DEPS := $(APP_OBJS:.o=.d) $(LDROM_OBJS:.o=.d)

ifeq ($(wildcard $(ROBOT_ROOT)/ldrom/protocol.c),)
$(error ROBOT_ROOT does not contain the expected music-robot firmware tree: $(ROBOT_ROOT))
endif

all: $(BUILD_DIR)/$(PROJECT).bin size
ldrom: $(BUILD_DIR)/$(LDROM_PROJECT).bin ldrom-size
images: all ldrom package

$(BUILD_DIR)/local/%.o: src/%.c
	@$(call MAKE_DIR,$(dir $@))
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/borrowed/%.o: $(ROBOT_ROOT)/%.c
	@$(call MAKE_DIR,$(dir $@))
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/ldrom/%.o: $(ROBOT_ROOT)/%.c
	@$(call MAKE_DIR,$(dir $@))
	$(CC) $(LDROM_CFLAGS) -c $< -o $@

$(BUILD_DIR)/$(PROJECT).elf: $(APP_OBJS) $(ROBOT_ROOT)/m2003.ld
	$(CC) $(APP_OBJS) $(LDFLAGS) -o $@

$(BUILD_DIR)/$(LDROM_PROJECT).elf: $(LDROM_OBJS) $(ROBOT_ROOT)/ldrom/m2003_ldrom.ld
	$(CC) $(LDROM_OBJS) $(LDROM_LDFLAGS) -o $@

$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf
	$(OBJCOPY) -O binary $< $@

package: $(BUILD_DIR)/$(PROJECT).bin
	$(PYTHON) $(ROBOT_ROOT)/scripts/firmware_image.py $< \
		--image-version $(FIRMWARE_IMAGE_VERSION) \
		--image-out $(BUILD_DIR)/$(PROJECT).update.bin \
		--manifest-out $(BUILD_DIR)/$(PROJECT).manifest.bin

size: $(BUILD_DIR)/$(PROJECT).elf
	$(SIZE) $<

ldrom-size: $(BUILD_DIR)/$(LDROM_PROJECT).elf
	$(SIZE) $<

clean:
	$(RM) -r $(BUILD_DIR)

.PHONY: all ldrom images package size ldrom-size clean
-include $(DEPS)
