cmake_minimum_required(VERSION 3.20.0)
list(APPEND BOARD_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/..)
list(APPEND DTS_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/..)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(collar_tracker_r02)
target_sources(app PRIVATE src/main.c src/uplink.c src/dns.c src/supervisor.c
                          src/recovery.c ../tracker/src/outbox.c)
target_include_directories(app PRIVATE ../factory/src ../tracker/src)
target_compile_options(app PRIVATE -Wall -Wextra -Werror)
