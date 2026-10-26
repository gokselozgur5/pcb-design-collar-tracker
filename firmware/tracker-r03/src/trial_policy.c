#include "trial_policy.h"
#include <limits.h>

bool trial_policy_init(struct trial_policy *p, int64_t now, bool pending,
		       uint32_t budget_ms, uint32_t stable_ms)
{
	*p = (struct trial_policy){.state = pending ? TRIAL_PENDING : TRIAL_CONFIRMED};
	if (!pending) { return true; }
	if (now < 0 || budget_ms <= stable_ms || budget_ms - stable_ms <= 15000 ||
	    now > INT64_MAX - budget_ms) {
		p->state = TRIAL_FAILED;
		return false;
	}
	p->deadline = now + budget_ms;
	p->earliest = now + stable_ms;
	return true;
}

bool trial_policy_expired(struct trial_policy *p, int64_t now)
{
	if (p->state != TRIAL_CONFIRMED && (now < 0 || now >= p->deadline)) {
		p->state = TRIAL_FAILED;
	}
	return p->state == TRIAL_FAILED;
}

void trial_policy_mark(struct trial_policy *p, enum trial_evidence evidence)
{
	if (p->state == TRIAL_PENDING) {
		p->evidence |= (unsigned)evidence & (TRIAL_FIX_PERSISTED | TRIAL_UPLOAD_ACKNOWLEDGED);
	}
}

enum trial_action trial_policy_decide(struct trial_policy *p, int64_t now)
{
	if (trial_policy_expired(p, now)) { return TRIAL_RESET; }
	if (p->state == TRIAL_CONFIRMED) { return TRIAL_DONE; }
	if (p->state != TRIAL_PENDING || now < p->earliest || p->deadline - now < 15000 ||
	    p->evidence != (TRIAL_FIX_PERSISTED | TRIAL_UPLOAD_ACKNOWLEDGED)) { return TRIAL_WAIT; }
	/* Allow 10s for the flash write with another 5s before the trial deadline. */
	p->state = TRIAL_CONFIRMING;
	return TRIAL_CONFIRM;
}

bool trial_policy_finish(struct trial_policy *p, int64_t now, bool success)
{
	if (trial_policy_expired(p, now) || p->state != TRIAL_CONFIRMING || !success) {
		p->state = TRIAL_FAILED;
		return false;
	}
	p->state = TRIAL_CONFIRMED;
	return true;
}
