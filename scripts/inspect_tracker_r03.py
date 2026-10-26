#!/usr/bin/env python3
"""Inspect signed r03 artifacts; use the pinned SDK Python for cryptography."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from inspect_tracker_image import require
from inspect_tracker_r02 import RECOVERY_CONTRACT

BOOT_CONTRACT = [
    'CONFIG_BOOT_SIGNATURE_TYPE_ECDSA_P256=y', 'CONFIG_BOOT_ECDSA_NRF_OBERON=y',
    'CONFIG_BOOT_VALIDATE_SLOT0=y', 'CONFIG_BOOT_SWAP_USING_OFFSET=y',
    'CONFIG_MCUBOOT_DOWNGRADE_PREVENTION=y', 'CONFIG_FPROTECT=y',
    'CONFIG_BOOT_WATCHDOG_FEED=y',
    'CONFIG_MCUBOOT_MCUBOOT_IMAGE_NUMBER=-1', 'CONFIG_NCS_MCUBOOT_IMG_VALIDATE_ATTEMPT_COUNT=1',
    'CONFIG_MCUBOOT_LOG_LEVEL_OFF=y', '# CONFIG_CONSOLE is not set', '# CONFIG_SERIAL is not set',
    '# CONFIG_BOOT_BYPASS_KEY_MATCH is not set', '# CONFIG_BOOT_DIRECT_XIP is not set',
    '# CONFIG_BOOT_RAM_LOAD is not set', '# CONFIG_MCUBOOT_SERIAL is not set',
    '# CONFIG_MCUBOOT_CHECK_HEADER_LOAD_ADDRESS is not set',
]
APP_CONTRACT = [
    'CONFIG_BUILD_WITH_TFM=y', 'CONFIG_TRUSTED_EXECUTION_NONSECURE=y',
    'CONFIG_BOOTLOADER_MCUBOOT=y', 'CONFIG_MCUBOOT_BOOTLOADER_MODE_SWAP_USING_OFFSET=y',
    'CONFIG_MCUBOOT_BOOTLOADER_NO_DOWNGRADE=y', 'CONFIG_NVS_DATA_CRC=y',
    'CONFIG_NRF_MODEM_LIB=y', 'CONFIG_LTE_NETWORK_MODE_LTE_M_GPS=y',
    '# CONFIG_SERIAL is not set', '# CONFIG_TFM_SECURE_UART is not set',
    '# CONFIG_TFM_DUMMY_PROVISIONING is not set',
    'CONFIG_TRACKER_HOST=""', 'CONFIG_TRACKER_DEVICE_ID=""',
    'CONFIG_TRACKER_TRIAL_SECONDS=600', 'CONFIG_TRACKER_TRIAL_STABLE_SECONDS=30',
] + RECOVERY_CONTRACT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_hex(path):
    """Reject corrupt/ambiguous records, including overlapping identical data."""
    memory, base, ended = {}, 0, False
    for line in path.read_text().splitlines():
        require(not ended and line.startswith(':'), 'Invalid HEX record sequence')
        r = bytes.fromhex(line[1:])
        require(len(r) >= 5 and len(r) == r[0] + 5 and sum(r) % 256 == 0,
                'Invalid HEX checksum/length')
        count, address, kind = r[0], int.from_bytes(r[1:3], 'big'), r[3]
        data = r[4:-1]
        if kind == 0:
            require(address + count <= 65536, 'HEX record crosses a segment')
            for i, byte in enumerate(data):
                location = base + address + i
                require(location <= 0xffffffff and location not in memory, 'Overlapping/out-of-range HEX')
                memory[location] = byte
        elif kind == 1:
            require(count == 0 and address == 0, 'Invalid EOF')
            ended = True
        elif kind in (2, 4):
            require(count == 2 and address == 0, 'Invalid extended address')
            base = int.from_bytes(data, 'big') << (4 if kind == 2 else 16)
        elif kind in (3, 5):
            require(count == 4 and address == 0, 'Invalid start address')
        else:
            raise ValueError('Unexpected HEX record type')
    require(ended and memory, 'Missing HEX data/EOF')
    return memory


def write_hex(memory, path):
    lines, upper = [], None
    def record(address, kind, data):
        raw = bytes([len(data)]) + address.to_bytes(2, 'big') + bytes([kind]) + data
        lines.append(':' + (raw + bytes([-sum(raw) & 255])).hex().upper())
    addresses = sorted(memory)
    i = 0
    while i < len(addresses):
        start = addresses[i]
        if start >> 16 != upper:
            upper = start >> 16
            record(0, 4, upper.to_bytes(2, 'big'))
        data = bytearray([memory[start]])
        i += 1
        while i < len(addresses) and len(data) < 16 and addresses[i] == start+len(data) and addresses[i] >> 16 == upper:
            data.append(memory[addresses[i]])
            i += 1
        record(start & 65535, 0, bytes(data))
    record(0, 1, b'')
    content = '\n'.join(lines)+'\n'
    if path.exists():
        require(path.read_text() == content, 'Refusing to replace different complete image')
    else:
        path.write_text(content)


def verify_signed(data, public):
    require(len(data) >= 32, 'Short signed image')
    magic, load, header, protected, size, flags, major, minor, revision, build, pad = struct.unpack_from('<IIHHIIBBHII', data)
    require((magic, load, header, protected, flags, major, minor, revision, build, pad) ==
            (0x96f3b83d, 0x50000, 512, 0, 256, 0, 3, 0, 0, 0), 'Unexpected image header')
    end = header+size
    require(0 < size and end+4 <= len(data) < 0x6e000, 'Invalid image size/slot capacity')
    tlv_magic, tlv_size = struct.unpack_from('<HH', data, end)
    require(tlv_magic == 0x6907 and end+tlv_size == len(data), 'Invalid TLV extent')
    tlvs, cursor = {}, end+4
    while cursor < len(data):
        require(cursor+4 <= len(data), 'Truncated TLV')
        kind, reserved, length = struct.unpack_from('<BBH', data, cursor)
        cursor += 4
        require(not reserved and cursor+length <= len(data) and kind not in tlvs, 'Invalid/duplicate TLV')
        tlvs[kind] = data[cursor:cursor+length]
        cursor += length
    require(set(tlvs) == {1, 0x10, 0x22}, 'Unexpected signature TLVs')
    der = public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    require(tlvs[1] == hashlib.sha256(der).digest(), 'Signing key hash mismatch')
    hashed = hashlib.sha256(data[:end]).digest()
    require(tlvs[0x10] == hashed, 'Signed image hash mismatch')
    public.verify(tlvs[0x22], hashed, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
    return dict(version='0.3.0+0', header_bytes=header, payload_bytes=size,
                signed_content_sha256=hashed.hex(), spki_sha256=hashlib.sha256(der).hexdigest(),
                signature_bytes=len(tlvs[0x22]), total_bytes=len(data), flags=flags, load_address=load)


def inspect(directory, public_path, merge=False):
    directory = Path(directory)
    boot_path = directory/'mcuboot/zephyr/zephyr.hex'
    signed_path = directory/'tracker-r03/zephyr/zephyr.signed.hex'
    bin_path = directory/'tracker-r03/zephyr/zephyr.signed.bin'
    boot, signed = read_hex(boot_path), read_hex(signed_path)
    require(all(0 <= a < 0x10000 for a in boot), 'Bootloader outside reserved flash')
    require(all(0x10000 <= a < 0x7e000 for a in signed), 'Image enters trailer/other storage')
    require(set(signed) == set(range(0x10000, max(signed)+1)), 'Holes in signed HEX')
    public = serialization.load_pem_public_key(public_path.read_bytes())
    require(isinstance(public, ec.EllipticCurvePublicKey) and isinstance(public.curve, ec.SECP256R1), 'Not a P-256 verification key')
    der = public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    boot_bytes = bytes(boot.get(i, 255) for i in range(0x10000))
    require(boot_bytes.count(der) == 1, 'Verification key not uniquely embedded in actual bootloader')
    signed_bytes = bytes(signed[a] for a in sorted(signed))
    image = verify_signed(signed_bytes, public)
    binary = verify_signed(bin_path.read_bytes(), public)
    require(image['signed_content_sha256'] == binary['signed_content_sha256'], 'HEX/BIN sign different content')
    # Separate signing invocations may legitimately produce different ECDSA signatures.
    tfm_merged = read_hex(directory/'tracker-r03/zephyr/tfm_merged.hex')
    require(all(signed.get(a) == byte for a, byte in tfm_merged.items()), 'Signed payload differs from linked TF-M/application')
    combined = boot | signed
    vectors = {}
    for label, base, limit, ram_base, ram_limit in (
            ('bootloader', 0, 0x10000, 0x20000000, 0x20016000),
            ('secure', 0x10200, 0x50000, 0x20000000, 0x20016000),
            ('application', 0x50000, 0x7e000, 0x20020000, 0x20040000)):
        require(all(base+i in combined for i in range(8)), 'Missing '+label+' vector')
        stack, reset = struct.unpack('<II', bytes(combined[base+i] for i in range(8)))
        require(ram_base < stack <= ram_limit and stack % 8 == 0, 'Invalid '+label+' stack')
        require(reset & 1 and base <= (reset & ~1) < limit and reset & ~1 in combined, 'Invalid '+label+' reset handler')
        vectors[label] = dict(address=base, initial_sp=stack, reset_handler=reset)
    for relative, contract in [('mcuboot/zephyr/.config', BOOT_CONTRACT), ('tracker-r03/zephyr/.config', APP_CONTRACT)]:
        lines = (directory/relative).read_text().splitlines()
        require(all(x in lines for x in contract), 'Compiled contract mismatch: '+relative)
    require('NRF_NS_STORAGE:BOOL=y' in (directory/'tracker-r03/tfm/CMakeCache.txt').read_text(), 'NVS access missing')
    for target in ['mcuboot', 'tracker-r03']:
        dts = (directory/target/'zephyr/zephyr.dts').read_text()
        for label, address, size in [('boot_partition', '0', '10000'), ('slot0_partition', '10000', '70000'),
                                     ('slot1_partition', '80000', '70000'), ('storage_partition', 'f8000', '8000')]:
            start = dts.index(label+': partition@'+address)
            span = dts[start:dts.index('};', start)]
            require('0x'+address in span and '0x'+size in span, 'Unexpected partition '+label)
    complete = directory/'collar-tracker-r03-prototype.hex'
    if merge:
        write_hex(combined, complete)
    require(read_hex(complete) == combined, 'Complete HEX differs from bootloader/signed image')
    return dict(result='PASS', complete_hex=complete.name, complete_sha256=digest(complete),
                signed_hex=image, signed_bin=binary, reset_vectors=vectors,
                programmed_storage_bytes=0, programmed_secondary_bytes=0,
                storage=dict(address=0xf8000, bytes=32768), secondary_update_address=0x81000,
                boot_contract=BOOT_CONTRACT, application_contract=APP_CONTRACT,
                signatures_verified_against_embedded_key=True, physical_boot_observed=False,
                ota_transport_implemented=False, manufacturing_release=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    parser.add_argument('--public-key', type=Path, required=True)
    parser.add_argument('--merge', action='store_true')
    args = parser.parse_args()
    print(json.dumps(inspect(args.build_dir, args.public_key, args.merge), indent=2))
