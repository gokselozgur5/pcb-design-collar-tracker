"""Exercise the actual C payload over local TLS with disposable test credentials."""
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import sqlite3
import ssl
import subprocess
import tempfile
import threading
import unittest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from receiver import Receiver, Store, tls_context, validate

ROOT = Path(__file__).resolve().parents[2]


def certificates(directory):
    now = datetime.now(timezone.utc)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Disposable collar test CA')])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=1))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False),
                         critical=True).sign(ca_key, hashes.SHA256()))
    (directory/'ca.pem').write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    for label, name, usage in [('server', 'localhost', ExtendedKeyUsageOID.SERVER_AUTH),
                                ('client', 'collar-01', ExtendedKeyUsageOID.CLIENT_AUTH)]:
        key = ec.generate_private_key(ec.SECP256R1())
        builder = (x509.CertificateBuilder()
                   .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
                   .issuer_name(ca_name).public_key(key.public_key())
                   .serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=1))
                   .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                   .add_extension(x509.ExtendedKeyUsage([usage]), critical=False)
                   .add_extension(x509.SubjectAlternativeName([x509.DNSName(name)]), critical=False))
        cert = builder.sign(ca_key, hashes.SHA256())
        key_path = directory/(label+'.key')
        key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        key_path.chmod(0o600)
        (directory/(label+'.pem')).write_bytes(cert.public_bytes(serialization.Encoding.PEM))


class ReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runtime = ROOT/'.runtime/tracker-r01'
        runtime.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='receiver-', dir=runtime)
        cls.directory = Path(cls.temp.name)
        certificates(cls.directory)
        cls.store = Store(cls.directory/'positions.sqlite3')
        d = cls.directory
        cls.server = Receiver(('127.0.0.1', 0), tls_context(d/'server.pem', d/'server.key', d/'ca.pem'),
                              cls.store)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.payload = subprocess.check_output([str(runtime/'outbox-test'), '--payload']).strip()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def request(self, payload=None, authenticated=True, headers=None):
        d = self.directory
        context = ssl.create_default_context(cafile=str(d/'ca.pem'))
        if authenticated:
            context.load_cert_chain(d/'client.pem', d/'client.key')
        conn = http.client.HTTPSConnection('localhost', self.server.server_port, context=context, timeout=5)
        try:
            conn.request('POST', '/v1/positions', body=self.payload if payload is None else payload,
                         headers=headers or {'Content-Type': 'application/json'})
            reply = conn.getresponse()
            return reply.status, reply.read()
        finally:
            conn.close()

    def test_idempotent_c_payload_and_restart(self):
        expected = (200, b'{"ack":"9007199254740993"}')
        self.assertEqual(self.request(), expected)
        self.assertEqual(self.request(), expected)
        restarted = Store(self.store.path)
        self.assertEqual(restarted.accept(json.loads(self.payload)), expected[1])
        with sqlite3.connect(self.store.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM positions').fetchone()[0], 1)

    def test_identity_is_bound_to_client_certificate(self):
        data = json.loads(self.payload)
        data['device'] = 'collar-02'
        self.assertEqual(self.request(json.dumps(data).encode())[0], 400)

    def test_same_sequence_cannot_replace_location(self):
        self.assertEqual(self.request()[0], 200)
        data = json.loads(self.payload)
        data['latitude_e7'] += 1
        self.assertEqual(self.request(json.dumps(data).encode())[0], 409)

    def test_client_certificate_is_required(self):
        with self.assertRaises((ssl.SSLError, ConnectionError, http.client.RemoteDisconnected)):
            self.request(authenticated=False)

    def test_storage_failure_never_acknowledges(self):
        class ReadOnlyStore(Store):
            def connect(inner):
                return sqlite3.connect('file:' + str(inner.path) + '?mode=ro', uri=True)
        readonly = object.__new__(ReadOnlyStore)
        readonly.path = self.store.path
        data = json.loads(self.payload)
        data['sequence'] = '9007199254740994'
        self.server.store = readonly
        try:
            self.assertEqual(self.request(json.dumps(data).encode()), (503, b'{}'))
            with sqlite3.connect(self.store.path) as db:
                self.assertIsNone(db.execute('SELECT payload FROM positions WHERE sequence=?',
                                             (data['sequence'],)).fetchone())
        finally:
            self.server.store = self.store

    def test_malformed_payloads_and_transport(self):
        cases = [b'{}', b'[]', self.payload + b'junk', b'\xff',
                 self.payload.replace(b'"v":1', b'"v":1,"v":1'),
                 self.payload.replace(b'"v":1', b'"v":true')]
        for raw in cases:
            with self.subTest(raw=raw[:20]):
                self.assertEqual(self.request(raw)[0], 400)
        self.assertEqual(self.request(b'x'*1025)[0], 400)
        self.assertEqual(self.request(headers={'Content-Type': 'text/plain'})[0], 400)

    def test_range_and_sequence_validation(self):
        for field, value in [('sequence', '01'), ('sequence', str(2**64)), ('sequence', 1),
                             ('utc_ms', 0), ('latitude_e7', 900000001),
                             ('longitude_e7', -1800000001), ('accuracy_cm', 0),
                             ('battery_mv', 1999), ('battery_mv', True)]:
            data = json.loads(self.payload); data[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate(json.dumps(data).encode(), 'collar-01')


if __name__ == '__main__':
    unittest.main(verbosity=2)
