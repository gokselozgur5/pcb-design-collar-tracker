# Project checkpoints

## 2026-10-25 — Repository and fresh-session handoff

- Event: Göksel requested atomic GitHub commits and a Claude session that can
  continue without another explanation of the project.
- Decision: Preserve the verified 0.3.4 baseline and checkpoint the unfinished
  Paul/nano-SIM revision separately. Use a private personal repository.
- Result: Source, historical revisions, selected DFM evidence, manufacturer
  references and explicit project entry files are included. Browser sessions,
  credentials, raw browser captures and unrelated private continuity stay local.
- Next: Resolve the r04 builder's KiCad/SWIG board-mutation failure, then implement
  ground fanout/routing and complete the new revision's own acceptance checks.

Earlier engineering decisions are in `docs/decisions.md` and the revision reports.
Their evidence is dated; do not transfer an older pass to a newer source file.

## 2026-10-25 — Nano-SIM ground layout and first route

- Event: Continued the authorized Paul/nano-SIM implementation after publication.
- Decision: Preserve 0.3.4; use two inner GND planes and local pad-to-via stubs.
- Result: Fixed KiCad board mutation; saved 54-footprint placement. Connected
  81 ground pads through 68 vias; ground-stage native DRC has zero violations,
  zero parity issues, no open GND and 84 remaining non-GND connections. Imported
  the first route while preserving ground and RF geometry. Native result:
  14 opens, three dangling vias, zero parity issues. No new JLC acceptance.
- Next: Finish routing, review returns/power/copper balance and run the new
  revision's own native and supplier checks. See STATUS for exact source/evidence.

## 2026-10-25 — Reusable PCB workflow and English repository

- Event: The owner requested a reusable PCB Design workflow and English-only
  GitHub content, and renamed the repository.
- Decision: Apply English to docs, comments, generated labels, commits, issues and
  PRs, even when chat is Turkish. Use the live canonical repository name
  `gokselozgur5/pcb-design-collar-tracker`; keep the existing local directory.
- Result: Added `docs/PCB_DESIGN.md`, linked project entry instructions, translated
  current and historical documentation, and regenerated the mechanical review
  sheet in English. Updated remote/repository links. Published hardware, release
  ZIPs and raw supplier evidence retain their original bytes.
- Validation: Reviewed English prose and the rendered sheet, scanned repository
  text, checked local Markdown links/Python syntax and verified saved baseline
  evidence. Historical documents retain their original verification limits.
- Next: Continue the unfinished r04 routing from STATUS. The language change does
  not add new manufacturing or functional acceptance.

## 2026-10-25 — Local routing and charger escape checkpoint

- Event: Continued the authorized PCB work and verified that the English commit
  was present on the renamed public repository.
- Decision: Preserve every released baseline. Add footprint-aware routing and
  retain native checks at each stage; remove an excessive signal detour rather
  than presenting a lower open-net count as layout completion.
- Result: Local routing reduced 14 opens to three, but CHG_FAULT took 77.33 mm.
  Removing that detour and adjusting charger/ground exits leaves four opens and
  four dangling vias, zero parity issues and no copper-clearance violations.
  All 67 GND via centers remain in both inner fills; 81 ground pads are connected.
  A Freerouting repair repeated unchanged results and was stopped without import.
- Validation: Fresh native DRC and filled-plane check are bound to the current
  source in `routing-checkpoint.json`. Return-via planner/application scripts are
  present but unexecuted. Socket access, TI land-pattern differences and Nordic
  power guidance were recorded; they remain review items, not acceptance claims.
- Next: Resolve charger/SPI fanout and socket/ESD placement. Then complete return,
  power and passive-copper review, native checks and two real same-byte JLC runs.

## 2026-10-25 — Localized charger trial and import regression

- Event: Continued the Paul/nano-SIM work while keeping all repository content
  and the new handoff in English.
- Decision: Reject the whole-net r04c rework; retain working remote pin escapes
  and the original outward-facing SIM orientation in r04d. Use TI's DCK land
  example. Preserve failed stages and the accepted 0.3.4 source/ZIP.
