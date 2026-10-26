#include "outbox.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>

struct memory {
	unsigned char bytes[320][40];
	int lengths[320];
	int fail_at;
	int mutations;
	bool commit_failure;
};
static struct memory mem;

static int read_value(void *ctx, uint16_t key, void *out, size_t n)
{
	struct memory *m = ctx;
	assert(key < 320);
	int size = m->lengths[key];
	if (!size) { return -ENOENT; }
	memcpy(out, m->bytes[key], (size_t)size < n ? (size_t)size : n);
	return size;
}
static int write_value(void *ctx, uint16_t key, const void *in, size_t n)
{
	struct memory *m = ctx;
	assert(key < 320 && n <= 40);
	bool fail = ++m->mutations == m->fail_at;
	if (!fail || m->commit_failure) {
		memcpy(m->bytes[key], in, n); m->lengths[key] = (int)n;
	}
	return fail ? -EIO : (int)n;
}
static int remove_value(void *ctx, uint16_t key)
{
	struct memory *m = ctx;
	bool fail = ++m->mutations == m->fail_at;
	if (!fail || m->commit_failure) { m->lengths[key] = 0; }
	return fail ? -EIO : 0;
}
static const struct outbox_io io = { &mem, read_value, write_value, remove_value };
static struct position fix(void)
{
	return (struct position){.utc_ms = 1792978382000, .latitude_e7 = -339000000,
		.longitude_e7 = 1512000000, .accuracy_cm = 1234, .battery_mv = 3999};
}

int main(int argc, char **argv)
{
	struct outbox box;
	struct position p = fix(), got;
	if (argc == 2 && strcmp(argv[1], "--payload") == 0) {
		char payload[384]; p.sequence = UINT64_C(9007199254740993);
		assert(position_json(&p, "collar-01", payload, sizeof(payload)) > 0);
		puts(payload); return 0;
	}
	assert(outbox_init(&box, &io) == 0);
	assert(outbox_peek(&box, &got) == -ENOENT);
	assert(outbox_enqueue(&box, &p) == 0 && p.sequence == 1);
	assert(outbox_init(&box, &io) == 0);
	assert(outbox_peek(&box, &got) == 0 && got.sequence == 1);
	assert(got.latitude_e7 == p.latitude_e7 && got.longitude_e7 == p.longitude_e7);
	assert(outbox_enqueue(&box, &p) == 0 && p.sequence == 257);
	assert(outbox_ack(&box, 257) == -ESTALE);
	assert(outbox_peek(&box, &got) == 0 && got.sequence == 1);
	assert(outbox_ack(&box, 1) == 0);
	assert(outbox_peek(&box, &got) == 0 && got.sequence == 257);
	assert(outbox_ack(&box, 257) == 0);
	assert(outbox_init(&box, &io) == 0);
	assert(outbox_enqueue(&box, &p) == 0 && p.sequence == 513);
	puts("PASS reboot replay, signed coordinates, stale ACK, non-reused IDs");

	memset(&mem, 0, sizeof(mem));
	assert(outbox_init(&box, &io) == 0);
	for (int i = 0; i < OUTBOX_CAPACITY; ++i) { assert(outbox_enqueue(&box, &p) == 0); }
	assert(outbox_enqueue(&box, &p) == -ENOSPC);
	for (int i = 1; i <= OUTBOX_CAPACITY; ++i) {
		assert(outbox_peek(&box, &got) == 0 && got.sequence == (uint64_t)i);
		assert(outbox_ack(&box, got.sequence) == 0);
	}
	assert(outbox_peek(&box, &got) == -ENOENT);
	puts("PASS full queue retains oldest records and drains in order");

	/* NVS mutations can fail before or after committing. Recreate the process
	 * after each metadata, record and deletion failure; never repair by erase. */
	for (int mutation = 1; mutation <= 3; ++mutation) {
		for (int committed = 0; committed <= 1; ++committed) {
			memset(&mem, 0, sizeof(mem));
			mem.fail_at = mutation; mem.commit_failure = committed;
			assert(outbox_init(&box, &io) == 0);
			int ret = outbox_enqueue(&box, &p);
			if (mutation <= 2) { assert(ret == -EIO); }
			else { assert(ret == 0); assert(outbox_ack(&box, p.sequence) == -EIO); }
			assert(outbox_enqueue(&box, &p) == -EIO);
			mem.fail_at = 0;
			assert(outbox_init(&box, &io) == 0);
			ret = outbox_peek(&box, &got);
			bool saved = (mutation == 2 && committed) || (mutation == 3 && !committed);
			assert(ret == (saved ? 0 : -ENOENT));
			if (saved) { assert(got.sequence == 1); assert(outbox_ack(&box, 1) == 0); }
			assert(outbox_enqueue(&box, &p) == 0);
			assert(p.sequence == ((mutation == 1 && !committed) ? 1 : 257));
		}
	}
	puts("PASS six crash boundaries preserve committed records and sequence ownership");

	for (int byte = 0; byte < OUTBOX_RECORD_SIZE; ++byte) {
		memset(&mem, 0, sizeof(mem));
		assert(outbox_init(&box, &io) == 0); assert(outbox_enqueue(&box, &p) == 0);
		mem.bytes[OUTBOX_FIRST_KEY][byte] ^= 1;
		assert(outbox_init(&box, &io) == -EILSEQ && !box.healthy);
		assert(mem.lengths[OUTBOX_FIRST_KEY] == OUTBOX_RECORD_SIZE);
	}
	memset(&mem, 0, sizeof(mem));
	assert(outbox_init(&box, &io) == 0); assert(outbox_enqueue(&box, &p) == 0);
	mem.lengths[OUTBOX_META_KEY] = 0;
	assert(outbox_init(&box, &io) == -EILSEQ);
	puts("PASS all record-byte corruptions and missing metadata stop without erasing");

	char json[384];
	p = fix(); p.sequence = UINT64_MAX;
	assert(position_json(&p, "collar-01", json, sizeof(json)) > 0);
	assert(strstr(json, "\"sequence\":\"18446744073709551615\""));
	assert(position_json(&p, "bad\"id", json, sizeof(json)) == -EINVAL);
	assert(position_json(&p, "collar-01", json, 10) == -ENOSPC);
	assert(tracker_ack_matches("{\"ack\":\"1\"}", 11, 1));
	assert(!tracker_ack_matches("{\"ack\":\"2\"}", 11, 1));
	assert(!tracker_ack_matches("{\"ack\":\"1\"}junk", 15, 1));
	assert(!tracker_ack_matches("{\"ack\":\"1\"}", 10, 1));
	p.utc_ms = 0; assert(!position_valid(&p));
	p = fix(); p.latitude_e7 = INT32_MAX; assert(!position_valid(&p));
	puts("PASS strict ACK, JSON size/identity validation and invalid fixes");
	return 0;
}
