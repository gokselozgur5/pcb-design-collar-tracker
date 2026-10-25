# Power-off sequencing: manufacturer exception to review

Rechecked on 2026-10-25. Nordic explicitly permits VDD_GPIO to fall after VDD or
ENABLE when the application tolerates undefined GPIO states. Its normal startup
recommendation still delays VDD_GPIO until the module has completed hardware
boot. [Nordic nRF9151 ENABLE sequence](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/enable_sequence.html).

The conditional r05 source-retention calculation is therefore not proof that
every abrupt supply loss violates an unconditional manufacturer requirement or
damages the module. The collar's acceptable shutdown behavior, external loads and
leakage still need assessment before relying on that exception. In particular,
identify what an undefined extension-port/control state would do.

No schematic or acceptance state changed on this basis. Review the exception
before adding further retention hardware or simplifying the existing sequence.
It does not resolve modem undervoltage, component bounds, source pulse capability
or the absent powered tests.