- Result: r04d has six open connections and 14 dangling-item warnings, with zero
  parity or other native DRC violations. All 66 GND via centers lie in both inner
  fills, no inner tracks remain, and 24 RF segments match the baseline. The
  29/75 return-via screen and auxiliary J5 supply connection remain open.
  Rejected 59.98/79.59 mm detours and the three-clearance-error SIM experiment
  are preserved separately. No new JLC analysis was run.
- Validation: A no-routing DSN/SES round-trip reproduced an importer defect:
  old locked signal routes survived beside replacements, adding two co-located
  drill findings. Matching export/import locks removed those findings while
  preserving the original six opens, 189 GND items and 28 manual escapes. Native
  DRC, source hashes, power estimates and replay evidence are tied together in
  r04d's `evidence/routing-checkpoint.json`.
- Next: Reconcile the router model's larger incomplete count with actual native
  connectivity before another search. No routing process remains. Finish the
  six connections and remaining layout reviews, then run both real JLC checks.

## 2026-10-25 — Router contact fixes and complete native routing

- Event: Continued the authorized Paul/nano-SIM layout and English repository work.
- Decision: Fix actual DSN contacts and loaded lock states before further routing.
  Preserve r04e at 35 × 28 mm; test 40 × 32 mm after measured routing failures.
  Reject the 83.52 mm auxiliary supply detour in the earlier unlocked trial.
- Result: r04f closes every net after one nearby GND-via move. Removing two unused
  charger vias gives zero native opens, violations, warnings and parity findings.
  Fifteen added GND return vias keep those checks clean and reduce 30 screening
  gaps to nine. All 81 GND pads reach a local via, all 81 GND via centers lie in
  both inner fills, no inner tracks exist, and 24 RF segments remain exact.
- Validation: The loaded-lock regression rejects the old 930 USER_FIXED model
  and accepts the corrected model. Native source/evidence hashes are recorded in
  r04f `routing-checkpoint.json`; accepted 0.3.4 bytes are preserved.
- Next: Resolve nine return-screen gaps, review power/ESD/passive balance, add
  useful English labels and run two new unchanged-rule same-byte JLC analyses.
  No new supplier acceptance, order, powered test or production approval yet.

## 2026-10-25 — Native-clean r04g, English labels and two actual JLC passes

- Event: Continued the Paul/nano-SIM revision and verified the English-only
  repository requirement against the live personal repository.
- Decision: Preserve 0.3.4 and r04f; keep successful local repairs in r04g and
  retain the incomplete coupled-return alternative separately. Supplier success
  applies to its exact PCB/ZIP, not to the remaining review or production.
- Result: r04g has 81 locally connected GND pads, 86 ground vias in both continuous
  inner planes, no inner tracks and 24 unchanged RF segments. Native DRC/ERC,
  connectivity and parity are clean. Return-screen gaps fall from nine to two.
  Nine English labels meet native silk minima; source-bound placement rejects
  stale plans. Actual top/bottom views were inspected.
- DFM: The first r04f analysis was 0 Danger / 2 Warning. Moving the D1 GND via
  0.02 mm and the nearby CHG_STAT run 0.15 mm closes the two measured gaps without
  changing lands, apertures or rules. The identical r04g ZIP passed twice at 0/0,
  all 29 rows complete: records 637221644721938434 and 637222172922957825. Both
  raw measurements, UI views, complete PDFs and hashes were checked. SMT was off.
- Boundary: A coupled SIM_IO/COEX0 move clears the distance screen but leaves one
  HEALTH_INT open and two dangling warnings; it is preserved as an incomplete
  experiment. Wider routing also exposed moved/duplicated signal vias and a
  blocked HEALTH_RESET exit; those alternatives were not accepted. A help-only
  Freerouting invocation migrated its default local settings version before the
  workspace profile was specified; subsequent invocations use explicit paths.
- Next: Resolve SIM_IO and COEX0 return gaps, finish ESD/passive/power review,
  and repeat native plus two same-byte JLC checks after further layout changes.
  No order, payment, supplier message or physical acceptance occurred.

## 2026-10-25 — Complete return screen, SIM topology and passive review

- Event: Continued the authorized Paul/nano-SIM work and kept the repository,
  generated labels and portable handoff in English.
- Decision: Preserve r04g and its two JLC reports. Resolve the coupled return
  geometry, then inspect actual SIM protection and passive copper before another
  supplier submission. A native or supplier pass cannot accept card access.
