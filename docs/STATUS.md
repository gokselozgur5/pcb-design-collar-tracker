# Current state — 2026-10-25

**Active: Paul layout fixes + physical nano-SIM + real JLC DFM all green.**

GitHub publication is a checkpoint of the current work. The new revision is unfinished.

| Item | State | Source |
|---|---|---|
| Last PCB DFM baseline | 0.3.4, 35 × 28 × 0.8 mm, four copper layers | `experiments/35x28-clearance-r034/hardware/` |
| Baseline validation | Native DRC/ERC clean under the recorded profile; two JLC PCB runs 0 Danger / 0 Warning | `evidence/release-034/`, `release/` |
| Production readiness | Not ready: power/RF/BOM/SMT/firmware/fixture/mechanics open | `docs/order-readiness-0.3.4.md` |
| New revision | `experiments/paul-nanosim-r04/`, schematic + footprints written | `scripts/build_paul_nanosim.py` |
| New PCB | Not saved yet: builder fails while removing old board geometry | Next action below |
| New revision DFM | Not run | Do not reuse baseline acceptance |

## Exact next action

Fix the in-memory KiCad board rebuild in `scripts/build_paul_nanosim.py`.
The last attempt failed at `list(b.GetDrawings())` after the track/zone removal loops:

```text
TypeError: 'swig_runtime_data5.SwigPyObject' object is not iterable
```

A fresh standalone `LoadBoard` + `GetDrawings()` returned eight drawings correctly.
The removal loop also emitted SWIG ownership warnings. The cause is not established.
Inspect ownership/iterator lifetime; collect the board items before mutation or
rebuild a fresh BOARD from cloned footprints/settings. Do not change the baseline.

The failed attempt has written the r04 schematic/BOM/libraries but **no r04 PCB**.
The default trial name is reusable only while that PCB does not exist. After a PCB
exists, use a new `--name` instead of removing the overwrite guard.

Then complete, in order:

1. Check socket/ESD pin mapping, real land geometry, bottom-side keepouts and card access.
2. Add short local GND pad connections to vias and two uninterrupted inner GND planes.
3. Route non-GND nets on the outer layers; preserve/review the existing RF geometry.
4. Add nearby return vias; review power widths, passive pad copper balance and labels.
5. Verify native DRC/ERC/parity, GND connectivity, actual fills and physical geometry.
6. Export a new Gerber ZIP; run JLC twice with unchanged rules and identical bytes.
7. Bind final evidence to source/ZIP hashes, update STATUS and deliver the absolute path.

## Fixed decisions

Nano-SIM now, eSIM later. Candidate socket **GCT SIM8051-6-0-14-00-A / C7363812**;
ESD **TI TPD4E1U06DCKR / C194628**. No factory stock/assembly acceptance yet.
The nRF9151 still uses LTE-M/NB-IoT and a 1.8 V UICC. Türkiye operator/service
qualification remains open; a regular phone SIM is not evidence of compatibility.

0.3.4 has only one signal-free inner plane. Its 61 non-GND vias include 52 outside
the historical 2 mm ground-return screen; max 7.0902 mm. That is a layout-review gap,
not 52 experimentally demonstrated failures. Its all-green DFM does not close Paul.

No order, payment, supplier message, powered test or production approval has occurred.
