#ifndef COLLAR_HOST_KERNEL_H
#define COLLAR_HOST_KERNEL_H
/* POSIX scheduling adapter for the production DNS worker, not a Zephyr emulator. */
#include <assert.h>
#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <time.h>

#define ARG_UNUSED(x) (void)(x)
typedef int64_t k_timeout_t;
#define K_FOREVER INT64_C(-1)
#define K_MSEC(ms) ((k_timeout_t)(ms))
#define K_SECONDS(s) ((k_timeout_t)(s) * 1000)
#define K_NO_WAIT INT64_C(0)
struct k_spinlock { atomic_int locked; };
typedef int k_spinlock_key_t;
static inline k_spinlock_key_t k_spin_lock(struct k_spinlock *s)
{
	while (atomic_exchange(&s->locked, 1)) { sched_yield(); }
	return 0;
}
static inline void k_spin_unlock(struct k_spinlock *s, k_spinlock_key_t key)
{
	(void)key; atomic_store(&s->locked, 0);
}
struct k_sem { pthread_mutex_t mutex; pthread_cond_t changed; unsigned count, limit; };
#define K_SEM_DEFINE(name, initial, maximum) \
	struct k_sem name = {PTHREAD_MUTEX_INITIALIZER, PTHREAD_COND_INITIALIZER, initial, maximum}
static inline void k_sem_give(struct k_sem *s)
{
	pthread_mutex_lock(&s->mutex);
	if (s->count < s->limit) { ++s->count; }
	pthread_cond_signal(&s->changed);
	pthread_mutex_unlock(&s->mutex);
}
static inline void k_sem_reset(struct k_sem *s)
{
	pthread_mutex_lock(&s->mutex); s->count = 0; pthread_mutex_unlock(&s->mutex);
}
static inline int k_sem_take(struct k_sem *s, k_timeout_t timeout)
{
	struct timespec end;
	clock_gettime(CLOCK_REALTIME, &end);
	if (timeout > 0) {
		end.tv_sec += timeout / 1000;
		end.tv_nsec += (timeout % 1000) * 1000000;
		if (end.tv_nsec >= 1000000000) { ++end.tv_sec; end.tv_nsec -= 1000000000; }
	}
	pthread_mutex_lock(&s->mutex);
	while (!s->count) {
		int ret = timeout == K_FOREVER ? pthread_cond_wait(&s->changed, &s->mutex) :
			(timeout == 0 ? ETIMEDOUT : pthread_cond_timedwait(&s->changed, &s->mutex, &end));
		if (ret) { pthread_mutex_unlock(&s->mutex); return -EAGAIN; }
	}
	--s->count;
	pthread_mutex_unlock(&s->mutex);
	return 0;
}
static inline int64_t k_uptime_get(void)
{
	struct timespec now; clock_gettime(CLOCK_MONOTONIC, &now);
	return now.tv_sec * INT64_C(1000) + now.tv_nsec / 1000000;
}
static inline void k_sleep(k_timeout_t timeout)
{
	struct timespec delay = {.tv_sec = timeout < 0 ? 3600 : timeout / 1000,
		.tv_nsec = timeout < 0 ? 0 : (timeout % 1000) * 1000000};
	if (timeout < 0) { for (;;) { nanosleep(&delay, NULL); } }
	while (nanosleep(&delay, &delay) != 0) { assert(errno == EINTR); }
}
#define K_THREAD_DEFINE(name, stack, entry, a, b, c, priority, options, delay) \
	static void *name##_wrapper(void *arg) { (void)arg; entry(a,b,c); return NULL; } \
	static void __attribute__((constructor)) name##_start(void) { \
		pthread_t id; assert(pthread_create(&id, NULL, name##_wrapper, NULL) == 0); \
		assert(pthread_detach(id) == 0); }

#endif
