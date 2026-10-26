cmake_minimum_required(VERSION 3.20.0)
list(APPEND BOARD_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/..)
list(APPEND DTS_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/..)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(collar_tracker_r03)
# TF-M runs a fourth, nested CMake process; sysbuild's child cache is not inherited.
if(NOT DEFINED USER_CACHE_DIR)
    message(FATAL_ERROR "Pass an explicit task USER_CACHE_DIR")
endif()
set_property(TARGET zephyr_property_target APPEND PROPERTY TFM_CMAKE_OPTIONS
    "-DUSER_CACHE_DIR:PATH=${USER_CACHE_DIR}")
target_sources(app PRIVATE src/main.c src/uplink.c src/trial.c src/trial_policy.c ../tracker/src/outbox.c
    ../tracker-r02/src/dns.c ../tracker-r02/src/supervisor.c ../tracker-r02/src/recovery.c)
target_include_directories(app PRIVATE ../factory/src ../tracker/src ../tracker-r02/src)
target_compile_options(app PRIVATE -Wall -Wextra -Werror)
