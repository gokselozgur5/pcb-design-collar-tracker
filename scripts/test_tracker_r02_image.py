#!/usr/bin/env python3
"""Reject changed linked vectors/storage and disabled/inaccessible watchdog settings."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import tempfile

from inspect_tracker_image import read_hex
from inspect_tracker_r02 import inspect
from test_tracker_image import write_hex

ROOT = Path(__file__).resolve().parents[1]


def test(directory):
    source = inspect(directory)
    memory = read_hex(directory/source['merged_hex'])
    config = (directory/'zephyr/.config').read_text()
    runtime = ROOT/'.runtime/tracker-r02'
    runtime.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='image-controls-', dir=runtime) as tmp:
        target = Path(tmp)
        for name in ('zephyr/.config', 'zephyr/zephyr.dts', 'tfm/CMakeCache.txt'):
            (target/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(directory/name, target/name)
        for name, expected in [
                ('reset-into-storage', 'Invalid reset handler'),
                ('image-overwrites-nvs', 'Firmware writes outside code partitions'),
                ('watchdog-disabled', 'Compiled watchdog/recovery contract mismatch'),
                ('watchdog-secure-only', 'Compiled watchdog/recovery contract mismatch')]:
            changed, changed_config = memory.copy(), config
            if name == 'reset-into-storage':
                for i, byte in enumerate(struct.pack('<I', 0xf8001)):
                    changed[4+i] = byte
            elif name == 'image-overwrites-nvs':
                changed[0xf8000] = 0
            elif name == 'watchdog-disabled':
                changed_config = config.replace('CONFIG_WATCHDOG=y', '# CONFIG_WATCHDOG is not set')
            else:
                changed_config = config.replace('# CONFIG_NRF_WDT0_SECURE is not set',
                                                'CONFIG_NRF_WDT0_SECURE=y')
            write_hex(target/'zephyr/tfm_merged.hex', changed)
            (target/'zephyr/.config').write_text(changed_config)
            try:
                inspect(target)
            except ValueError as error:
                if expected not in str(error):
                    raise
                results.append(dict(name=name, error=str(error)))
            else:
                raise AssertionError('Image/configuration mutation was accepted: '+name)
    result = dict(result='PASS', actual_merged_sha256=source['merged_sha256'],
                  rejected_mutations=results, physical_test=False)
    (runtime/'image-controls.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    print(json.dumps(test(parser.parse_args().build_dir), indent=2))
