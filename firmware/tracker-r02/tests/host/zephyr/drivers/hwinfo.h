#ifndef COLLAR_HOST_HWINFO_H
#define COLLAR_HOST_HWINFO_H
#include <stdint.h>
int hwinfo_get_reset_cause(uint32_t *);
int hwinfo_clear_reset_cause(void);
#endif
