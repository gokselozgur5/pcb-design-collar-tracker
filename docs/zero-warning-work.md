# Zero-warning work — 2026-10-25

The owner requested zero warnings. **The 0.3.4 PCB DFM task was completed:** two
independent JLC uploads returned **0 Danger / 0 Warning**, with native KiCad
**0 violations / 0 opens / 0 parity issues**. Reports: 2026-10-25 06:39:36 and
06:41:25; SMT disabled. See [0.3.4](clearance-revision-0.3.4.md) for changes,
evidence and delivery. This acceptance does not transfer to later revisions.

The library cleanup and threshold research below precede the physical fixes.
The delivered source is `35x28-clearance-r034`.

## Native library cleanup

Working copy preserving 0.3.2's physical design:
`/Users/gok/codex/projects/collar-tracker/experiments/35x28-zero-r033/hardware/collar-tracker.kicad_pcb`

Customized footprints still used old standard-library identities. Saved the actual
53 definitions in `Collar033.pretty` and updated PCB/schematic library links.
`library-provenance.json` records prior identities and file hashes. This resolves
source/library consistency; it does not qualify the physical lands for assembly.

- Before: 0 errors / 47 library warnings / 0 opens / 0 parity issues.
- After: **0 errors / 0 warnings / 0 opens / 0 parity issues**.
- Used `--severity-all --schematic-parity --all-track-errors`.
- Project/custom DRC files byte-identical; no disabled check, severity change or exclusion.
- Only footprint IDs changed in the schematic. Native pad/mask/track/via/fill/silk
  geometry stayed identical. **All 11 Gerber layers** match released 0.3.2 after
  stripping generation timestamps.
- PCB SHA256: `345544f51eec67767cb7154620392a062bba0ac8ea19051c3e0de5a2beee255b`.

Evidence: `experiments/35x28-zero-r033/evidence/library-cleanup-checks.json`,
`library-drc.json`, `geometry.json`, `gerbers/`. Tools:
`scripts/persist_trial_footprints.py`, `dfm_geometry.py`, `verify_library_cleanup033.py`.

This stage was not released as the physical 0.3.3 Gerber revision. Since physical
output was unchanged, the existing 0.3.2 ZIP remained the right supplier comparison
input. Library cleanup was not claimed to change JLC findings.

## Actual default JLC thresholds

Inspected the [public JLCDFM demo](https://jlcdfm.com/viewer?pcbUploadFileId=637065032774410242&demo=1)
in a fresh anonymous browser context. No user Gerber was uploaded at this stage.
Opened the rules panel without Apply/Save/Set as default. Downloaded system config
and screenshots were retained locally under `evidence/zero-warning-r033/`.

| Check | Config values, mil | Warning/green boundary |
|---|---|---|
| Pad spacing | 4, 6, 8 | 6 mil = 0.1524 mm |
| Mask bridge | 4, 6, 8 | 6 mil = 0.1524 mm |
| Mask to nearby track | 3, 6, 8 | 6 mil = 0.1524 mm |
| Negative mask opening | No numeric threshold; warning-value | Geometry finding |

Rounding explains why displayed 0.15 mm values can be either orange or green.
The earlier 0.20 mm scan did not reproduce the exact warning threshold. The demo
profile was not assumed to be the user's actual configuration without reading it.

Counting actual openings against 0.1524 mm yielded 30 mask-neighbor gaps in 0.3.1
and 26 in 0.3.2. These were **local geometry counts, not a 0.3.2 JLC result**.
No zero-warning ZIP was claimed and no supplier rules were relaxed.

The PDF lacked all coordinates for two negative-mask and three mask/trace findings.
A same-net trace-overhang candidate scan found nothing; it was not offered as the
cause of those warnings. ST's official MKI179V1 Gerber link was found, but HTTP/2
failure/timeouts prevented downloading it. No claim was made to have inspected
that reference board's lands.

## Actual analysis and authorization correction

JLC analysis was recognized as a necessary part of the already requested work;
the unnecessary extra permission gate was removed. Only manufacturing layers and
drills were prepared. Anonymous upload required login; the owner logged into the
dedicated browser and asked to retry. The normal session was used without reading
or exporting passwords, cookies or tokens.

Actual 0.3.2 and corrected 0.3.3 uploads initially showed **40 → 0 Warning**.
Raw results, unchanged rules, complete PDF and screenshots were saved. That run's
raw coordinates identified U1.30, and negative-mask findings were at FB1's two pads.
The local count of 26 mask bridges matched the actual 0.3.2 result. No order or
supplier message was sent. Electrical/RF/BOM/firmware/test and new footprint/mask
process qualification remained open for working factory delivery.

## 0.3.3 repeat check and 0.3.4

The owner showed one orange warning. Reuploading the same delivered 0.3.3 ZIP
reproduced 0/1. The first 0/0 was insufficient acceptance evidence. Raw coordinates
identified U1.71; U1.30 was a separate symmetric connection. Treating the earlier
U1.71 image match as disproved was incorrect.

0.3.4 also widens this second ground neck to 0.30 mm. Two different JLC records
for identical final ZIP bytes returned 0/0 under the same rules; the second upload
used the final delivery path. The cause of the earlier result discrepancy remains
unestablished.
