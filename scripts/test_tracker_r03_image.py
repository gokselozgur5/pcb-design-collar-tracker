#!/usr/bin/env python3
"""Reject actual signed-image/key mutations; do not flash or alter build output."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from inspect_tracker_image import require
from inspect_tracker_r03 import digest, inspect, read_hex, verify_signed, write_hex
from tracker_signing_key import inspect as inspect_key

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT/'.runtime/tracker-r03'


def test(directory, public_path, sdk):
    baseline = inspect(directory, public_path)
    original = (directory/'tracker-r03/zephyr/zephyr.signed.bin').read_bytes()
    public = serialization.load_pem_public_key(public_path.read_bytes())
    rejected = []

    def reject(name, action):
        try:
            action()
        except (ValueError, InvalidSignature) as error:
            rejected.append(dict(name=name, rejection=type(error).__name__+': '+str(error)))
        else:
            raise AssertionError('Accepted negative control: '+name)

    changed = bytearray(original)
    changed[600] ^= 1
    reject('changed-payload', lambda: verify_signed(bytes(changed), public))
    changed = bytearray(original)
    changed[-1] ^= 1
    reject('changed-signature', lambda: verify_signed(bytes(changed), public))
    reject('different-p256-key', lambda: verify_signed(original, ec.generate_private_key(ec.SECP256R1()).public_key()))
    reject('truncated-image', lambda: verify_signed(original[:-1], public))

    # Copy only inspected inputs; mutate one at a time and restore baseline bytes.
    with tempfile.TemporaryDirectory(prefix='image-controls-', dir=RUNTIME) as temporary:
        temp = Path(temporary)
        names = ['mcuboot/zephyr/zephyr.hex', 'mcuboot/zephyr/.config', 'mcuboot/zephyr/zephyr.dts',
                 'tracker-r03/zephyr/zephyr.signed.hex', 'tracker-r03/zephyr/zephyr.signed.bin',
                 'tracker-r03/zephyr/tfm_merged.hex', 'tracker-r03/zephyr/.config',
                 'tracker-r03/zephyr/zephyr.dts', 'tracker-r03/tfm/CMakeCache.txt',
                 'collar-tracker-r03-prototype.hex']
        for name in names:
            (temp/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(directory/name, temp/name)
        def mutate_hex(name, change):
            path = temp/name
            memory = read_hex(path)
            change(memory)
            path.unlink()  # Disposable test copy only; write_hex refuses replacement.
            write_hex(memory, path)
        mutate_hex('mcuboot/zephyr/zephyr.hex', lambda m: [m.pop(i) for i in range(8)])
        reject('missing-boot-reset', lambda: inspect(temp, public_path))
        shutil.copyfile(directory/names[0], temp/names[0])
        mutate_hex('tracker-r03/zephyr/zephyr.signed.hex', lambda m: m.update({0xf8000: 0}))
        reject('image-overwrites-nvs', lambda: inspect(temp, public_path))
        shutil.copyfile(directory/names[3], temp/names[3])
        config = temp/names[1]
        config.write_text(config.read_text().replace('CONFIG_BOOT_VALIDATE_SLOT0=y', '# CONFIG_BOOT_VALIDATE_SLOT0 is not set'))
        reject('primary-validation-disabled', lambda: inspect(temp, public_path))
        shutil.copyfile(directory/names[1], config)
        config.write_text(config.read_text().replace('CONFIG_FPROTECT=y', '# CONFIG_FPROTECT is not set'))
        reject('boot-protection-disabled', lambda: inspect(temp, public_path))
        copied_key = temp/'renamed-sdk-test-key.pem'
        shutil.copyfile(sdk/'bootloader/mcuboot/root-ec-p256.pem', copied_key)
        copied_key.chmod(0o600)
        reject('renamed-public-sdk-private-key', lambda: inspect_key(copied_key, sdk))
    inputs = {str(p.relative_to(ROOT)): digest(p) for p in [
        Path(__file__).resolve(), ROOT/'scripts/inspect_tracker_r03.py', ROOT/'scripts/tracker_signing_key.py']}
    result = dict(result='PASS', actual_complete_sha256=baseline['complete_sha256'],
                  actual_signed_bin_sha256=hashlib.sha256(original).hexdigest(),
                  rejected_mutations=rejected, inputs=inputs,
                  actual_bootloader_executed=False, physical_test=False)
    (RUNTIME/'image-controls.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    parser.add_argument('--public-key', type=Path, required=True)
    parser.add_argument('--sdk-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(test(args.build_dir, args.public_key, args.sdk_root), indent=2))
