#include "outbox.h"

#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#define MAGIC UINT32_C(0x31525443)
#define RESERVATION UINT64_C(256)

static void put(uint8_t *p, uint64_t value, size_t n)
{
	for (size_t i = 0; i < n; ++i) { p[i] = (uint8_t)(value >> (8 * i)); }
}

static uint64_t get(const uint8_t *p, size_t n)
{
	uint64_t value = 0;
	for (size_t i = 0; i < n; ++i) { value |= (uint64_t)p[i] << (8 * i); }
	return value;
}

static uint32_t crc(const uint8_t *p, size_t n)
{
	uint32_t value = UINT32_MAX;
	for (size_t i = 0; i < n; ++i) {
		value ^= p[i];
		for (unsigned b = 0; b < 8; ++b) {
			value = (value >> 1) ^ (UINT32_C(0xedb88320) & (0U - (value & 1U)));
		}
	}
	return ~value;
}

static int hold(struct outbox *box, int error)
{
	box->healthy = false;
	return error;
}

bool position_valid(const struct position *p)
{
	/* 2020-01-01 through 2099-12-31. Never manufacture a timestamp. */
	return p->utc_ms >= UINT64_C(1577836800000) &&
	       p->utc_ms < UINT64_C(4102444800000) &&
	       p->latitude_e7 >= -900000000 && p->latitude_e7 <= 900000000 &&
	       p->longitude_e7 >= -1800000000 && p->longitude_e7 <= 1800000000 &&
	       p->accuracy_cm > 0 && p->accuracy_cm <= 100000000 &&
	       (p->battery_mv == 0 || (p->battery_mv >= 2000 && p->battery_mv <= 5000));
}

static int read_record(struct outbox *box, unsigned slot, struct position *p)
{
	uint8_t bytes[OUTBOX_RECORD_SIZE];
	int ret = box->io.read(box->io.context, OUTBOX_FIRST_KEY + slot, bytes, sizeof(bytes));
	if (ret == -ENOENT) { return ret; }
	if (ret < 0) { return hold(box, ret); }
	if (ret != sizeof(bytes) || get(bytes, 4) != MAGIC ||
	    get(bytes + 36, 4) != crc(bytes, 36) || get(bytes + 34, 2) != 0) {
		return hold(box, -EILSEQ);
	}
	p->sequence = get(bytes + 4, 8);
	p->utc_ms = get(bytes + 12, 8);
	/* Decode signed coordinates without implementation-defined unsigned casts. */
	int64_t lat = (int64_t)get(bytes + 20, 4);
	int64_t lon = (int64_t)get(bytes + 24, 4);
	if (lat > INT32_MAX) { lat -= INT64_C(4294967296); }
	if (lon > INT32_MAX) { lon -= INT64_C(4294967296); }
	p->latitude_e7 = (int32_t)lat;
	p->longitude_e7 = (int32_t)lon;
	p->accuracy_cm = get(bytes + 28, 4);
	p->battery_mv = get(bytes + 32, 2);
	if (!position_valid(p) || p->sequence == 0 || p->sequence >= box->limit) {
		return hold(box, -EILSEQ);
	}
	return 0;
}

int outbox_init(struct outbox *box, const struct outbox_io *io)
{
	if (!box || !io || !io->read || !io->write || !io->remove) { return -EINVAL; }
	*box = (struct outbox){ .io = *io };
	uint8_t meta[16];
	int ret = io->read(io->context, OUTBOX_META_KEY, meta, sizeof(meta));
	if (ret == -ENOENT) {
		box->limit = 1;
	} else if (ret < 0) {
		return ret;
	} else if (ret != sizeof(meta) || get(meta, 4) != MAGIC ||
		   get(meta + 12, 4) != crc(meta, 12) || get(meta + 4, 8) == 0) {
		return -EILSEQ;
	} else {
		box->limit = get(meta + 4, 8);
	}
	/* Burn unused IDs from the previous boot's reserved block. */
	box->next = box->limit;
	box->healthy = true;
	uint64_t seen[OUTBOX_CAPACITY];
	size_t count = 0;
	for (unsigned i = 0; i < OUTBOX_CAPACITY; ++i) {
		struct position p;
		ret = read_record(box, i, &p);
		if (ret == -ENOENT) { continue; }
		if (ret) { return ret; }
		for (size_t j = 0; j < count; ++j) {
			if (seen[j] == p.sequence) { return hold(box, -EILSEQ); }
		}
		seen[count++] = p.sequence;
	}
	return 0;
}

