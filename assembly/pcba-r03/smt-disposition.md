# First actual SMT analysis — unresolved

The run used record `637366801595977730`, the unchanged r05l Gerber, r03 BOM/CPL
and the original JLC rule hash
`f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`.
The [actual PDF](smt-report.pdf), [screen](previews/smt-initial.png) and
[sanitized raw measurements](smt-results.json) preserve the failing result.
No category was disabled and no threshold or native land was changed.

The UI/PDF caps results at 50 per layer/category. Counts below distinguish
returned measurements from the backend's `truncate.orig_num`; they are category
measurements, not counts of independent defective components.

| Category | Returned / backend total | Evidence and disposition |
|---|---:|---|
| Inner pin edge | 50 / 64 | Returned U1 distances are 0.00000508..0.00003183 mm. Consistent with numerical conversion, but omitted measurements have not been inspected. |
| Left pin edge | 50 / 57 | Returned records include U1, U2 and U3; largest reported distance 0.01104646 mm. Compare package terminal bounds and native recommended lands before disposition. |
| Outer pin edge | 23 / 23 | Returned U1 distances are 0.00000508..0.00003556 mm. Numerical-scale discrepancy, not a reason to enlarge all native module lands. |
| Right pin edge | 50 / 75 | Returned U1 distances are 0.00000254..0.00007366 mm; 25 measurements omitted. |
| Lead/paste overlap | 5 / 5 | U2 0.3191, U9 0.3771, J1/J2 0.6178: Danger; U3 0.8485: Warning. Review notes below; none is claimed closed. |
| Component to edge | 4 / 4 | D1 0.7000 mm, U12 0.7250 mm and C29 0.7500 mm are Warning; R29 1.0000 mm is Good. Panel/rail and depanelization review remains open. |
| Component spacing | 84 / 211 | All returned distances are Good, minimum 0.5500 mm. 127 top-side measurements were not returned. This is not 211 inspected results. |

## Paste and library comparisons

- **U2, SKY65943-11:** the native stencil has three centre apertures. The reported
  shape is the middle 1.55 x 0.67 mm aperture, not their union. The other two are
  about 1.55 x 0.745 mm. Skyworks 204404H, Figure 7, depicts that split aperture
  pattern. This explains why a single-region ratio can understate total paste;
  it does not by itself qualify the stencil or the separate edge findings.
- **U9, MAX17048:** the native exposed land is 0.80 x 1.38 mm, matching Maxim
  drawing 90-0065 Rev E. Two 0.65 x 0.60 mm paste rectangles have 70.65% combined
  nominal area relative to that copper land. JLC reports one region at 37.71%
  against its model, a different denominator. The manufacturer land drawing
  does not specify this stencil split; process acceptance remains open.
- **U3, BQ25185:** the native 0.90 x 1.50 mm exposed land has a smaller paste
  aperture. TI's package drawing explicitly illustrates 88% paste coverage;
  JLC's generic 90% warning threshold does not establish that 100% paste is
  required. Compare the actual rounded aperture and stencil thickness; do not
  increase paste solely to clear the warning.
- **J1/J2, U.FL:** native copper matches Hirose's recommended mounting pattern,
  as documented in r02. The supplier uses a different land outline/numbering
  and an offset model origin. The two overlap findings require exact terminal
  and stencil review, despite the corrected visual alignment.

Sources already inspected: Skyworks 204404H Figure 7
(`references/sky65943-11.pdf`), TI BQ25185 package paste example
(`references/bq25185.pdf`), Maxim 90-0065 Rev E, and the manufacturer sources in
[r02 provenance](../pcba-r02/sources.json). Local copyrighted source copies remain
in their existing reference locations; the repository stores derived findings.

## Scope still missing

J6 body spacing appears in the backend results, while its visual preview is a
placeholder and explicit pin coverage is absent. The eight manufacturer land
and net checks are valid separate evidence, not a complete automated SMT pass.
The omitted pin-edge measurements and exact terminal/stencil comparisons still
need resolution. A missing model or truncated response must not be called green.

The DFM service's quote metadata defaults to 1.6 mm and generic finish/copper
settings. Those are not an accepted order specification: the design uses the
six-layer JLC06081H-7628 0.8 mm class stack, CAD thickness 0.84088 mm. Actual order
settings, panelization, stencil/reflow and factory placement datums need to match
the design. No order or production acceptance was submitted.
