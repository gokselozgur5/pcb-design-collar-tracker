# Local position receiver

`receiver.py` is a standard-library HTTPS reference service bound to `127.0.0.1`.
It is not a public deployment and the cellular device cannot reach this loopback
address. It provides a concrete protocol and a local integration test target.

`POST /v1/positions` requires a trusted client certificate and `application/json`.
The certificate's single common name must equal `device` in the payload. A strict
schema bounds values and rejects duplicate fields, floats in integer fields,
unknown fields, oversized bodies and noncanonical sequence numbers.

```json
{"v":1,"device":"collar-01","sequence":"9007199254740993","utc_ms":1792978382000,"latitude_e7":-339000000,"longitude_e7":1512000000,"accuracy_cm":1234,"battery_mv":3999}
```

The sequence is a decimal **string**, preserving all 64 bits. Latitude/longitude
use degrees times 10^7; accuracy is centimeters; battery voltage is millivolts
(zero means unavailable). UTC is Unix milliseconds. Example coordinates are test
data. The service commits to SQLite with `synchronous=FULL` before returning:

```json
{"ack":"9007199254740993"}
```

The response is exactly that compact JSON, with no trailing newline. The same
device/sequence/payload can be retried safely; a changed payload reusing the same
sequence gets HTTP 409. There is no unauthenticated or plaintext HTTP fallback.

Run the [tracker tests](../tracker/README.md) to generate disposable test
certificates inside the ignored runtime directory, start a temporary local server,
exercise the actual C payload, and shut down. No persistent service is started by
the tests and no test private key is committed. `cryptography` is needed only for
test certificate generation, using the pinned tracker Python environment.

For manual local use, supply your own local test certificates and an ignored
database path; do not put production keys in this repository:

```sh
python3 firmware/receiver/receiver.py \
  --cert /absolute/test/server.pem --key /absolute/test/server.key \
  --client-ca /absolute/test/ca.pem \
  --database /Users/gok/codex/projects/collar-tracker/.runtime/positions.sqlite3
```

Private-location storage access, retention/deletion, enrollment/revocation, backups,
rate limits, observability and a production hosting decision remain open. This
single-process reference has five-second socket timeouts and no production
availability or throughput claims. A new device identity is required after wiping
its sequence storage; reusing an old identity would cause conflicts with retained
server records.
