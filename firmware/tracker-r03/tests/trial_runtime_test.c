#include "trial.h"
#include "supervisor.h"
#include <zephyr/kernel.h>
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

atomic_llong trial_test_now = 100;
static atomic_int writes;
static bool factory;
static int write_error;
static int expected_writes;
static const char *expected_reason;

bool boot_is_img_confirmed(void) { return factory; }
int boot_write_img_confirmed(void) { atomic_fetch_add(&writes, 1); return write_error; }
void supervisor_enter(enum tracker_phase phase, uint32_t budget)
{
	assert(phase == PHASE_STORAGE && budget == 10000);
}
FUNC_NORETURN void supervisor_reset(const char *reason)
{
	assert(expected_reason && strstr(reason, expected_reason));
	assert(atomic_load(&writes) == expected_writes);
	printf("PASS production trial requests reset: %s; confirmation writes=%d\n", reason, expected_writes);
	exit(42); /* Deliberate host reset sentinel, not a physical watchdog reset. */
}

int main(int argc, char **argv)
{
	assert(argc == 2);
	factory = strcmp(argv[1], "factory") == 0;
	tracker_trial_init();
	assert(tracker_trial_pending() == !factory);
	if (strcmp(argv[1], "missing-ack") == 0) {
		expected_reason = "deadline expired";
		tracker_trial_mark(TRIAL_FIX_PERSISTED);
		atomic_store(&trial_test_now, 600100);
		k_sleep(K_SECONDS(3));
		abort(); /* Deadline monitor must request reset independently of main progress. */
	}
	tracker_trial_mark(TRIAL_UPLOAD_ACKNOWLEDGED);
	tracker_trial_confirm_if_ready();
	assert(atomic_load(&writes) == 0);
	tracker_trial_mark(TRIAL_FIX_PERSISTED);
	tracker_trial_confirm_if_ready();
	assert(atomic_load(&writes) == 0);
	if (strcmp(argv[1], "late-evidence") == 0) {
		expected_reason = "expired";
		atomic_store(&trial_test_now, 600100);
	} else {
		atomic_store(&trial_test_now, 30100);
	}
	if (strcmp(argv[1], "confirmation-failed") == 0) {
		write_error = -EIO;
		/* The independent monitor may observe the sticky failure first. */
		expected_reason = "Firmware trial";
		expected_writes = 1;
	}
	tracker_trial_confirm_if_ready();
	assert(!expected_reason);
	assert(atomic_load(&writes) == (factory ? 0 : 1));
	assert(!tracker_trial_pending());
	tracker_trial_confirm_if_ready();
	assert(atomic_load(&writes) == (factory ? 0 : 1));
	puts("PASS production trial confirms once after evidence; initial image is never rewritten");
	return 0;
}
