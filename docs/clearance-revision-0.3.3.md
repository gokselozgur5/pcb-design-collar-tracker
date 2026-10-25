# 0.3.3 — first JLC result and failed repeat check

**Correction:** the first 06:29:27 result below was real, but uploading the exact
delivered ZIP again returned 0/1. The owner also showed one orange warning.
The remaining U1.71 connection and new acceptance checks are covered in
[0.3.4](clearance-revision-0.3.4.md). The first 0/0 was not repeatable acceptance.

The actual JLC report dated **2026-10-25 06:29:27** showed **0 Danger / 0 Warning**
for the 35 × 28 mm, four-layer board. PCB analysis was enabled; SMT was disabled.
The complete report was viewed in two raster sections.

- ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.3-35x28-dfm.zip`
- PDF: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.3-jlc-dfm-report.pdf`
- Source: `experiments/35x28-clearance-r033/hardware/`
- [JLC result](https://jlcdfm.com/viewer?pcbUploadFileId=637105049294819330)
- Local evidence: `evidence/zero-warning-r033/candidate033-1/`
- Verification record: `release/collar-tracker-0.3.3-verification.json`

The delivered ZIP is **byte-for-byte identical** to the uploaded
`collar-tracker-0.3.3-iteration1.zip`; only its name changed. This explains the old
name in the report. It contains 14 Gerber/drill/layer files, 132683 bytes, with no
private notes or account data. SHA256:
`6fc0fa2a60f7820cf1ea0a2b06f517fcde13f5683420a5f289cc2b1dabe0f312`.

## Actual before/after results

0.3.2 was analyzed first in the same session: 0/40. The earlier user report had
45 warnings for 0.3.1. Both new analyses used identical JLC rules and thresholds;
no check or severity was disabled or weakened. Rule-file SHA256:
`f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`.

| Warning category | 0.3.2 | First 0.3.3 run |
|---|---:|---:|
| Pad spacing | 10 | 0 |
| Solder-mask bridge | 26 | 0 |
| Mask-to-nearby-copper clearance | 2 | 0 |
| Negative solder mask | 2 | 0 |

## Physical changes

- **U2:** reduced expansion on six small terminal masks from 0.050 to 0.025 mm
  per edge; center-mask width 1.55 → 1.50 mm, height unchanged at 2.90 mm.
  Copper/paste unchanged, positive mask margin retained. This is an adaptation to
  [JLC's LDI/1:1 mask process](https://jlcpcb.com/capabilities/pcb-capabilities),
  not an exact copy of Skyworks Figure 7. Assembly qualification remains open.
- **U5:** local pad dimensions 0.375 × 0.350 → 0.375 × 0.340 mm. Centers, rotation
  and pitch unchanged; mask/paste match the pads. Solder area decreased 2.857%.
  This departs by 0.010 mm from the general +0.10 mm width recommendation in
  [ST TN0018](https://www.st.com/resource/en/technical_note/cd00134799.pdf).
  It is not presented as an exactly ST-approved footprint. Maximum terminals fit
  at nominal placement, which does not qualify placement/reflow robustness.
- **FB1:** added 0.025 mm mask expansion to both pads; copper/paste unchanged.
- **U1.30:** widened one GND segment 0.200 → 0.300 mm to match the pad and remove
  the narrow fill gap. No ground void was added. That record's raw coordinates
  identified U1.30. A later analysis also found U1.71; declaring the earlier U1.71
  match definitely wrong was an error. Both symmetric connections needed checks.
- **J7.1:** moved three nearby SWDIO segments 0.0483 mm left, preserving the net,
  0.20 mm width and 45° entry/exit.
- Refilled ground zones; changed the revision label/title to 0.3.3.

## Local verification and limits

Native KiCad, all severities/tracks and schematic parity: **0 errors / 0 warnings /
0 opens / 0 parity issues**. Project/DRC rules and electrical schematic unchanged.
53 footprints, 792 segments, the same 77 vias/holes. All 268 pads are exposed in
the actual Gerber; minimum separate mask bridge 0.155 mm. Previous source and ZIP
hashes were preserved. PCB SHA256:
`ab78d20c04a6b872dec1dfaad2b50d3995f3112f852905cbfc1ee378c5b992ea`.

The observed supplier result covered **PCB DFM only**, with the repeat-check
failure noted above. SMT, power/RF/antenna, exact BOM, SIM/operator, firmware,
programming/test fixture and enclosure qualification remained open. No order was
placed; this was not working-PCBA acceptance or assembly approval.
