#include "uplink.h"
#include "dns.h"
#include "supervisor.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <modem/modem_key_mgmt.h>
#include <zephyr/net/http/client.h>
#include <zephyr/net/socket.h>
#include <zephyr/net/tls_credentials.h>

struct reply {
	char body[40];
	size_t length;
	bool complete;
	int status;
};

static int response(struct http_response *rsp, enum http_final_call final, void *context)
{
	struct reply *reply = context;
	if (rsp->body_frag_len > sizeof(reply->body) - reply->length) { return -EMSGSIZE; }
	if (rsp->body_frag_len) {
		memcpy(reply->body + reply->length, rsp->body_frag_start, rsp->body_frag_len);
		reply->length += rsp->body_frag_len;
	}
	reply->status = rsp->http_status_code;
	reply->complete = final == HTTP_DATA_FINAL && rsp->message_complete;
	return 0;
}

int uplink_configured(void)
{
	if (!tracker_device_id_valid(CONFIG_TRACKER_DEVICE_ID) || !CONFIG_TRACKER_HOST[0]) {
		return -ENOENT;
	}
	/* DNS name only: no URL, credentials, path, whitespace or injected headers. */
	size_t n = strlen(CONFIG_TRACKER_HOST);
	if (n > 253) { return -EINVAL; }
	for (size_t i = 0; i < n; ++i) {
		char c = CONFIG_TRACKER_HOST[i];
		if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
		    (c >= '0' && c <= '9') || c == '-' || c == '.')) { return -EINVAL; }
	}
	const enum modem_key_mgmt_cred_type types[] = {
		MODEM_KEY_MGMT_CRED_TYPE_CA_CHAIN, MODEM_KEY_MGMT_CRED_TYPE_PUBLIC_CERT,
		MODEM_KEY_MGMT_CRED_TYPE_PRIVATE_CERT,
	};
	for (size_t i = 0; i < sizeof(types) / sizeof(types[0]); ++i) {
		bool exists = false;
		int ret = modem_key_mgmt_exists(CONFIG_TRACKER_SEC_TAG, types[i], &exists);
		if (ret) { return ret; }
		if (!exists) { return -ENOENT; }
	}
	return 0;
}

int uplink_send(const struct position *p)
{
	char payload[384], port[6];
	int length = position_json(p, CONFIG_TRACKER_DEVICE_ID, payload, sizeof(payload));
	if (length < 0) { return length; }
	snprintf(port, sizeof(port), "%u", CONFIG_TRACKER_PORT);
	struct resolved_address address;
	supervisor_enter(PHASE_DNS, CONFIG_TRACKER_DNS_SECONDS * 1000U + 2000U);
	int ret = tracker_dns_lookup(&address);
	if (ret) { return ret; }
	struct sockaddr_storage peer = {0};
	socklen_t peer_size;
	int family;
	if (address.version == 4) {
		struct sockaddr_in *ip = (struct sockaddr_in *)&peer;
		family = AF_INET; peer_size = sizeof(*ip);
		ip->sin_family = family; ip->sin_port = htons(address.port);
		memcpy(&ip->sin_addr, address.bytes, 4);
	} else if (address.version == 6) {
		struct sockaddr_in6 *ip = (struct sockaddr_in6 *)&peer;
		family = AF_INET6; peer_size = sizeof(*ip);
		ip->sin6_family = family; ip->sin6_port = htons(address.port);
		ip->sin6_scope_id = address.scope_id;
		memcpy(&ip->sin6_addr, address.bytes, 16);
	} else { return -EAFNOSUPPORT; }
	int fd = -1;
	ret = -ECONNREFUSED;
	/* One address per cycle bounds connect attempts; dual-stack fallback needs
	 * field qualification. Never downgrade TLS or skip certificate validation. */
	supervisor_enter(PHASE_CONNECT, 35000);
	fd = zsock_socket(family, SOCK_STREAM, IPPROTO_TLS_1_2);
	if (fd < 0) { ret = -errno; goto done; }
	int verify = 2;
	sec_tag_t tag = CONFIG_TRACKER_SEC_TAG;
	struct timeval timeout = {.tv_sec = 30};
	if (zsock_setsockopt(fd, SOL_TLS, TLS_PEER_VERIFY, &verify, sizeof(verify)) ||
	    zsock_setsockopt(fd, SOL_TLS, TLS_SEC_TAG_LIST, &tag, sizeof(tag)) ||
	    zsock_setsockopt(fd, SOL_TLS, TLS_HOSTNAME, CONFIG_TRACKER_HOST,
			strlen(CONFIG_TRACKER_HOST)) ||
	    zsock_setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) ||
	    zsock_setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout))) {
		ret = -errno; goto done;
	}
	int flags = zsock_fcntl(fd, F_GETFL, 0);
	if (flags < 0 || zsock_fcntl(fd, F_SETFL, flags | O_NONBLOCK)) {
		ret = -errno; goto done;
	}
	if (zsock_connect(fd, (struct sockaddr *)&peer, peer_size) < 0) {
		if (errno != EINPROGRESS) { ret = -errno; goto done; }
		struct zsock_pollfd pending = {.fd = fd, .events = ZSOCK_POLLOUT};
		ret = zsock_poll(&pending, 1, 30000);
		if (ret <= 0) { ret = ret == 0 ? -ETIMEDOUT : -errno; goto done; }
		int error = 0;
		socklen_t size = sizeof(error);
		if (zsock_getsockopt(fd, SOL_SOCKET, SO_ERROR, &error, &size)) {
			ret = -errno; goto done;
		}
		if (error || !(pending.revents & ZSOCK_POLLOUT)) {
			ret = error ? -error : -ECONNABORTED; goto done;
		}
	}
	if (zsock_fcntl(fd, F_SETFL, flags)) {
		ret = -errno; goto done;
	}
	uint8_t receive[768];
	struct reply reply = {0};
	const char *headers[] = {"Connection: close\r\n", NULL};
	struct http_request request = {
		.method = HTTP_POST, .url = "/v1/positions", .protocol = "HTTP/1.1",
		.host = CONFIG_TRACKER_HOST, .port = port, .header_fields = headers,
		.content_type_value = "application/json", .payload = payload, .payload_len = length,
		.response = response, .recv_buf = receive, .recv_buf_len = sizeof(receive),
	};
	supervisor_enter(PHASE_HTTP, 35000);
	ret = http_client_req(fd, &request, 30000, &reply);
	if (ret >= 0) {
		ret = reply.complete && reply.status == 200 &&
		      tracker_ack_matches(reply.body, reply.length, p->sequence) ? 0 : -EBADMSG;
	}
done:
	supervisor_enter(PHASE_CLEANUP, 5000);
	if (fd >= 0) { zsock_close(fd); }
	return ret;
}
