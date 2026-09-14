cmake_minimum_required(VERSION 3.20)
project(haptic_bracelet_core_tests C)

enable_testing()
add_executable(hb_core_tests
    test_core.c
    ../common/src/hb_crc.c
    ../common/src/hb_ring.c
    ../common/src/hb_telemetry.c
    ../common/src/hb_attitude_map.c
)
target_include_directories(hb_core_tests PRIVATE ../common/include)
if(MSVC)
    target_compile_options(hb_core_tests PRIVATE /W4 /WX)
else()
    target_compile_options(hb_core_tests PRIVATE -Wall -Wextra -Werror)
endif()
add_test(NAME hb_core_tests COMMAND hb_core_tests)
