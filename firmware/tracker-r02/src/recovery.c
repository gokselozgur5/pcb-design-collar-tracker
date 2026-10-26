#include "recovery.h"
#include <errno.h>
#include <limits.h>
#include <string.h>

static bool deadline(int64_t now, uint32_t budget, int64_t *end)
{
	if (now < 0 || !budget || now > INT64_MAX - budget) { return false; }
	*end = now + budget;
	return true;
}

bool lease_init(struct progress_lease *lease, int64_t now, uint32_t budget)
{
	*lease = (struct progress_lease){.phase = PHASE_BOOT};
	lease->failed = !deadline(now, budget, &lease->deadline);
	return !lease->failed;
}

bool lease_feed_allowed(struct progress_lease *lease, int64_t now)
{
	if (now < 0 || now >= lease->deadline) { lease->failed = true; }
	return !lease->failed;
}

bool lease_enter(struct progress_lease *lease, int64_t now,
		 enum tracker_phase phase, uint32_t budget)
{
	if (!lease_feed_allowed(lease, now)) { return false; }
	if ((unsigned)phase > PHASE_SERVICE || !deadline(now, budget, &lease->deadline)) {
		lease->failed = true;
		return false;
	}
	lease->phase = phase;
	return true;
}

void lease_fail(struct progress_lease *lease) { lease->failed = true; }

int dns_slot_begin(struct dns_slot *slot, int64_t now, uint32_t budget, uint32_t *ticket)
{
	if (slot->state != DNS_IDLE) { return -EBUSY; }
	if (!deadline(now, budget, &slot->deadline)) { return -EINVAL; }
	/* At most one worker exists; no ticket is reused while it can still publish. */
	*ticket = ++slot->generation;
	slot->state = DNS_PENDING;
	slot->result = -EINPROGRESS;
	memset(&slot->address, 0, sizeof(slot->address));
	return 0;
}

bool dns_slot_publish(struct dns_slot *slot, uint32_t ticket, int64_t now,
		      int result, const struct resolved_address *address)
{
	if (slot->generation != ticket ||
	    (slot->state != DNS_PENDING && slot->state != DNS_ABANDONED)) { return false; }
	if (slot->state == DNS_ABANDONED || now >= slot->deadline || now < 0) {
		/* The worker has finished and freed its SDK result. A new job is safe. */
		slot->state = DNS_IDLE;
		return false;
	}
	if (result == 0 && (!address || (address->version != 4 && address->version != 6))) {
		result = -EAFNOSUPPORT;
	}
	slot->result = result;
	if (result == 0) { slot->address = *address; }
	slot->state = DNS_READY;
	return true;
}

int dns_slot_poll(struct dns_slot *slot, uint32_t ticket, int64_t now,
		  struct resolved_address *address)
{
	if (slot->generation != ticket) { return -ESTALE; }
	if (slot->state == DNS_READY) {
		int result = slot->result;
		if (!result) { *address = slot->address; }
		slot->state = DNS_IDLE;
		return result;
	}
	if (slot->state == DNS_PENDING) {
		if (now >= slot->deadline || now < 0) {
			slot->state = DNS_ABANDONED;
			return -ETIMEDOUT;
		}
		return -EINPROGRESS;
	}
	/* IDLE here means completion was late and discarded; ABANDONED still owns
	 * the slot until the worker returns. Neither permits a stale address. */
	return -ETIMEDOUT;
}