- Result: The return-only repair is native-clean with zero screen gaps. r04h
  adds a second ESD array and short contact routes, removes a same-net clock
  bypass, reworks five passive attachments and retains all 24 baseline RF
  segments. It has 55 footprints, 82 locally connected GND pads, 90 GND vias in
  both continuous inner fills, no inner tracks and all 91 non-GND vias within
  the 2 mm screen. Fresh all-severity DRC/ERC/connectivity/parity checks pass.
- Review: All four old clamp bypasses are reproduced by the copper audit;
  none remains in r04h. Four discriminating topology tests pass. Main power-path
  estimates are unchanged; the added LDO/VIO checks retain current/thermal
  uncertainty. Native top/bottom views and the schematic were inspected. The
  D2 schematic symbol was moved above the title block without changing PCB bytes.
- Open issue: D1 and C10 now occupy the projected SIM insertion corridor.
  This placement is WIP. Relocate their bodies before the next manufacturing
  package, then rerun topology/native/geometry checks and two actual same-byte
  JLC analyses. No r04h supplier upload, order or powered test occurred.

## 2026-10-25 — Clear SIM access and verify r04i supplier DFM

- Event: Resumed under the new complete-design/DFM goal; swimming/IP68 was added.
- Decision: Move D1/C10 outside the card lane, preserve the protected SIM topology
  and reject the long reset detour. Keep physical qualification separate.
- Result: r04i is native-clean, with 82 local GND pads, 91 plane-connected GND
  vias, 93 of 93 return screens, 24 preserved RF segments and zero card-lane body
  overlaps or clamp bypasses. R12 moved and obsolete clock copper was removed.
- Supplier evidence: Initial 5 Danger / 2 Warning at the SIM legend resolved by
  moving that legend 1.476 mm. Final ZIP 6304b66623a473e4c5405c6db7181b3f1879fa93088f9812802d43e814f90898
  passed records 637245503244296194 and 637247002053398530 at 0/0, with 29 rows
  and 442 green measurements each. Rules unchanged; SMT off. Both complete PDFs
  and native views inspected. A no-upload browser attempt was excluded.
- Next: Complete the swim-r01 review/mesh package and resolve actual fit/part
  selections. No physical IP, powered, RF, PCBA or production acceptance exists.

## 2026-10-25 — Package the swimming enclosure prototype for review

- Event: Added a serviceable shell/lid, carrier, independent radial contact seals,
  external blind magnet slots, captured plugs, dock alignment shell and TPU boot.
- Decision: Use provisional 2 m fresh water / 60 min and magnetic charging while
  preference replies are pending. Keep actual production part selections open.
- Result: Rigid body 57.4 × 49.4 × 17.6 mm; 58.7 mm with the key. The boot is
  60.4 × 52.4 × 22.4 mm. Thirty declared geometry checks pass. Four regressions
  retain the rejected gland/cell cases. All eight exported meshes have closed,
  oriented edges and one connected surface; actual bounds match the CAD screen.
- Review: Inspected the exploded/section/mounted previews and both review sheets.
  The 124-file bundle includes editable PCB/CAD, meshes, the tested Gerber ZIP and
  both full JLC reports. Bundle SHA256:
  `21e3f0573d7cc0b6ef8b13118e3d23182f1fe0f6fd29d14bfad34404460a6805`.
- Next: Select the actual protected pack, antennas, dock/harness, seal compounds
  and fasteners; replace component-height reservations and review fit/assembly.
  Qualify the final physical assembly. No IP rating or production readiness is claimed.

## 2026-10-25 — Check populated fit and revise the carrier/contact retention

- Event: Replaced blanket component-height reservations with the actual r04i
  placement export and sourced height profiles, preserving the tested PCB bytes.
- Decision: Treat generic-part MPNs and harness bounds as candidates/requirements.
  Retain the old carrier and M4 hardware as rejected fit cases; keep battery and
  antenna approval open when available drawings do not establish suitability.
