#ifndef COLLAR_HOST_MCUBOOT_H
#define COLLAR_HOST_MCUBOOT_H
#include <stdbool.h>
bool boot_is_img_confirmed(void);
int boot_write_img_confirmed(void);
#endif
