#!/usr/bin/env python3
"""Inspect real linked reset vectors, storage exclusion and compiled configuration."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def require(value, message):
    if not value:
        raise ValueError(message)


def read_hex(path):
    memory, base, ended = {}, 0, False
    for line in path.read_text().splitlines():
        require(not ended and line.startswith(':'), 'Invalid HEX record sequence')
        record = bytes.fromhex(line[1:])
        require(len(record) >= 5 and len(record) == record[0] + 5 and sum(record) % 256 == 0,
                'Invalid HEX checksum/length')
        count, address, kind = record[0], int.from_bytes(record[1:3], 'big'), record[3]
        payload = record[4:4 + count]
        if kind == 0:
            for offset, byte in enumerate(payload):
                location = base + address + offset
                require(location not in memory, 'Overlapping HEX data')
                memory[location] = byte
        elif kind == 1:
            require(count == 0, 'Invalid EOF')
            ended = True
        elif kind == 4:
            require(count == 2, 'Invalid extended address')
            base = int.from_bytes(payload, 'big') << 16
        elif kind in (3, 5):
            require(count == 4, 'Invalid start address')
        else:
            raise ValueError('Unexpected HEX record type')
    require(ended, 'Missing HEX EOF')
    return memory


def inspect(directory):
    directory = Path(directory)
    candidates = [directory/'tfm_merged.hex', directory/'zephyr/tfm_merged.hex']
    merged = next((p for p in candidates if p.is_file()), None)
    require(merged is not None, 'Missing combined TF-M/application image')
    memory = read_hex(merged)
    require(all(0 <= address < 0x80000 for address in memory),
            'Firmware writes outside code partitions (storage must survive update)')
    vectors = {}
    for label, base, end, ram_start, ram_end in (
            ('secure', 0, 0x40000, 0x20000000, 0x20016000),
            ('application', 0x40000, 0x80000, 0x20020000, 0x20040000)):
        require(all(base+i in memory for i in range(8)), 'Missing ' + label + ' reset vector')
        stack, reset = struct.unpack('<II', bytes(memory[base+i] for i in range(8)))
        require(ram_start < stack <= ram_end and stack % 8 == 0, 'Invalid initial stack: ' + label)
        require(reset & 1 and base <= (reset & ~1) < end, 'Invalid reset handler: ' + label)
        require((reset & ~1) in memory, 'Reset handler missing from image: ' + label)
        vectors[label] = dict(address=base, initial_sp=stack, reset_handler=reset)
    config = (directory/'zephyr/.config').read_text()
    required = ['CONFIG_BUILD_WITH_TFM=y', 'CONFIG_TRUSTED_EXECUTION_NONSECURE=y',
                'CONFIG_USE_DT_CODE_PARTITION=y', 'CONFIG_NRF_MODEM_LIB=y',
                'CONFIG_LTE_NETWORK_MODE_LTE_M_GPS=y', 'CONFIG_NVS_DATA_CRC=y',
                '# CONFIG_SERIAL is not set', '# CONFIG_TFM_SECURE_UART is not set',
                '# CONFIG_TFM_DUMMY_PROVISIONING is not set']
    require(all(line in config.splitlines() for line in required), 'Compiled security/I/O contract mismatch')
    tfm = (directory/'tfm/CMakeCache.txt').read_text()
    require('NRF_NS_STORAGE:BOOL=y' in tfm, 'NVS is not accessible to the non-secure application')
    # The generated map must declare the expected storage span; code addresses
    # were independently checked above against the actual merged image.
    dts = (directory/'zephyr/zephyr.dts').read_text()
    start = dts.index('storage_partition: partition@f8000')
    storage = dts[start:dts.index('};', start)]
    require('0xf8000' in storage and '0x8000' in storage, 'Unexpected NVS partition')
    return dict(result='PASS', merged_hex=str(merged.relative_to(directory)),
                merged_sha256=hashlib.sha256(merged.read_bytes()).hexdigest(),
                reset_vectors=vectors, storage=dict(address=0xf8000, bytes=32768, sectors=8),
                compiled_contract=required, programmed_storage_bytes=0,
                signed_boot=False, ota=False, flashed=False, physical_test=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    print(json.dumps(inspect(parser.parse_args().build_dir), indent=2))
