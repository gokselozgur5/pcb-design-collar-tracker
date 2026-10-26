#ifndef COLLAR_OUTBOX_H
#define COLLAR_OUTBOX_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define OUTBOX_CAPACITY 64
#define OUTBOX_RECORD_SIZE 40
#define OUTBOX_META_KEY 1
#define OUTBOX_FIRST_KEY 256

struct position {
	uint64_t sequence;
	uint64_t utc_ms;
	int32_t latitude_e7;
	int32_t longitude_e7;
	uint32_t accuracy_cm;
	uint16_t battery_mv; /* Zero means unavailable. */
};

/* Read: exact byte count or -ENOENT. Write: exact count (zero for unchanged).
 * Remove: zero. A failed mutation makes this instance unusable until reboot. */
struct outbox_io {
	void *context;
	int (*read)(void *, uint16_t, void *, size_t);
	int (*write)(void *, uint16_t, const void *, size_t);
	int (*remove)(void *, uint16_t);
};

struct outbox {
	struct outbox_io io;
	uint64_t next;
	uint64_t limit;
	bool healthy;
};

int outbox_init(struct outbox *, const struct outbox_io *);
int outbox_enqueue(struct outbox *, struct position *);
int outbox_peek(struct outbox *, struct position *);
int outbox_ack(struct outbox *, uint64_t);
bool position_valid(const struct position *);
bool tracker_device_id_valid(const char *);
int position_json(const struct position *, const char *, char *, size_t);
bool tracker_ack_matches(const char *, size_t, uint64_t);

#endif
