# r05m Q1 sourcing revision

Native source for the ROHM UM6K34NTCN selection described in
[PCBA r03](../../assembly/pcba-r03/README.md). Q1 replaces DMN62D2UDW-7.
Only its symbol/value/MPN/datasheet strings change. All other copied native
files, copper geometry, pads, nets, stack and rules remain identical to r05l.
The original r05l source is preserved.

Fresh KiCad 10 DRC/ERC/open-net/schematic-parity reports are under `evidence/`.
The inherited five DRC and four ERC disabled categories are unchanged and are
listed in [native-checks.json](../../assembly/pcba-r03/native-checks.json).
Use the existing r05l Gerber; it contains no substituted part strings and is
reused byte for byte. No new PCB DFM pass is claimed.

This is the next prototype candidate, not a manufacturing release. The actual
SMT run has unresolved findings; current continuation is in
[STATUS](../../docs/STATUS.md).