int outbox_enqueue(struct outbox *box, struct position *p)
{
	if (!box->healthy) { return -EIO; }
	if (!position_valid(p)) { return -EINVAL; }
	unsigned free_slot = OUTBOX_CAPACITY;
	for (unsigned i = 0; i < OUTBOX_CAPACITY; ++i) {
		struct position old;
		int ret = read_record(box, i, &old);
		if (ret == -ENOENT) { if (free_slot == OUTBOX_CAPACITY) { free_slot = i; } }
		else if (ret) { return ret; }
	}
	if (free_slot == OUTBOX_CAPACITY) { return -ENOSPC; }
	if (box->next == box->limit) {
		if (box->limit > UINT64_MAX - RESERVATION) { return hold(box, -EOVERFLOW); }
		uint8_t meta[16];
		uint64_t limit = box->limit + RESERVATION;
		put(meta, MAGIC, 4); put(meta + 4, limit, 8); put(meta + 12, crc(meta, 12), 4);
		int ret = box->io.write(box->io.context, OUTBOX_META_KEY, meta, sizeof(meta));
		if (ret != 0 && ret != sizeof(meta)) { return hold(box, ret < 0 ? ret : -EIO); }
		box->limit = limit;
	}
	p->sequence = box->next++;
	uint8_t bytes[OUTBOX_RECORD_SIZE] = {0};
	put(bytes, MAGIC, 4); put(bytes + 4, p->sequence, 8); put(bytes + 12, p->utc_ms, 8);
	put(bytes + 20, (uint32_t)p->latitude_e7, 4);
	put(bytes + 24, (uint32_t)p->longitude_e7, 4);
	put(bytes + 28, p->accuracy_cm, 4); put(bytes + 32, p->battery_mv, 2);
	put(bytes + 36, crc(bytes, 36), 4);
	int ret = box->io.write(box->io.context, OUTBOX_FIRST_KEY + free_slot, bytes, sizeof(bytes));
	return (ret == sizeof(bytes) || ret == 0) ? 0 : hold(box, ret < 0 ? ret : -EIO);
}

static int oldest(struct outbox *box, struct position *p, uint16_t *key)
{
	if (!box->healthy) { return -EIO; }
	bool found = false;
	for (unsigned i = 0; i < OUTBOX_CAPACITY; ++i) {
		struct position candidate;
		int ret = read_record(box, i, &candidate);
		if (ret == -ENOENT) { continue; }
		if (ret) { return ret; }
		if (!found || candidate.sequence < p->sequence) {
			*p = candidate; *key = OUTBOX_FIRST_KEY + i; found = true;
		}
	}
	return found ? 0 : -ENOENT;
}

int outbox_peek(struct outbox *box, struct position *p)
{
	uint16_t key;
	return oldest(box, p, &key);
}

int outbox_ack(struct outbox *box, uint64_t sequence)
{
	struct position p;
	uint16_t key;
	int ret = oldest(box, &p, &key);
	if (ret) { return ret; }
	if (p.sequence != sequence) { return -ESTALE; }
	ret = box->io.remove(box->io.context, key);
	return ret == 0 ? 0 : hold(box, ret < 0 ? ret : -EIO);
}

bool tracker_device_id_valid(const char *id)
{
	if (!id || !*id) { return false; }
	size_t n = 0;
	for (; id[n]; ++n) {
		char c = id[n];
		if (n >= 64 || !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
		    (c >= '0' && c <= '9') || c == '-' || c == '_')) { return false; }
	}
	return true;
}

int position_json(const struct position *p, const char *device, char *out, size_t size)
{
	if (!position_valid(p) || p->sequence == 0 || !tracker_device_id_valid(device)) {
		return -EINVAL;
	}
	int ret = snprintf(out, size,
		"{\"v\":1,\"device\":\"%s\",\"sequence\":\"%" PRIu64
		"\",\"utc_ms\":%" PRIu64 ",\"latitude_e7\":%" PRId32
		",\"longitude_e7\":%" PRId32 ",\"accuracy_cm\":%" PRIu32
		",\"battery_mv\":%u}", device, p->sequence, p->utc_ms,
		p->latitude_e7, p->longitude_e7, p->accuracy_cm, (unsigned)p->battery_mv);
	return ret < 0 ? -EIO : ((size_t)ret >= size ? -ENOSPC : ret);
}

bool tracker_ack_matches(const char *body, size_t size, uint64_t sequence)
{
	char expected[40];
	int n = snprintf(expected, sizeof(expected), "{\"ack\":\"%" PRIu64 "\"}", sequence);
	return n > 0 && size == (size_t)n && memcmp(expected, body, size) == 0;
}
