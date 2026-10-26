#ifndef COLLAR_RECOVERY_H
#define COLLAR_RECOVERY_H
#include <stdbool.h>
#include <stdint.h>

/* Callers serialize all access to these policies. Neither performs I/O. */
enum tracker_phase {
	PHASE_BOOT, PHASE_STORAGE, PHASE_MODEM, PHASE_FIX, PHASE_ATTACH,
	PHASE_DNS, PHASE_CONNECT, PHASE_HTTP, PHASE_CLEANUP, PHASE_SLEEP, PHASE_SERVICE
};
struct progress_lease {
	int64_t deadline;
	enum tracker_phase phase;
	bool failed;
};
bool lease_init(struct progress_lease *, int64_t now, uint32_t budget_ms);
bool lease_enter(struct progress_lease *, int64_t now, enum tracker_phase, uint32_t budget_ms);
bool lease_feed_allowed(struct progress_lease *, int64_t now);
void lease_fail(struct progress_lease *);

enum dns_state { DNS_IDLE, DNS_PENDING, DNS_READY, DNS_ABANDONED };
struct resolved_address {
	uint8_t bytes[16];
	uint32_t scope_id;
	uint16_t port;
	uint8_t version; /* 4 or 6; independent of host/Zephyr AF_* numeric values. */
};
struct dns_slot {
	enum dns_state state;
	uint32_t generation;
	int64_t deadline;
	int result;
	struct resolved_address address;
};
int dns_slot_begin(struct dns_slot *, int64_t now, uint32_t budget_ms, uint32_t *ticket);
/* Worker must release every SDK addrinfo allocation before publishing. */
bool dns_slot_publish(struct dns_slot *, uint32_t ticket, int64_t now,
		      int result, const struct resolved_address *);
int dns_slot_poll(struct dns_slot *, uint32_t ticket, int64_t now, struct resolved_address *);

#endif
