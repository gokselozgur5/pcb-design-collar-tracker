#!/usr/bin/env python3
"""Local mTLS reference receiver. Not a deployed service or production API."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import sqlite3
import ssl

FIELDS = {'v', 'device', 'sequence', 'utc_ms', 'latitude_e7', 'longitude_e7',
          'accuracy_cm', 'battery_mv'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate field')
        result[key] = value
    return result


def validate(raw, identity):
    record = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    if type(record) is not dict or set(record) != FIELDS:
        raise ValueError('Unexpected fields')
    if record['device'] != identity or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', identity):
        raise ValueError('Certificate identity mismatch')
    sequence = record['sequence']
    if (type(sequence) is not str or not re.fullmatch(r'[1-9][0-9]{0,19}', sequence)
            or int(sequence) > 2**64 - 1):
        raise ValueError('Invalid sequence')
    limits = {'v': (1, 1), 'utc_ms': (1577836800000, 4102444799999),
              'latitude_e7': (-900000000, 900000000),
              'longitude_e7': (-1800000000, 1800000000),
              'accuracy_cm': (1, 100000000), 'battery_mv': (0, 5000)}
    for key, (low, high) in limits.items():
        if type(record[key]) is not int or not low <= record[key] <= high:
            raise ValueError('Invalid ' + key)
    if 0 < record['battery_mv'] < 2000:
        raise ValueError('Invalid battery voltage')
    return record


class Store:
    def __init__(self, path):
        self.path = path
        db = self.connect()
        try:
            with db:
                db.execute('CREATE TABLE IF NOT EXISTS positions ('
                           'device TEXT NOT NULL, sequence TEXT NOT NULL, payload TEXT NOT NULL,'
                           ' PRIMARY KEY(device, sequence))')
        finally:
            db.close()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute('PRAGMA synchronous=FULL')
        return db

    def accept(self, record):
        payload = json.dumps(record, sort_keys=True, separators=(',', ':'))
        db = self.connect()
        try:
            with db:
                db.execute('BEGIN IMMEDIATE')
                old = db.execute('SELECT payload FROM positions WHERE device=? AND sequence=?',
                                 (record['device'], record['sequence'])).fetchone()
                if old and old[0] != payload:
                    raise ValueError('Sequence already belongs to a different record')
                if not old:
                    db.execute('INSERT INTO positions VALUES (?, ?, ?)',
                               (record['device'], record['sequence'], payload))
            # Return only after SQLite commit has succeeded.
            return ('{"ack":"' + record['sequence'] + '"}').encode('ascii')
        finally:
            db.close()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def answer(self, status, body=b'{}'):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_POST(self):
        if self.path != '/v1/positions':
            self.answer(404)
            return
        lengths = self.headers.get_all('Content-Length', [])
        if (self.headers.get('Transfer-Encoding') is not None or len(lengths) != 1 or
                not re.fullmatch(r'[0-9]{1,4}', lengths[0]) or not 1 <= int(lengths[0]) <= 1024 or
                self.headers.get('Content-Type') != 'application/json'):
            self.answer(400)
            return
        cert = self.connection.getpeercert()
        names = [value for group in cert.get('subject', ()) for key, value in group
                 if key == 'commonName']
        if len(names) != 1:
            self.answer(403)
            return
        try:
            raw = self.rfile.read(int(lengths[0]))
            if len(raw) != int(lengths[0]):
                raise ValueError('Incomplete body')
            record = validate(raw, names[0])
        except (ValueError, UnicodeError):
            self.answer(400)
            return
        try:
            body = self.server.store.accept(record)
        except ValueError:
            self.answer(409)
            return
        except sqlite3.Error:
            self.answer(503)
            return
        self.answer(200, body)


class Receiver(HTTPServer):
    def __init__(self, address, context, store):
        self.context, self.store = context, store
        super().__init__(address, Handler)

    def get_request(self):
        sock, address = super().get_request()
        sock.settimeout(5)
        try:
            return self.context.wrap_socket(sock, server_side=True), address
        except Exception:
            sock.close()
            raise


def tls_context(cert, key, ca):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cert, key)
    context.load_verify_locations(cafile=ca)
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cert', required=True, type=Path)
    parser.add_argument('--key', required=True, type=Path)
    parser.add_argument('--client-ca', required=True, type=Path)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8443)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be 1..65535')
    context = tls_context(args.cert, args.key, args.client_ca)
    server = Receiver(('127.0.0.1', args.port), context, Store(args.database))
    print(f'Local reference receiver: https://localhost:{args.port}/v1/positions', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
