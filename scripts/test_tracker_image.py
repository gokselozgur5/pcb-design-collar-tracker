#!/usr/bin/env python3
"""Reject valid-checksum mutations of the actual linked tracker image."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import tempfile

from inspect_tracker_image import inspect, read_hex

ROOT = Path(__file__).resolve().parents[1]


def write_hex(path, memory):
    def line(address, kind, data):
        row = bytes((len(data),)) + address.to_bytes(2, 'big') + bytes((kind,)) + data
        return ':' + (row + bytes((-sum(row) & 255,))).hex().upper()
    rows, upper = [], None
    keys = sorted(memory)
    i = 0
    while i < len(keys):
        start = keys[i]
        if upper != start >> 16:
            upper = start >> 16
            rows.append(line(0, 4, upper.to_bytes(2, 'big')))
        data = bytearray()
        while (i < len(keys) and keys[i] == start + len(data) and
               len(data) < 16 and keys[i] >> 16 == upper):
            data.append(memory[keys[i]])
            i += 1
        rows.append(line(start & 65535, 0, data))
    rows.append(':00000001FF')
    path.write_text('\n'.join(rows)+'\n')


def test(directory):
    source = inspect(directory)
    memory = read_hex(directory/source['merged_hex'])
    runtime = ROOT/'.runtime/tracker-r01'
    runtime.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='image-controls-', dir=runtime) as tmp:
        target = Path(tmp)
        for name in ('zephyr/.config', 'zephyr/zephyr.dts', 'tfm/CMakeCache.txt'):
            (target/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(directory/name, target/name)
        for name, expected in [('reset-into-storage', 'Invalid reset handler'),
                               ('image-overwrites-nvs', 'Firmware writes outside code partitions')]:
            changed = memory.copy()
            if name == 'reset-into-storage':
                for i, byte in enumerate(struct.pack('<I', 0xf8001)):
                    changed[4+i] = byte
            else:
                changed[0xf8000] = 0
            write_hex(target/'zephyr/tfm_merged.hex', changed)
            try:
                inspect(target)
            except ValueError as error:
                if expected not in str(error):
                    raise
                results.append(dict(name=name, error=str(error)))
            else:
                raise AssertionError('Linked-image mutation was accepted: '+name)
    result = dict(result='PASS', actual_merged_sha256=source['merged_sha256'],
                  rejected_mutations=results, physical_test=False)
    (runtime/'image-controls.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    print(json.dumps(test(parser.parse_args().build_dir), indent=2))
