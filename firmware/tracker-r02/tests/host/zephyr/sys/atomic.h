#ifndef COLLAR_HOST_ATOMIC_H
#define COLLAR_HOST_ATOMIC_H
#include <stdatomic.h>
typedef atomic_int atomic_t;
static inline void atomic_set(atomic_t *value, int next) { atomic_store(value, next); }
static inline int atomic_get(const atomic_t *value) { return atomic_load(value); }
#endif
