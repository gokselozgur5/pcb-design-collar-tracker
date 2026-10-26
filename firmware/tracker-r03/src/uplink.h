#ifndef COLLAR_UPLINK_H
#define COLLAR_UPLINK_H
#include "outbox.h"
int uplink_configured(void);
int uplink_send(const struct position *position);
#endif
