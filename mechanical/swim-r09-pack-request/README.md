# r09 — requested pack and NTC fit

This is a dimensional study of [CT-BAT-001-A](../../assembly/pack-r03/request.json),
**not a supplier-approved pack or a released device**. r08 and every checked PCB
remain unchanged. The existing EEMB 350 mA PCM has not been accepted electrically.

The requested complete pack body is 32 x 30.5 x 5.3 mm. A flat 26 x 4.1 x 0.5 mm
SEMITEC 103JT-025 candidate sits on its broad face, with 0.15 mm bonding and
0.10 mm cover budgets. This gives a maximum modeled top at Z=8.15 mm within the
33 x 31.5 x 6.2 mm assembly reservation. Supplier confirmation must include
service swelling and the sensor's actual active-area/attachment drawing.

The board, both antennas and their cable routes move upward by 0.4 mm. The rigid
shell becomes **57.4 x 49.4 x 21.0 mm**; the boot is 60.4 x 52.4 x 25.8 mm. The
docking key still adds 1.3 mm in X. Contact/seal dimensions, the PCB, and nominal
20 mm screw candidate remain unchanged. Existing shell checks are reapplied to
the taller stack. The original board height is a failing component-clearance
control for this wider pack envelope.

The pack/NTC preview does not draw invented wires. Native J4 assignments are
checked in the [factory request](../../assembly/pack-r03/README.md); the actual
harness, strain relief, positive retention and adhesive strength are unfinished.
Cable tolerances, thermal response, RF and physical ingress are also unqualified.

Reproduce with the geometry environment, then export and inspect the real CAD:

```sh
.venv-dfm/bin/python scripts/check_pack_request.py
python3 scripts/export_pack_enclosure.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_pack_request.py -v
```

The export includes eight meshes, five previews and actual CAD intersection
controls. The numerical result describes only the declared envelopes. It does
not establish complete assembly, battery acceptance or an IP68 rating.
