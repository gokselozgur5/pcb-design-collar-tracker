# Battery and charging review

**HOLD: the direct 10 kΩ / B3435 thermistor option does not protect a 0–45°C charging pack.**
This is a new source-based finding on the unchanged r05k board. Its two clean
PCB DFM reports remain valid; they do not assess battery charging behavior.

The saved native netlist connects J4.3 directly to U3.6 (TS/MR), and U3.4 (/CE)
to GND. There is no firmware-controlled charge enable in this topology.

## Reproduced mismatch

The [TI BQ25185 revision B](https://www.ti.com/lit/ds/symlink/bq25185.pdf),
pages 4, 8 and 18, specifies a 38 µA nominal TS bias and 0.115 V nominal hot
threshold. The [SEMITEC 103JT](https://www.semitec-global.com/uploads/2022/01/P9-JT-Thermistor.pdf)
table gives 4.147 kΩ at 50°C. Their product is **0.157586 V**: the charger still
permits charging above the reviewed pack's 45°C maximum.

Including the published current/comparator endpoints and an approximate R25/B
sensitivity gives 0.148522–0.166926 V at 50°C, still above even the 0.125 V hot
threshold maximum. A constant-beta approximation gives a nominal hot trip near
59.5°C and a 54.9–64.5°C sensitivity range. These are calculations, not measured
trip temperatures or a guaranteed full thermistor curve. The independent table
point is sufficient to reject the proposed direct connection.

The thin-film 103JT-025 is therefore **not selected**. Its 0.5 mm maximum thickness
does not establish electrical compatibility. The manufacturer also requires a
7 mm minimum distance between the sensor head and a lead bend; force, bonding
and thermal coupling need an actual assembly definition.

```sh
python3 scripts/check_pack_charge.py       # Expected exit 2: electrical HOLD
python3 -m unittest discover -s tests -p test_pack_charge.py -v
```

The handoff verifier reproduces the evidence and preserves HOLD. It does not
treat the expected exit code as an implementation failure or turn it into PASS.

## Pack screen

The inspected [EEMB manufacturer specification, distributor-hosted](https://macrogroup.ru/upload/iblock/806/l9ka6axlc8lwl5b0dbf2xov43s2g5l33/LP503030.pdf)
is **ZJQM-RD-SPC-A04005 revision 0.0, 2018-07-30**, for LP503030-PCM-LD.
Its bare cell supports 700 mA, but page 7 limits the assembled PCM to **350 mA
continuous, or 1 A for 3 seconds**. Neither the cell rating nor the short peak
rating establishes a 600 mA continuous supply or an LTE/NB-IoT pulse duty cycle.
The 600 mA screen is an engineering headroom target, not a measured load.

This pack is **not selected**. It has no NTC and specifies charging at 0–45°C.
The maximum pack dimensions are 32 × 30.5 × 5.3 mm; the drawing does not supply
a swelling/harness acceptance envelope. Product pages with a different capacity
must not be substituted for this controlled specification.

The new [Synzen ZETA SZK-C-0G04 GNSS candidate](https://synzen.com.tw/uploads/DATASHEETS/zeta_szk-c-0g04---datasheet---gnss_rev-0-4.pdf)
is 40 × 10 × 0.2 mm with 100 mm of 1.13 mm coax and an MHF I/U.FL-compatible plug.
It is narrower than the earlier Bentoni candidate, but is not yet selected or
placed. Its published RF results use 2 mm ABS and cable chokes; performance does
not transfer to the current shell and body environment. No antenna or enclosure
change is claimed in this review.

## Required implementation

1. Implement a charge interlock that measures the actual cell and is disabled
   outside its allowed range, including tolerances and thermal lag. It must work
   during cold start, low-cell recovery, reset, absent firmware and sensor failure.
   A nominal B3435 match, charger die overtemperature or software status polling
   is insufficient. Keep r05k immutable and give any circuit successor new native
   checks and two real same-byte supplier analyses.
2. Select a fully specified protected pack against current, temperature, charging
   voltage tolerance, PCM recovery and cell aging. Do not infer pack capability
   from cell-only specifications. Then bind its NTC/harness and actual volume.
3. Place and qualify the real antennas/cables, finish the carrier retention and
   sealed charging assembly, and implement factory firmware and acceptance tests.

No circuit correction, pack procurement, supplier message, order, powered test,
RF test or physical ingress qualification was performed. Source hashes and the
small reproducible parameter extracts are in `inputs.json`; third-party PDFs
remain in ignored local references.
