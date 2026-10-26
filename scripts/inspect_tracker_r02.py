#!/usr/bin/env python3
"""Inspect the r02 linked image and compiled recovery contract, without flashing."""
import argparse
import json
from pathlib import Path

from inspect_tracker_image import inspect as inspect_base, require

RECOVERY_CONTRACT = [
    'CONFIG_WATCHDOG=y', 'CONFIG_WDT_NRFX=y', 'CONFIG_NRFX_WDT=y',
    'CONFIG_HWINFO=y', 'CONFIG_HWINFO_NRF=y', 'CONFIG_MAIN_THREAD_PRIORITY=5',
    'CONFIG_NRF_MODEM_LIB_ON_FAULT_APPLICATION_SPECIFIC=y',
    '# CONFIG_NRF_MODEM_LIB_ON_FAULT_RESET_MODEM is not set',
    '# CONFIG_NRF_WDT0_SECURE is not set',
]


def inspect(directory):
    result = inspect_base(directory)
    config = (Path(directory)/'zephyr/.config').read_text().splitlines()
    require(all(line in config for line in RECOVERY_CONTRACT),
            'Compiled watchdog/recovery contract mismatch')
    result['watchdog_contract'] = RECOVERY_CONTRACT
    result['hardware_reset_observed'] = False
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    print(json.dumps(inspect(parser.parse_args().build_dir), indent=2))
