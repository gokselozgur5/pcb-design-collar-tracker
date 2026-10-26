#include "trial.h"
#include "supervisor.h"
#include <zephyr/dfu/mcuboot.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

static struct trial_policy trial;
static struct k_spinlock lock;
K_SEM_DEFINE(trial_started, 0, 1);

static void monitor(void *a, void *b, void *c)
{
	ARG_UNUSED(a); ARG_UNUSED(b); ARG_UNUSED(c);
	k_sem_take(&trial_started, K_FOREVER);
	for (;;) {
		k_spinlock_key_t key = k_spin_lock(&lock);
		bool expired = trial_policy_expired(&trial, k_uptime_get());
		bool done = trial.state == TRIAL_CONFIRMED;
		k_spin_unlock(&lock, key);
		if (expired) { supervisor_reset("Firmware trial deadline expired; leave image unconfirmed"); }
		if (done) { return; }
		k_sleep(K_SECONDS(1));
	}
}
K_THREAD_DEFINE(trial_thread, 1024, monitor, NULL, NULL, NULL, 2, 0, 0);

void tracker_trial_init(void)
{
	/* MCUboot treats an initial image with an unset trailer as confirmed. */
	bool pending = !boot_is_img_confirmed();
	k_spinlock_key_t key = k_spin_lock(&lock);
	bool okay = trial_policy_init(&trial, k_uptime_get(), pending,
		CONFIG_TRACKER_TRIAL_SECONDS * 1000U, CONFIG_TRACKER_TRIAL_STABLE_SECONDS * 1000U);
	k_spin_unlock(&lock, key);
	if (!okay) { supervisor_reset("Invalid firmware trial configuration"); }
	if (pending) {
		printk("Firmware trial: require a fresh persisted fix and an acknowledged upload\n");
		k_sem_give(&trial_started);
	}
}

void tracker_trial_mark(enum trial_evidence evidence)
{
	k_spinlock_key_t key = k_spin_lock(&lock);
	trial_policy_mark(&trial, evidence);
	k_spin_unlock(&lock, key);
}

bool tracker_trial_pending(void)
{
	k_spinlock_key_t key = k_spin_lock(&lock);
	bool pending = trial.state == TRIAL_PENDING || trial.state == TRIAL_CONFIRMING;
	k_spin_unlock(&lock, key);
	return pending;
}

void tracker_trial_confirm_if_ready(void)
{
	k_spinlock_key_t key = k_spin_lock(&lock);
	enum trial_action action = trial_policy_decide(&trial, k_uptime_get());
	k_spin_unlock(&lock, key);
	if (action == TRIAL_RESET) { supervisor_reset("Firmware trial expired before confirmation"); }
	if (action != TRIAL_CONFIRM) { return; }
	supervisor_enter(PHASE_STORAGE, 10000);
	int ret = boot_write_img_confirmed();
	key = k_spin_lock(&lock);
	bool accepted = trial_policy_finish(&trial, k_uptime_get(), ret == 0);
	k_spin_unlock(&lock, key);
	if (!accepted) { supervisor_reset("Firmware trial confirmation failed"); }
	printk("Firmware trial confirmed\n");
}
