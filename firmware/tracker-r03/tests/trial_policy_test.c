#include "trial_policy.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>

int main(void)
{
	struct trial_policy p;
	assert(trial_policy_init(&p, 100, false, 600000, 30000));
	assert(trial_policy_decide(&p, INT64_MAX) == TRIAL_DONE);
	assert(trial_policy_init(&p, 100, true, 600000, 30000));
	assert(trial_policy_decide(&p, 30100) == TRIAL_WAIT);
	trial_policy_mark(&p, TRIAL_UPLOAD_ACKNOWLEDGED);
	assert(trial_policy_decide(&p, 30100) == TRIAL_WAIT);
	trial_policy_mark(&p, TRIAL_FIX_PERSISTED);
	assert(trial_policy_decide(&p, 30099) == TRIAL_WAIT);
	assert(trial_policy_decide(&p, 30100) == TRIAL_CONFIRM);
	assert(trial_policy_decide(&p, 30101) == TRIAL_WAIT);
	assert(trial_policy_finish(&p, 30102, true));
	assert(trial_policy_decide(&p, 900000) == TRIAL_DONE);
	puts("PASS initial image remains stable; trial needs fresh storage, server ACK and minimum uptime");

	assert(trial_policy_init(&p, 100, true, 600000, 30000));
	trial_policy_mark(&p, TRIAL_FIX_PERSISTED);
	assert(trial_policy_decide(&p, 600099) == TRIAL_WAIT);
	assert(trial_policy_decide(&p, 600100) == TRIAL_RESET);
	trial_policy_mark(&p, TRIAL_UPLOAD_ACKNOWLEDGED);
	assert(trial_policy_decide(&p, 30100) == TRIAL_RESET);
	assert(!trial_policy_finish(&p, 30101, true));
	puts("PASS lost ACK causes expiry; late evidence and a late completion cannot clear failure");

	for (int delta = -1; delta <= 1; ++delta) {
		assert(trial_policy_init(&p, 100, true, 600000, 30000));
		trial_policy_mark(&p, TRIAL_FIX_PERSISTED);
		trial_policy_mark(&p, TRIAL_UPLOAD_ACKNOWLEDGED);
		assert(trial_policy_decide(&p, 585100 + delta) == (delta <= 0 ? TRIAL_CONFIRM : TRIAL_WAIT));
	}
	assert(trial_policy_init(&p, 100, true, 600000, 30000));
	trial_policy_mark(&p, TRIAL_FIX_PERSISTED);
	trial_policy_mark(&p, TRIAL_UPLOAD_ACKNOWLEDGED);
	assert(trial_policy_decide(&p, 30100) == TRIAL_CONFIRM);
	assert(!trial_policy_finish(&p, 30101, false));
	assert(trial_policy_decide(&p, 30102) == TRIAL_RESET);
	assert(!trial_policy_init(&p, INT64_MAX-1, true, 600000, 30000));
	assert(!trial_policy_init(&p, -1, true, 600000, 30000));
	assert(!trial_policy_init(&p, 0, true, 45000, 30000));
	puts("PASS confirmation write margin, failure latch and deadline overflow guards");
	return 0;
}
