# U.FL datum experiment — rejected

**This directory is diagnostic evidence, not an assembly order package.**
Keep the [r03 CPL](../pcba-r03/cpl-jlc-review.csv). Its model-origin correction
is still needed. No native copper, land, paste, part, rule or threshold changed.

The experiment restored only J1/J2 to native physical X centres 18.3/28.3 mm
in the supplier CPL. It used PCB record `637366592129687553`; the selected r03
SMT record `637366801595977730` was left unchanged. Both use the same frozen
Gerber and rule hash. All 44 MPNs and 81 placements were read back and compared.

| Actual SMT result | Selected r03 | Diagnostic |
|---|---:|---:|
| J1 minimum lead/paste overlap | 61.78165% | 4.054812% |
| J2 minimum lead/paste overlap | 61.77933% | 4.052492% |
| J1/J2 additional ground-overlap warnings | 0 | 4 |
| J2 lead-to-hole finding | None | 0.02493 mm |

The [preview](diagnostic-top.png) also shows the shifted connectors.
This rules out removing the X-origin correction as a remedy. It does **not**
accept r03's remaining overlap findings or establish a different backend datum.
Do not upload [rejected-native-centres-cpl.csv](rejected-native-centres-cpl.csv)
for an order. The live diagnostic record contains these rejected inputs.

Evidence: [comparison](comparison.json), [actual placements](jlc-preview-positions.json),
[sanitized measurements](smt-results.json), [actual PDF](diagnostic-report.pdf)
and [SMT screen](diagnostic-smt.png). Account metadata and raw browser state
are excluded. Read-only verification: `python3 scripts/verify_pcba_r04.py`.

## Updated disposition

The two runs returned different subsets of unchanged U1/U2/U3/U9 pin findings.
Their union covers inner 55/64, left 57/57, outer 23/23 and right 64/75.
**20 pin-edge measurements remain unreturned.** This is not complete SMT coverage.
The largest returned U1/U3/U9 discrepancy is 0.00036322 mm. U2 reaches
0.01104646 mm. Do not confuse these dimensions with solder-clearance violations.

| Item | Source comparison and action |
|---|---|
| U2 pin ends | Skyworks 204404H, Fig. 7 specifies the 0.425 x 0.515 mm corner apertures and 1.1435 mm offset used in the native footprint. Retain those dimensions; a library edge flag alone does not justify enlarging them. |
| U2 paste | Fig. 7 explicitly shows three centre apertures. The reported intersection is 1.4 x 0.67 mm within the middle aperture; it is not their union. Retain the split pattern pending stencil/process acceptance. |
| U3 paste | TI DLH0010A drawing 4226298/A illustrates reduced paste. Native 0.84 x 1.41 mm, radius 0.21 mm gives 84.93% of its 0.90 x 1.50 mm copper area. TI's 0.85 x 1.38 mm, radius 0.05 mm example is different; the drawing labels its example 88%. Do not describe the native aperture as an exact copy or increase it just to exceed JLC's generic 90% threshold. |
| U9 paste | Native 0.80 x 1.38 mm land matches Maxim 90-0065 Rev E. The two 0.65 x 0.60 mm windows total 70.65% nominal area. A reported single-window ratio of 37.71% is not total paste coverage; the chosen stencil split still needs process acceptance. |
| J1/J2 | Native land bounds agree with Hirose's recommended pattern; supplier land/terminal geometry differs. Retain the verified physical centres and r03 model-origin correction. Exact factory terminal/paste registration remains open. |
| Edge clearance | D1/U12/C29 body distances are 0.700/0.725/0.750 mm. These are unchanged process warnings; panel support and depanelization acceptance remain open. |
| J6 | The exact SIM8051 MPN is matched and included as a fitted SMT part. Its eight native lands/functions were checked against GCT D6 in r02. A preview placeholder and body-spacing checks do not establish complete pin/placement acceptance. |

The existing manufacturer sources are listed in [r02 provenance](../pcba-r02/sources.json)
and [r03 disposition](../pcba-r03/smt-disposition.md). The current
[Hirose catalogue](https://www.hirose.com/product/download/?distributor=all&lang=en&series=U.FL&type=catalogue)
also recommends a 0.10–0.12 mm stencil and at most two reflow cycles (page 33).
The [TI package example](https://www.ti.com/lit/ds/symlink/bq25185.pdf)
uses 0.125 mm. These are process inputs, not evidence of a qualified common
stencil or thermal profile. Reflow/process acceptance must use the complete BOM.

**PCBA order readiness remains NO.** The remaining release work is complete
terminal/model coverage, stencil/reflow and board-edge handling acceptance for
this exact assembly. No supplier acceptance exists. Do not remove parts, hide
findings, change the rules or call these source comparisons an all-green result.
Physical prototype power/RF tests remain a later, separate requirement.
