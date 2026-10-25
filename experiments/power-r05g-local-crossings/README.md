# r05g local crossing trial — not selected

This four-layer alternative finishes with six open connections, four dangling-track
warnings and 48 signal-via return gaps. It did not improve the saved r05f checkpoint.
No Gerber or supplier acceptance is claimed.

The trial isolated U7's POWER_GOOD entry and tried a bounded crossing repair around
VIO_ENABLE. HEALTH_EN reconnected, but CHG_STAT and CHG_FAULT did not. Other terminal
groups, original power backbones, local GND paths, RF geometry and SIM topology were
retained. Both inner layers remain continuous GND planes with no tracks.

The native source and source-bound evidence are preserved for inspection. Continue
from r05h, which adds two routing layers while retaining two dedicated GND planes.
Do not import this unfinished crossing repair into the active board.