- Result: 49 component entries, two harness requirements and two bare-pad areas
  pass the declared geometry screen. D1 gets a carrier relief. Contact retention
  changes to M3 with centers at Z=5.5 mm and shallow carrier underside reliefs;
  the 1 mm bridges retain a single connected carrier. Outer dimensions unchanged.
  Six regressions pass; the revised CAD interference is empty and the old carrier
  produces a positive interference solid. Eight actual meshes and four previews
  pass integrity checks; both updated review pages were visually inspected.
- Package: 132 files with native PCB/CAD, both clean JLC reports, fit evidence and
  self-contained source-reference links. SHA256:
  `ea960e01f39e7b31aef930359a82b7b360e9e6c4a1fb232dad78c8d7f7032206`.
  The first local packaging attempt was retained under ignored runtime storage;
  the final bundle fixes relative documentation links. r01 is unchanged.
- Next: Final protected pack/NTC and antenna/feed/cable selections, harness/dock,
  positive PCB retention, material/seal/fastener/torque definition and physical
  fit, ingress, power, RF and assembly qualification. The active goal is unfinished.

## 2026-10-25 — Reproduce the open power-domain findings

- Event: Reviewed the existing electrical holds before selecting the final pack
  and antennas. Kept the tested r04i and populated swim-r02 geometry unchanged.
- Decision: Export the real schematic and compare its power pins to native board
  geometry. Separate source conclusions, illustrative calculations and absent
  powered measurements. Do not add an unreviewed supervisor merely to close a list.
- Result: 148 unique power-related pins agree. The evidence reproduces three
  open findings: modem undervoltage margin, GPIO supply sequencing and battery-ADC
  off-state feed. Nominal charger settings are 4.2 V, 500 mA input and 100 mA charge.
  The audit returns electrical HOLD; standard handoff verification retains that
  state. Three regressions reject mismatched board pins and unreviewed topology
  while reproducing the unchanged baseline. No circuit repair or powered test.
- Next: Implement supervised undervoltage/restart and the GPIO/ADC off-state
  strategy in a separate schematic revision before routing a successor. Review
  brief-brownout timing as well as nominal startup.

## 2026-10-25 — Bound Türkiye connectivity claims and update continuation

- Event: Checked current operator/manufacturer pages and an nRF9151-DK support
  case while preserving the user's Türkiye-first and physical nano-SIM decisions.
- Decision: Keep the modem as a prototype candidate. Manufacturer Vodafone
  certification listings, an activated Turkcell NB-IoT offer and a firsthand
  local-SIM success report do not establish our subscription or mobility result.
- Result: Added a source-linked evidence table and a discriminating development-kit
  check. Updated the English entry chain to prioritize electrical completion
  before successor routing and final pack/antenna assembly. Review PDF, both
  mechanical bundles, native r04i and the two actual JLC records stay unchanged.
- Next: Implement the power successor and validate the intended local SIM/service,
  then continue pack/antenna/dock/harness/retention and physical qualification.
  No operator message, account change, purchase or powered test occurred.

## 2026-10-25 — Implement the supervised-power candidate and diagnose native Python crashes

- Event: Continued the power successor while answering the user's Gerber/progress
  questions and reports of macOS Python crash dialogs.
- Decision: Preserve r04i and mechanical releases. Build a separate source-bound
  71-part candidate, retain electrical HOLD for unqualified timing/source behavior,
  and check native failures instead of suppressing them. Keep working original
  signal paths when the unrestricted router disrupts their pin exits.
- Result: r05 adds adjustable rail supervision/hysteresis, restart and GPIO timing,
  Schmitt/FET discharge and an I2C fuel gauge; the old ADC divider is removed.
  Native ERC and seven regressions pass; 205 unrelated pin memberships remain.
  The 40 × 32 mm PCB has zero geometry/parity violations and 23 non-GND opens.
  All 97 physical GND pads / 94 unique terminals have local paths, 100 GND vias
  join both continuous inner planes, and 24 RF segments are retained. Four of 99
  non-GND return screens and passive/footprint/populated-fit reviews remain open.
  All four SIM clamp paths remain present without bypass. Recovered 128 valid
  original rail items, rejected 14 conflicts, and pruned three unused tails only
  after native pad-island invariants passed. The current PCB SHA256 is
  `78df6a520fc978e08451c94e6c6f475877f401867b55c0218802ee3434d193a2`.
