#include "dns.h"
#include <zephyr/kernel.h>
#include <zephyr/net/socket.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static pthread_mutex_t control = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t release_worker = PTHREAD_COND_INITIALIZER;
static bool blocked, error_with_result, ipv6;
static unsigned allocations, frees, calls;

int zsock_getaddrinfo(const char *host, const char *port, const struct addrinfo *hints,
		      struct addrinfo **out)
{
	assert(strcmp(host, "test.invalid") == 0 && strcmp(port, "443") == 0);
	assert(hints->ai_family == AF_UNSPEC);
	pthread_mutex_lock(&control);
	++calls;
	while (blocked) { pthread_cond_wait(&release_worker, &control); }
	struct addrinfo *result = calloc(1, sizeof(*result));
	assert(result);
	if (ipv6) {
		result->ai_family = AF_INET6;
		result->ai_addrlen = sizeof(struct sockaddr_in6);
		struct sockaddr_in6 *ip = calloc(1, result->ai_addrlen);
		assert(ip); ip->sin6_family = AF_INET6; ip->sin6_scope_id = 7;
		ip->sin6_addr.s6_addr[0] = 0x20; ip->sin6_addr.s6_addr[1] = 0x01;
		ip->sin6_addr.s6_addr[15] = 8;
		result->ai_addr = (struct sockaddr *)ip;
	} else {
		result->ai_family = AF_INET;
		result->ai_addrlen = sizeof(struct sockaddr_in);
		struct sockaddr_in *ip = calloc(1, result->ai_addrlen);
		assert(ip); ip->sin_family = AF_INET;
		const uint8_t bytes[] = {192, 0, 2, 9}; memcpy(&ip->sin_addr, bytes, 4);
		result->ai_addr = (struct sockaddr *)ip;
	}
	++allocations; *out = result;
	int ret = error_with_result ? EAI_FAIL : 0;
	pthread_mutex_unlock(&control);
	return ret;
}

void zsock_freeaddrinfo(struct addrinfo *result)
{
	assert(result && result->ai_addr);
	free(result->ai_addr); free(result);
	pthread_mutex_lock(&control); ++frees; pthread_mutex_unlock(&control);
}

int main(void)
{
	struct resolved_address address;
	assert(tracker_dns_lookup(&address) == 0);
	assert(address.version == 4 && address.port == 443 && address.bytes[3] == 9);
	assert(tracker_dns_wait_idle(20));
	pthread_mutex_lock(&control);
	assert(calls == 1 && allocations == 1 && frees == 1);
	blocked = true;
	pthread_mutex_unlock(&control);
	int64_t start = k_uptime_get();
	assert(tracker_dns_lookup(&address) == -ETIMEDOUT);
	int64_t elapsed = k_uptime_get() - start;
	assert(elapsed >= 950 && elapsed < 3000); /* Host uses a one-second test deadline. */
	assert(!tracker_dns_wait_idle(20));
	assert(tracker_dns_lookup(&address) == -EBUSY);
	pthread_mutex_lock(&control);
	assert(calls == 2 && allocations == 1 && frees == 1);
	ipv6 = true; blocked = false;
	pthread_cond_signal(&release_worker);
	pthread_mutex_unlock(&control);
	assert(tracker_dns_wait_idle(1000));
	pthread_mutex_lock(&control); assert(allocations == 2 && frees == 2); pthread_mutex_unlock(&control);
	memset(&address, 0, sizeof(address));
	assert(tracker_dns_lookup(&address) == 0);
	assert(address.version == 6 && address.scope_id == 7 && address.bytes[15] == 8);
	pthread_mutex_lock(&control); error_with_result = true; pthread_mutex_unlock(&control);
	assert(tracker_dns_lookup(&address) == -EHOSTUNREACH);
	assert(tracker_dns_wait_idle(20));
	pthread_mutex_lock(&control); assert(calls == 4 && allocations == 4 && frees == 4); pthread_mutex_unlock(&control);
	puts("PASS production DNS worker: timeout returns while worker remains owned; no second job overlaps");
	puts("PASS late success freed before reuse; fresh IPv6 answer preserved; error allocation also freed");
	printf("Observed host timeout: %lld ms; four allocations/four frees\n", (long long)elapsed);
	return 0;
}
