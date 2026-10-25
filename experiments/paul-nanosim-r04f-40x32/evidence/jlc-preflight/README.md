# Preliminary JLC result: 0 Danger / 2 Warning

This is the first real PCB DFM result for the native-clean 40 × 32 mm r04f
checkpoint. It is not final acceptance. SMT analysis was not run.

- Board SHA256: `240be3bbab528ffb123737fe75c54bb642ec2f204b32a6533e704f794691a6d2`.
- Input: [manufacturing ZIP](../collar-tracker-04-preflight-40x32.zip), SHA256
  `b91c94dba2b69d1c44f0d9fe8b33179999470c4b4d9b78e57ae97dc70b4533d2`.
- [JLC record 637217298994909185](https://jlcdfm.com/viewer?pcbUploadFileId=637217298994909185).
- All 29 PCB rows completed. The unchanged rule hash is
  `f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`.
- [Native export manifest](../collar-tracker-04-preflight-40x32/manifest.json),
  [full supplier PDF](report.pdf), [UI](screen.png), [raw result](dfm.json),
  [measured coordinates](summary.json) and [upload receipt](receipt.json).

| Warning | Actual geometry | Measured gap | Green boundary |
|---|---|---:|---:|
| B.Cu pad spacing | GND via at (124.8, 116) to D1.2 | 0.1500378 mm | 0.1524 mm |
| F.Mask opening to trace | J3.1 mask to adjacent CHG_STAT copper | 0.1502156 mm | 0.1524 mm |

Fix the local via/track geometry and rerun native checks. Keep the TI lands,
mask apertures and supplier rules. A local correction does not establish a new
supplier result; the final package still needs two fresh same-byte 0/0 runs.

The raw measurement coordinates use mils: multiply by 0.0254 for millimetres.
With this export's plot origin, native `x = 100 + raw_x × 0.0254` and
`y = 128 − raw_y × 0.0254`. Board-size metadata uses a different unit.
The supplier's default 1.6 mm thickness is parser metadata, not an order or
approval of the proposed 0.8 mm stackup. The original supplier data is retained
verbatim; this English summary explains its scope.
