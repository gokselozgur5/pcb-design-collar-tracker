#include "recovery.h"
#include <assert.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
	struct progress_lease lease;
	assert(lease_init(&lease, 100, 30000));
	assert(lease_feed_allowed(&lease, 30099));
	assert(!lease_feed_allowed(&lease, 30100));
	assert(!lease_enter(&lease, 30100, PHASE_SLEEP, 300000));
	assert(!lease_feed_allowed(&lease, 101)); /* Expiry cannot be undone by a late caller. */
	assert(lease_init(&lease, 0, 10));
	assert(lease_enter(&lease, 9, PHASE_DNS, 30000));
	assert(lease_feed_allowed(&lease, 30008));
	assert(!lease_enter(&lease, 30009, PHASE_HTTP, 35000));
	assert(lease_init(&lease, 0, 100));
	lease_fail(&lease);
	assert(!lease_enter(&lease, 1, PHASE_SLEEP, 86400000));
	assert(!lease_init(&lease, INT64_MAX-1, 2));
	assert(!lease_init(&lease, 0, 0));
	assert(lease_init(&lease, 0, 100));
	assert(!lease_enter(&lease, 1, (enum tracker_phase)-1, 100));
	assert(lease_init(&lease, 0, 100));
	assert(!lease_enter(&lease, 1, (enum tracker_phase)(PHASE_SERVICE+1), 100));
	assert(lease_init(&lease, 0, 100));
	assert(lease_enter(&lease, 1, PHASE_SLEEP, 86405000));
	assert(lease_feed_allowed(&lease, 86405000));
	assert(!lease_feed_allowed(&lease, 86405001));
	puts("PASS watchdog deadline edges, sticky failure, long sleep and overflow guards");

	struct dns_slot slot = {0};
	struct resolved_address address = {.version=4, .port=443, .bytes={192,0,2,1}}, got;
	uint32_t ticket, next;
	assert(dns_slot_begin(&slot, 0, 30000, &ticket) == 0);
	assert(dns_slot_begin(&slot, 1, 30000, &next) == -EBUSY);
	assert(dns_slot_poll(&slot, ticket, 29999, &got) == -EINPROGRESS);
	assert(dns_slot_poll(&slot, ticket, 30000, &got) == -ETIMEDOUT);
	assert(slot.state == DNS_ABANDONED);
	assert(dns_slot_begin(&slot, 30001, 30000, &next) == -EBUSY);
	assert(!dns_slot_publish(&slot, ticket, 30002, 0, &address));
	assert(slot.state == DNS_IDLE);
	assert(dns_slot_begin(&slot, 30003, 30000, &next) == 0 && next != ticket);
	assert(!dns_slot_publish(&slot, ticket, 30004, 0, &address));
	assert(dns_slot_poll(&slot, ticket, 30004, &got) == -ESTALE);
	assert(dns_slot_poll(&slot, next, 30004, &got) == -EINPROGRESS);
	assert(dns_slot_publish(&slot, next, 30005, 0, &address));
	assert(dns_slot_poll(&slot, next, 30006, &got) == 0);
	assert(memcmp(&address, &got, sizeof(got)) == 0 && slot.state == DNS_IDLE);
	puts("PASS pending job ownership, timeout quarantine, late cleanup and stale ticket rejection");

	/* Both sides of the deadline race: completion before deadline may be taken
	 * after scheduler delay; completion at/after deadline is discarded. */
	for (int delay = -1; delay <= 1; ++delay) {
		assert(dns_slot_begin(&slot, 100, 100, &ticket) == 0);
		bool published = dns_slot_publish(&slot, ticket, 200+delay, 0, &address);
		assert(published == (delay < 0));
		assert(dns_slot_poll(&slot, ticket, 205, &got) == (delay < 0 ? 0 : -ETIMEDOUT));
	}
	assert(dns_slot_begin(&slot, 100, 100, &ticket) == 0);
	assert(dns_slot_publish(&slot, ticket, 150, -EHOSTUNREACH, NULL));
	assert(dns_slot_poll(&slot, ticket, 151, &got) == -EHOSTUNREACH);
	assert(dns_slot_begin(&slot, 100, 100, &ticket) == 0);
	assert(dns_slot_publish(&slot, ticket, 150, 0, NULL));
	assert(dns_slot_poll(&slot, ticket, 151, &got) == -EAFNOSUPPORT);
	assert(dns_slot_begin(&slot, INT64_MAX-1, 2, &ticket) == -EINVAL);
	puts("PASS completion/deadline races, resolver errors and malformed addresses");
	/* Enumerate worker completion versus caller timeout at every millisecond
	 * around the boundary, both possible orders under the production lock. */
	unsigned cases = 0;
	for (int completion=28; completion<=32; ++completion) {
		for (int poll=28; poll<=32; ++poll) {
			for (int first=0; first<2; ++first) {
				slot = (struct dns_slot){0};
				assert(dns_slot_begin(&slot, 0, 30, &ticket) == 0);
				if (first == 0 && completion <= poll) {
					(void)dns_slot_publish(&slot, ticket, completion, 0, &address);
					int ret = dns_slot_poll(&slot, ticket, poll, &got);
					assert(ret == (completion < 30 ? 0 : -ETIMEDOUT));
					++cases;
				} else if (first == 1 && poll <= completion) {
					int ret = dns_slot_poll(&slot, ticket, poll, &got);
					assert(ret == (poll < 30 ? -EINPROGRESS : -ETIMEDOUT));
					bool accepted = dns_slot_publish(&slot, ticket, completion, 0, &address);
					assert(accepted == (completion < 30 && poll < 30));
					++cases;
				}
			}
		}
	}
	assert(cases == 30);
	printf("PASS %u ordered DNS deadline interleavings\n", cases);
	return 0;
}
