#ifndef COLLAR_TRIAL_POLICY_H
#define COLLAR_TRIAL_POLICY_H
#include <stdbool.h>
#include <stdint.h>

enum trial_state { TRIAL_CONFIRMED, TRIAL_PENDING, TRIAL_CONFIRMING, TRIAL_FAILED };
enum trial_action { TRIAL_WAIT, TRIAL_CONFIRM, TRIAL_RESET, TRIAL_DONE };
enum trial_evidence { TRIAL_FIX_PERSISTED = 1, TRIAL_UPLOAD_ACKNOWLEDGED = 2 };
struct trial_policy {
	enum trial_state state;
	int64_t deadline, earliest;
	unsigned evidence;
};
/* Caller serializes every access. A factory image with no trial is already stable. */
bool trial_policy_init(struct trial_policy *p, int64_t now, bool pending,
		       uint32_t budget_ms, uint32_t stable_ms);
bool trial_policy_expired(struct trial_policy *p, int64_t now);
void trial_policy_mark(struct trial_policy *p, enum trial_evidence evidence);
enum trial_action trial_policy_decide(struct trial_policy *p, int64_t now);
bool trial_policy_finish(struct trial_policy *p, int64_t now, bool success);
#endif