- Result: The latest crash stack identifies `BOARD::FlipLayer` from an unowned
  footprint flip. Attaching the footprint first passes in an isolated process
  with normal exit; no CAD file is written by that smoke check. An earlier
  finalization crash has a distinct stack and remains unattributed. Preserved
  release hashes remain valid. A bare-snapshot project-rule substitution was
  also detected, discarded and guarded against in the placement helper.
- Next: Reserve new signal-pin exits and revise their local placement in an
  isolated successor; finish routing/returns and physical footprint/fit review
  before a new Gerber and two actual same-byte JLC runs. Qualify source retention,
  component bounds, selected cell/RF and factory/ingress behavior. No new JLC,
  order, payment, supplier message, physical test or production approval occurred.

## 2026-10-25 — Reserve every new pin exit and checkpoint r05b

- Event: Continued routing while checking the user's Python crash concern.
- Decision: Preserve r04i/r05 and use a separate placement with exits for every
  connected new pin. Correct lands against source drawings, keep native rules,
  and select routes by fresh native results. Retain electrical HOLD and explicit
  incomplete routing instead of treating a router's exit code as acceptance.
- Result: Twenty affected parts, 64 reserved exits and 63 added vias. U6/U7, U8
  and Q1 lands follow the recorded TI/Diodes drawings. The selected local route
  leaves 14 opens versus 24 in the alternative Freerouting result. Twenty-one
  obsolete leaf segments were pruned with native pad-island invariants; 1,350
  remaining protected items retain exact UUID/geometry. Final native DRC has
  27 dangling-via warnings, no other violations and no schematic mismatch under
  unchanged inherited settings. All 97 physical GND pads have local attachment;
  113 GND vias join both continuous inner planes. Two of 143 return screens remain
  outside 2 mm. All 24 RF segments, four SIM clamp paths, the projected card lane
  and 12 original power backbone paths remain checked. PCB SHA256:
  `4c047c3a5b69110ad758f83091236c7aa2c25a96f374732dcd8bda79bb88027e`.
- Result: Preliminary swim-r03 checks all 69 populated envelopes and 30 shell
  checks for this exact board. Nine resistor heights are explicit requirements,
  with exact MPN/tolerance/TCR unresolved. The original carrier control detects
  D1 interference; actual top/bottom and populated previews were inspected.
  No r03 mesh/boolean acceptance or physical ingress result is claimed.
- Result: Native operations in this continuation exited normally; no observed
  recurrence of the footprint-flip crash. The separate earlier finalization
  crash remains unattributed. The unchanged-source low-current branch attempt
  closed no connections; the rejected 73 mm FG_ALERT detour was not applied.
- Next: Inspect remaining free-space barriers and return-only GND stitches in an
  isolated copy, then finish routing, dangling exits and return gaps. Qualify
  electrical source/timing bounds, actual BOM/pack/antennas and assembly before
  production. New final Gerbers still need two real same-byte JLC analyses.
  No new supplier upload, order, payment, message or physical test occurred.

## 2026-10-25 — Close nine connections across r05c and r05f

- Event: Continued the unfinished power-layout routing after the user's status request.
- Decision: Preserve r05b and all earlier tested sources. Compare isolated routes
  using fresh native results; retain the existing circuit, lands and rules. Keep
  the more successful preserved-signal path instead of the broad joint reroute.
- Result: r05c closed six connections (14 to eight). r05d's strict Freerouting
  attempt stayed at eight without importing an SES; r05e ended at 17 and is not
  selected. r05f closed POWER_GOOD, relocated/connected C9 and closed VDD_NRF,
  leaving five opens and zero other native violations/warnings or parity issues.
  Source SHA256: `1b2b4bd7b90c3931bd8cbb151637408902332a94260d4a2a820ae6df04838a09`.
- Result: All 94 unique GND terminals retain local paths; 97 physical GND pads,
  83 GND vias, both continuous inner planes, all 24 RF segments, four no-bypass
  SIM clamp paths, clear card entry and 12 original power backbones remain checked.
  Return-only stitches were deliberately released; 44 of 129 signal vias remain
  outside the inherited return screen. The 68.085 mm POWER_GOOD detour needs review.
