#!/usr/bin/env python3
"""Return public verification material only; reject SDK-default P-256 signing keys."""
import argparse
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def inspect(key_path, sdk):
    if not key_path.is_file():
        raise ValueError('Signing key does not exist')
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError('Signing key must be an ECDSA P-256 private key')
    public = key.public_key()
    der = public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    reference = serialization.load_pem_private_key(
        (sdk/'bootloader/mcuboot/root-ec-p256.pem').read_bytes(), password=None)
    reference_der = reference.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    if der == reference_der:
        raise ValueError('Public SDK development key rejected, including copied or renamed files')
    if key_path.stat().st_mode & 0o077:
        raise ValueError('Signing key must have owner-only permissions')
    return dict(algorithm='ECDSA-P256', spki_sha256=hashlib.sha256(der).hexdigest(),
                public_pem=public.public_bytes(serialization.Encoding.PEM,
                    serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii'),
                production_custody_accepted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key', type=Path)
    parser.add_argument('--sdk-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.key.resolve(), args.sdk_root.resolve()), indent=2))
