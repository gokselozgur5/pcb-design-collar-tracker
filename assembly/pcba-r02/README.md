# r05l connector placement review

**Review only. Full SMT and factory release remain on hold.** This revision
resolves the U.FL preview offset and documents the SIM/Q1 manufacturer checks.
The PCB, Gerber, BOM and physical component positions are unchanged. The two
saved PCB DFM passes still apply to the same Gerber bytes; no new PCB run is claimed.

Use the unchanged [BOM](../pcba-r01/bom.csv) with this revision's
[JLC review CPL](cpl-jlc-review.csv), SHA-256
`5aa23f9f2b6a56a33e6bc581511507f6b09b449acc34ac6c0eb6119ab3ffd02f`.
The [native CPL](../pcba-r01/cpl.csv) remains the physical-coordinate reference.
Do not mix supplier-specific origins with native machine-placement coordinates.

| Reference | Result | Still required |
|---|---|---|
| J1/J2, Hirose U.FL | Native lands match the manufacturer pattern; JLC model origin corrected and preview inspected | Factory confirmation of the exact reel, placement datum and stencil/process |
| J6, GCT nano-SIM | All eight native lands and electrical functions match D6; no-peg variant and card-entry direction retained | Supplier model and complete placement/SMT review |
| Q1, DMN62D2UDW-7 | Native six-pin map and SOT363 lands checked | Source original part or qualify a documented alternate; mandatory fitted reference |

## U.FL origin and pin mapping

Hirose's pattern has a 4mm outer ground span, 1.9mm inner gap and 2.2mm
ground length. Rotated into this board's frame, it reproduces both native
footprints exactly. The native RF land is pin 1; both ground lands are pin 2.
The supplier library instead numbers the RF land 2 and the grounds 1/3.
Its ground lands have 270-degree local pad rotation; their global size is
2.2 x 1.1mm, not 1.1 x 2.2mm. Library lands are not the manufacturer stencil.
[Manufacturer pattern and provenance](sources.json).

The dated C88373 library has its footprint origin 0.6320028mm left of the
3D outline centre. The outline bounding-box centre agrees with that model datum.
This review CPL subtracts 0.6320028mm from J1/J2 X only. It retains the thirteen
IC/discrete angle corrections from [r01](../pcba-r01/README.md).

| Reference | Native physical centre X/Y, mm | This JLC model's CPL X/Y, mm |
|---|---|---|
| J1 | 18.3 / 5.7 | 17.667997 / 5.7 |
| J2 | 28.3 / 16.2 | 27.667997 / 16.2 |

After uploading these exact bytes, reloading and reopening Component Placements,
the downloaded preview reproduces all 80 available references, sides and angles.
The [top](previews/top.png) and [bottom](previews/bottom.png) were inspected;
J1/J2 now align with the native coax centres. The [sanitized read-back](jlc-preview-positions.json)
retains the evidence. Q1 is still absent. J6 has a BOM/position entry but no usable
returned model. No Save & Close approval or complete SMT analysis was submitted.
Factory confirmation is required before using any review CPL for machine programming.

## SIM and Q1

The [placement reference](placement-reference.pdf) identifies physical centres,
pad numbers and nets. Its J6 view mirrors X to show the bottom component side.
The GCT D6 drawing is rotated 180 degrees, then reflected in X, to compare it
with the Gerber top view. The existing no-peg socket remains at (27,20)mm;
card entry faces Gerber +Y. C6/VPP is unconnected and both shield lands are ground.
No locating holes or reverse orientation are introduced.

`DMN62D0UDW-7` is an **unselected candidate**, not an approved substitute.
Its manufacturer pin diagram and standard SOT363 land pattern agree with the
original. At 25C, its maximum specified RDS(on) at 1.8V/50mA is 3 ohm versus
4 ohm for the original. The inherited 6-ohm hot estimate and falling-rail behavior
remain unqualified. The visible JLC search at 07:21 UTC on 2026-10-26 showed only
one C781251 in stock. That does not resolve assembly supply.
See the [candidate screen](q1-review.json) and [primary sources](sources.json).

## Next action and evidence

Obtain Q1 sourcing and the J6 model/placement decision, then review all 81 fitted
references and run actual SMT analysis. The factory must also confirm stencil,
two-sided assembly, programming, testing and external harness responsibilities.
The protected-pack enquiry remains prepared but unsent. No order, payment or
supplier message was made. See [working-device delivery](../../docs/pcba-delivery.md).

`python3 scripts/verify_pcba_connectors.py` performs read-only checks against
native lands, the manufacturer dimensions, supplier read-back and frozen package.
The old U.FL origin fails both centre checks; this review correction passes.
The build/package scripts write evidence and must not be rerun during normal resume.