- Result: Cleanup removed unused exits and replaced unnecessary single-layer via
  junctions while preserving native terminal groups. Whole-segment deletion was
  refused where a dangling segment also carried a live branch; only its loose
  end was trimmed. Repeated native LoadBoard produced wx initialization warnings
  with normal exit; isolated probe processes avoid that path. No native crash
  was observed in these completed operations; the older finalization crash is
  still unattributed. Four raster regressions pass.
- Result: Fresh r05f preliminary fit checks 69 populated envelopes and 30 shell
  checks. C9 clears the carrier and the original D1 interference control remains
  effective. PCB and populated previews were inspected. No new mesh/physical
  qualification or component purchasing approval is claimed.
- Result: Rechecked Nordic's explicit exception for power-off order when the
  application tolerates undefined GPIO states. The follow-up records that scope
  and requires an actual collar shutdown-behavior review before using it; the
  circuit and electrical HOLD were not changed on that basis.
- Next: Resolve the specific barriers at U7/U4/gauge connections in an isolated
  copy, finish routing and restore returns, then refresh fit and obtain two
  same-ZIP JLC runs. Electrical source/BOM, pack, antennas, factory assembly and
  ingress qualification remain open. No new supplier upload, order, payment,
  supplier message or physical test occurred.

## 2026-10-25 — Complete six-layer routing and repeat real JLC DFM

- Event: The four-layer local crossing trial left six opens; preserving two GND
  planes and adding two routing layers closed all five r05f connections.
- Decision: Select r05h at 40 × 32 × nominal 0.8 mm. F/In2/In3/B carry routes;
  In1/In4 remain continuous GND. Keep all older tested sources unchanged.
- Result: Native DRC/ERC/parity are clear; all 94 unique grounds are local and
  all 128 signal transitions pass the 2 mm screen. POWER_GOOD's replacement is
  18.214 mm with no new vias; C30 attachments are balanced. Source-guarded cleanup
  preserved native terminal groups. The new native audit uses one LoadBoard per
  process, including the isolated RF-reference probe.
- Result: The first JLC report found four Danger/two Warning silkscreen-to-hole
  findings. Moving two full-size labels resolved them. Final2 ZIP
  `2cae8b12bdf20b3c8633f8db0c59cc6911a49a43ed82e1e1bdc381e6a9d69e34` passed records
  `637343111455133697` and `637343305880473601`: 0/0, 29 rows, 449 green measurements
  each; unchanged rules, SMT off. Both PDFs and raw results are preserved.
- Result: Fresh r06 nominal fit passes 69 component envelopes and 30 shell checks.
  Top/bottom and populated previews were inspected. No physical IP68 result exists.
- Validation: Seven router, two inner-power-path, five SIM-topology and two
  checkpoint rejection regressions pass; handoff and resume verification pass.
- Next: Select/model the real six-layer stack and RF geometry; close circuit/BOM,
  battery/NTC, antenna, factory-test and enclosure qualification requirements.
  PCB DFM completion does not lift the electrical or manufacturing HOLD.


## 2026-10-25 — RF stack candidate, reference coverage and repeat JLC DFM

- Event: Reviewed the actual six-layer stack and RF geometry after r05h completed PCB DFM.
- Decision: Preserve r05h. Use a separate r05i candidate with 0.36 mm main port
  tracks, two bounded module escapes and a GNSS elbow clear of a reference opening.
  Retain the FEM matching geometry and all unrelated copper/pads/vias/rules.
- Result: Native DRC/ERC/parity remain zero. The old GNSS centerline passed while
  0.006699 mm² of track projected into a plane opening; the revised trace is fully
  backed. 1,761 native Contains probes agree with independent polygon handling.
- Result: JLC records 637347019288170498 / 637347305582972929 each report 0/0/450,
  all 29 rows analyzed, same ZIP f662f1db64ef1958e7e15c63b44869413883fd36e80b82642b9e8262f0e72f2d,
  unchanged rules, SMT off. Both full PDFs and the copper comparison were inspected.
- Result: 69 component envelopes pass at 0.71/0.81/0.84088/0.91 mm; the old carrier
  still fails. Four RF regressions pass. Power estimates use actual catalog inner
  copper and the upper finished-thickness bound, with unqualified load/plating assumptions.
