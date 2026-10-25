# 40 × 32 mm return and DFM repair checkpoint

The native board passes DRC/ERC, connectivity and parity. The identical
manufacturing ZIP passed two fresh JLC PCB DFM runs at 0 Danger / 0 Warning.
Two return-via screen gaps remain; this is not complete Paul, SMT or product
acceptance. [Current project state](../../docs/STATUS.md) identifies the next work.

- [Source-bound checkpoint](evidence/routing-checkpoint.json).
- [Actual copper and fabrication view: top](evidence/top-review.png) and
  [bottom](evidence/bottom-review.png); the bottom view is mirrored.
- [Tested Gerber/Excellon ZIP](evidence/collar-tracker-04g-preflight-40x32.zip).
- [First JLC report](evidence/jlc-check1/report.pdf) and
  [second JLC report](evidence/jlc-check2/report.pdf).
- [Local repair provenance](evidence/rework-provenance.json).

`build/incomplete-return-gap-rework.kicad_pcb` is a separate unfinished
experiment, with one open and two dangling warnings. Its dedicated DRC and
inventory must not be confused with the current board's clean checks.
`build/undersized-label-trial.kicad_pcb` preserves the rejected first label-size
attempt; the current labels use the unchanged native minimum size and stroke.
The source and ZIP hashes in the checkpoint are the acceptance identities.
