#ifndef COLLAR_DNS_H
#define COLLAR_DNS_H
#include "recovery.h"
int tracker_dns_lookup(struct resolved_address *address);
bool tracker_dns_wait_idle(uint32_t timeout_ms);
#endif
