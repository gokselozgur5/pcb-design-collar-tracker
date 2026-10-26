#ifndef COLLAR_TRIAL_H
#define COLLAR_TRIAL_H
#include "trial_policy.h"
void tracker_trial_init(void);
void tracker_trial_mark(enum trial_evidence evidence);
void tracker_trial_confirm_if_ready(void);
bool tracker_trial_pending(void);
#endif