- Limits: Supplier Er/etch/mask/thickness conventions disagree. Both module RF pads
  have In2.Cu VBAT below them; their GND was retained. R3 has a two-entry attachment
  ratio of 2.09–2.41. Module escapes, tuning stubs and physical RF remain open.
- Next: Fix/review that local geometry in a new successor, resolve stack/process
  parameters, then close power/component/pack/antenna/factory/enclosure requirements.
  No supplier message, order, payment or physical test occurred. Release stays HOLD.

## 2026-10-25 — R3 balance, shorter tuning branches and two clean r05j reports

- Decision: Preserve r05i and isolate the two LTE route changes. Move R3 0.30 mm
  after the first local trial improved the immediate entry but worsened its outer
  contour. Keep that trial's native source and reports as evidence.
- Result: One 0.36 mm entry per R3 land; unique-copper ratios improve from
  2.288/2.413/2.090 to 1.004/1.003/1.001. C11 branch is 0.42 mm; C12's former
  2.84 mm branch is removed. Main feed length grows from 5.89 to 8.91 mm.
- Result: Native DRC/ERC/parity have zero findings. All other placements, lands,
  vias, non-LTE copper, planes, module escapes, stack and rules are unchanged.
  1,742 native probes agree and all RF trace copper is backed by In1.Cu. All 94
  local grounds, 128 return screens and 12 power backbones pass. 69 populated
  envelopes pass four thickness cases; original-carrier control still fails.
- Result: Same ZIP `8fd625d3da7b8bd3c59ea9aa0fd625dc93d458fe23b64a6fd7bc69d4c6915e50`
  passed JLC records `637352328236847105` and `637352583225630721`, each 0/0/450,
  29 rows and unchanged rules, SMT off. Both complete PDFs and the actual copper
  drawing were inspected. No order, payment, supplier message or physical test.
- Decision: Retain module-pad In1.Cu for this prototype to avoid exposing lower
  VBAT. Width alone does not establish excess pad capacitance; this is not full
  implementation of Nordic's cutout recommendation or RF acceptance.
- Next: Exact R1/R16–R23 MPN/tolerance/TCR and effective C9/C25/C26 bounds, then
  power, pack/NTC, antennas, factory delivery and enclosure definitions. Do not
  reroute a completed DFM milestone without new evidence. Electrical, RF,
  manufacturing and physical ingress qualification remain open.

## 2026-10-25 — Selected power parts and two clean r05k reports

- Decision: Preserve r05j. Select exact power resistors with manufacturer tolerance,
  TCR and height data. Use 200k / 26.1k / 3.4M for the feedback network and replace
  NRND C25 with the in-production 1uF C9 MPN. R21 uses a pulse-proof 0.2W series.
- Result: Initial-tolerance/TCR and additional-drift screens pass conditionally.
  Manufacturer typical small-signal capacitor data supports the conservative
  effective-capacitance sensitivity inputs; it does not guarantee lot/age limits.
  The former 600ms firmware wait fails; provisional wait is 1s. Five regressions pass.
- Result: Exact prototype MPNs now cover all 65 fitted references / 38 unique parts.
  Schematic, PCB fields, BOM, native netlist and candidate CPL agree. All copper,
  stack, rules, placements and original net membership are unchanged from r05j.
  Native DRC/ERC/parity have zero findings. No native process crashed in this work.
- Result: All 69 populated envelopes pass four thickness cases using sourced
  resistor heights and the larger C25. Original-carrier negative control still
  fails. C25 retains 0.60mm to the existing battery reservation.
- Result: Same ZIP 673c1d30bf2192f8abe60cf211ac183210472b8924f3fd4c3b5b46bd992412fc
  passed records 637356580811132930 and 637356797304328193, each 0/0/450,
  29 rows, unchanged rules, SMT off. Both full PDFs were rendered and inspected.
- Limits: Exact candidate MPNs do not establish procurement/SMT/powered acceptance.
  Effective capacitance/aging, timer extrapolation, abrupt collapse, actual cell,
  antennas, RF and ingress remain unqualified. UVLO retains pull-up consumption;
  protected-cell cutoff and charging recovery remain part of the pack review.
- Next: Protected NTC pack and actual antennas, then occupied-volume checks,
  harness/dock/positive retention, firmware and factory programming/test.
  No supplier message, order, payment or physical test occurred.
