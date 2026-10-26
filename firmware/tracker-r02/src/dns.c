#include "dns.h"
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/net/socket.h>

static struct dns_slot slot;
static struct k_spinlock slot_lock;
K_SEM_DEFINE(dns_request, 0, 1);
K_SEM_DEFINE(dns_done, 0, 1);

static void resolver(void *a, void *b, void *c)
{
	ARG_UNUSED(a); ARG_UNUSED(b); ARG_UNUSED(c);
	for (;;) {
		k_sem_take(&dns_request, K_FOREVER);
		k_spinlock_key_t key = k_spin_lock(&slot_lock);
		uint32_t ticket = slot.generation;
		k_spin_unlock(&slot_lock, key);
		char port[6];
		snprintf(port, sizeof(port), "%u", CONFIG_TRACKER_PORT);
		struct zsock_addrinfo hints = {.ai_family = AF_UNSPEC, .ai_socktype = SOCK_STREAM};
		struct zsock_addrinfo *addresses = NULL;
		struct resolved_address result = {.port = CONFIG_TRACKER_PORT};
		int ret = zsock_getaddrinfo(CONFIG_TRACKER_HOST, port, &hints, &addresses);
		if (ret) { ret = -EHOSTUNREACH; }
		else if (!addresses || !addresses->ai_addr) { ret = -EHOSTUNREACH; }
		else if (addresses->ai_family == AF_INET &&
			 addresses->ai_addrlen >= sizeof(struct sockaddr_in)) {
			const struct sockaddr_in *ip = (const struct sockaddr_in *)addresses->ai_addr;
			result.version = 4;
			memcpy(result.bytes, &ip->sin_addr, 4);
		} else if (addresses->ai_family == AF_INET6 &&
			   addresses->ai_addrlen >= sizeof(struct sockaddr_in6)) {
			const struct sockaddr_in6 *ip = (const struct sockaddr_in6 *)addresses->ai_addr;
			result.version = 6;
			memcpy(result.bytes, &ip->sin6_addr, 16);
			result.scope_id = ip->sin6_scope_id;
		} else { ret = -EAFNOSUPPORT; }
		/* The same worker always releases SDK memory, including late responses.
		 * Main never aborts this thread or accesses the returned pointer. */
		if (addresses) { zsock_freeaddrinfo(addresses); }
		key = k_spin_lock(&slot_lock);
		(void)dns_slot_publish(&slot, ticket, k_uptime_get(), ret, &result);
		k_spin_unlock(&slot_lock, key);
		k_sem_give(&dns_done);
	}
}
K_THREAD_DEFINE(resolver_thread, 2048, resolver, NULL, NULL, NULL, 6, 0, 0);

int tracker_dns_lookup(struct resolved_address *address)
{
	int64_t now = k_uptime_get();
	int64_t end = now + CONFIG_TRACKER_DNS_SECONDS * INT64_C(1000);
	uint32_t ticket;
	k_sem_reset(&dns_done);
	k_spinlock_key_t key = k_spin_lock(&slot_lock);
	int ret = dns_slot_begin(&slot, now, CONFIG_TRACKER_DNS_SECONDS * 1000U, &ticket);
	k_spin_unlock(&slot_lock, key);
	if (ret) { return ret; }
	k_sem_give(&dns_request);
	for (;;) {
		key = k_spin_lock(&slot_lock);
		ret = dns_slot_poll(&slot, ticket, k_uptime_get(), address);
		k_spin_unlock(&slot_lock, key);
		if (ret != -EINPROGRESS) { return ret; }
		int64_t remaining = end - k_uptime_get();
		if (remaining > 0) { (void)k_sem_take(&dns_done, K_MSEC(remaining)); }
	}
}

bool tracker_dns_wait_idle(uint32_t timeout_ms)
{
	int64_t end = k_uptime_get() + timeout_ms;
	for (;;) {
		k_spinlock_key_t key = k_spin_lock(&slot_lock);
		bool idle = slot.state == DNS_IDLE;
		k_spin_unlock(&slot_lock, key);
		if (idle) { return true; }
		int64_t remaining = end - k_uptime_get();
		if (remaining <= 0) { return false; }
		(void)k_sem_take(&dns_done, K_MSEC(remaining));
	}
}
