#ifndef COLLAR_HOST_SOCKET_H
#define COLLAR_HOST_SOCKET_H
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>
#define zsock_addrinfo addrinfo
int zsock_getaddrinfo(const char *, const char *, const struct addrinfo *, struct addrinfo **);
void zsock_freeaddrinfo(struct addrinfo *);
#endif
