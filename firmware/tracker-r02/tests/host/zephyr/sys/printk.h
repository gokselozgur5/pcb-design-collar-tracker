#ifndef COLLAR_HOST_PRINTK_H
#define COLLAR_HOST_PRINTK_H
#include <stdio.h>
#define printk(...) fprintf(stderr, __VA_ARGS__)
#endif
