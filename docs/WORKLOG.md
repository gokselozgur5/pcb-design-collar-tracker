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


## 2026-10-25 — Battery charging mismatch and current PCB review package

- Finding: The direct 10k/B3435 NTC option permits charging at 50 C. The inspected
  EEMB pack allows 0–45 C charging; r05k U3 /CE is grounded. This is a source-based
  incompatibility, not a powered test or an implemented correction.
- Finding: EEMB LP503030-PCM-LD specification ZJQM-RD-SPC-A04005 rev 0.0 lists
  700mA for the bare cell but only 350mA continuous / 1A for 3s for its PCM.
  It is not selected; pulse duty cycle, recovery, voltage tolerance and aging remain open.
- Result: Added a source-bound charge review with manufacturer hashes, a table-point
  calculation and explicit beta-model sensitivity. Three regressions pass; the
  standalone check intentionally returns exit 2 for electrical HOLD. Handoff
  verification reproduces the finding without accepting the circuit.
- Research: Synzen ZETA SZK-C-0G04 is a narrower 40x10mm GNSS FPC candidate with
  a 100mm/1.13mm cable. No antenna, cable, battery or enclosure fit change is claimed.
- Delivery: A 119-file current PCB bundle includes native KiCad, unchanged Gerber,
  candidate BOM/CPL, two complete JLC reports and the new charge HOLD. ZIP SHA256
  12d93e0acee77f66a877c1fad46a807d53b1fac592f4b3f85fb52fe546bb66e6.
  Fresh native top/bottom SVG exports exited 0; their raster views and actual review
  PDF were inspected. The original tested PCB and Gerber bytes remain unchanged.
- Next: Implement the actual-cell charge interlock in an isolated successor, with
  boot/reset/low-cell/sensor-fault behavior. Then finish full pack/NTC selection,
  antenna/harness/retention/sealed assembly and firmware/factory acceptance.
  No new supplier upload, message, order, payment, account switch or physical test.


## 2026-10-25 — r05l charge interlock and r07 carrier

Implemented a VSYS-powered hot/cold window using two TLV3012B comparators and a
SN74LVC1G00 NAND driving BQ25185 /CE. Sixteen parts are added; all original 71
footprints/lands and 27 RF segments remain unchanged. Only original pin U3.4
changes net; local VIN routing changed to open its escape. The temperature model
and four regressions pass conditionally; powered startup/thermal tests remain open.

The first JLC run found 3 Danger / 4 Warning. Three full-size labels and one VIN
via moved; a fresh native check also caught and corrected its VBAT clearance.
Final PCB `241c84d6...379b3` and ZIP `c736c5d3...af5d2` pass native DRC/ERC/parity.
Two actual records, `637366592129687553` and `637366801595977730`, each have
0 Danger / 0 Warning / 455 Good across all 29 rows, with unchanged rules and SMT off.
All 109 physical GND pads have local via paths and all 154 signal vias pass the
inherited 2mm return screen. Candidate assembly exports contain 81 parts / 44 MPNs.

The r07 carrier has a U12 relief and one moved leg. Eight meshes pass integrity
checks, 85 envelopes pass four thickness cases, and the independent CAD intersection
is empty; restoring the previous carrier produces 1.234mm³ interference. Four
previews and both supplier PDFs were inspected. No physical ingress or powered
acceptance is claimed. New source-bound verification and a PCB/enclosure review
bundle provide the continuation point. Next: protected pack/NTC attachment and
actual antennas, then harness/dock/retention and firmware/factory test.

## 2026-10-26 — r08 antenna assembly and current review delivery

Selected Synzen CAPH SZK-C-3L30 and ZETA SZK-C-0G04 as prototype antenna
candidates. Their sourced size classes replace the old placeholders. Two smooth
nominal cable paths terminate at native J1/J2 positions, with four internal lid
guides. Body height increases 3mm: rigid shell plus lid 57.4 × 49.4 × 20.6mm;
boot 60.4 × 52.4 × 25.4mm. A 20mm M2 fastener candidate and blind boot tip pockets
replace the earlier length assumption. Seal/contact dimensions are unchanged.

The first straight GNSS exit guide interfered by 0.031656mm³; a widened straight
channel still interfered by 0.013088mm³. Both failures are preserved. The final
curved channel has zero CAD interference. Restoring 1mm channels yields
4.399098mm³; restoring the old carrier yields 1.234334mm³. All 85 populated
envelopes pass four thickness cases, all 34 shell/seal/fastener screens pass,
and eight exported meshes are closed/oriented/connected. Five previews and both
pages rendered from the actual review PDF were inspected. Four discriminating
geometry regressions pass; the 45-file source/evidence checkpoint verifies.

Battery selection remains open. Current VARTA 014-pack data is distinct from
older 099 documentation, and the larger pack does not fit. Akyga cell ratings
do not establish its PCM limits. Corrected the inherited 600mA continuous target:
it is engineering headroom, not Nordic's stated approximately 500mA peak at 3.7V.
The next pack decision needs a bounded pulse/duty-cycle load, voltage/drop,
protection/recovery and charge compatibility. No battery was silently substituted.

Delivered a 260-file review package, SHA256
`c501ab26bbb190fc90ed5a23b79e8e9284c4cc28d2c437ac3e562cda44a05fdb`,
with the unchanged all-green r05l Gerber/native PCB/evidence and the current r08
CAD, meshes, drawings and selection limits. No new PCB edit or JLC upload was
needed. The prior r07 model and all earlier packages remain byte-preserved.

Cable end datums/tolerances, exact bend limit, feed bond, guide strength, opening
motion, actual pack/NTC attachment, retention/harness/dock, materials, firmware and
factory/physical qualification remain open. No powered, RF or ingress test,
supplier message, order, payment or account switch occurred. This is a conditional
assembly prototype, not a working-device or IP68 release.

## 2026-10-26 — Controlled battery request and r09 fit study

Prepared CT-BAT-001-A, an English supplier enquiry and a dimensioned PDF for a
complete protected pack with a cell-mounted SEMITEC sensor. No message has been
sent: separate user authorization is pending. This is a request, not a selected
EEMB part. Its 600mA continuous rating is engineering headroom. Nordic's typical
TX tables average one 1ms subframe and describe additional microsecond peaks;
neither those tables nor an invented reporting duty establishes the complete load.
Recorded the specific PCM, size and charging limits of the reviewed alternatives.

The requested 32 x 30.5 x 5.3mm body includes a requirement for service swelling
confirmation. Its sensor/bond/cover stack fits a 33 x 31.5 x 6.2mm reservation.
Raising the board, antennas, cables and shell by 0.4mm gives a rigid envelope of
57.4 x 49.4 x 21.0mm and boot of 60.4 x 52.4 x 25.8mm. PCB, seal/contact geometry,
all-green Gerber and prior review packages are unchanged.

All eight pack screens, 85 component envelopes over four board thicknesses and
34 shell checks pass their stated geometry conditions. Eight actual meshes are
closed/oriented/connected. Current carrier and cable-guide intersections are
empty; the old carrier produces 1.234334mm³ and undersized guides 4.399098mm³.
Four regressions include the original board height failing the wider pack.
Five CAD previews and the rendered supplier PDF were inspected. The 39-file
checkpoint verifies with standard Python, and the full handoff includes it.

No pack, adhesive construction, harness, retention or physical thermal behavior
is approved by the fit study. Supplier response, controlled leads/strain relief,
positive retention, dock, firmware and factory/physical qualification remain open.
Continue independent retention/harness/dock work while the enquiry is pending;
do not restart catalogue searches or repeat DFM on unchanged bytes. No order,
payment, supplier message, account switch or physical test occurred.

## 2026-10-26 — Captive PCB prototype with bounded-motion checks

Added r10's keyed retaining frame, four edge tabs, carrier guide rails, shell
locators and lid stops. The 40 x 32mm PCB, all-green Gerber, requested pack and
57.4 x 49.4 x 21.0mm rigid envelope are unchanged. The assigned ambient tolerance
stack allows the lid to seat and keeps four tab contacts across 27 offset/yaw
cases. It permits bounded free play; it is not a zero-motion or shock rating.

Swept envelopes for 85 populated parts clear the retention geometry by at least
0.205mm. This required larger D1/U12 reliefs, new C10/R29 reliefs and a 0.3mm leg
move. The original GNSS route failed when the PCB lifted; one GNSS control point
and the LTE initial bend were adjusted. Twenty-seven fixed-length cable poses
pass the component/bend/channel and separate wall/antenna/self-clearance screens.
The guide centers remain fixed. Sampling does not prove all continuous flex paths.
The SIM bridge was raised to preserve 0.20mm service clearance at assigned limits.
Six discriminating regressions cover the original failures and missing features.

The first carrier STL failed: 64 triangles collapsed at 0.00001mm and 75 oriented
edges were invalid. Preserved that export. Sharing the carrier's clipped outer
contour and local Z datum, with internal leg/frame overlap, fixes the geometry
without relaxing mesh acceptance. Solid checks run before preview rendering.

The final export exited zero: nine closed/oriented/connected meshes, five inspected
previews and all CAD controls pass. Current carrier, guide, swept-retention and
correct-key intersections are empty. The restored support gives 1.240259mm³,
undersized cable channels 4.391217mm³ and reversed key 0.576004mm³ of interference.
All 34 shell screens and four nominal board-thickness cases still pass. The actual
retention PDF was rendered and inspected. Read-only handoff verification includes
the new source-bound checkpoint; prior PCB/CAD/package identities stay unchanged.

The prototype drawing states its material and physical limits. Unfilled POM-C
remains a candidate, not an approved material. Resolve thermal expansion and
process capability next, followed by battery retention and controlled harness/dock
construction. The battery request remains unsent pending separate authorization.
No PCB edit, new JLC upload, native KiCad process, supplier message, order, payment
or physical test occurred. The whole-device release and IP68 qualification remain
open; preserve earlier checked revisions and their review packages.


## 2026-10-26 — Conditional thermal-fit prototype r11

Added four radial retainer/carrier keys, larger cavity/guide clearances, component
reliefs and revised LTE/GNSS paths. The SIM guide lane is open. The custom contact
stem is shortened from 7.70 to 7.50mm for the wider cavity; seal land/thread,
outside size and the all-green r05l PCB remain unchanged.

The preserved r10 candidate fails seven interface/closing checks under the same
assigned CTE intervals and independent -10 to +45°C part temperatures. r11 passes
29 thermal interface checks, 85 component envelopes, 27 cable poses, four nominal
thickness cases and 34 shell checks. Minimum component gap is 0.205mm, tab contact
0.162mm² and closing gap 0.058mm. Cable/body minimum is 0.235mm, bend radius
3.374mm and cable separation 0.322mm. The initial clearance failures are preserved.

Seven regressions pass, including the old thermal failures and comparison with
the preserved cable evaluator. Nine actual meshes and eight CAD controls pass:
current carrier/guide/retention/key intersections are empty; restoring the old
support, reducing guide bores and reversing the key produce interference.
The prototype drawing and generated views accompany the source-bound checkpoint.

Material bounds and machining tolerances remain engineering requirements. Cable
shape search changes plug azimuth by up to 30 degrees and does not qualify actual
connector loads, continuous deformation or flex life. Tilt/load, moisture/creep,
physical thermal fit and ingress remain open. No PCB change, new JLC upload,
native KiCad process, order/payment or supplier message occurred.

Next: battery retention and controlled harness/dock, supplier-pack confirmation
once sending is authorized, firmware and factory/physical qualification. Saved
handoff verification includes r11 while preserving all previous checkpoints.


## 2026-10-26 — Conditional pack-retention prototype r12

Added a shell-integral cradle and a retaining cap on the removable PCB carrier.
The requested pack seats on the existing floor, 0.3mm below the r09 drawing.
PCB, outside dimensions, contacts/seals and antenna paths remain unchanged.
The added 30.5 x 29 x 4.8mm minimum pack is an engineering capture requirement,
not a supplier-confirmed product; CT-BAT-001-A is unchanged and unsent.

The initial cap hit bottom-side parts and lacked guaranteed capture regions.
Added five component reliefs, a north capture tongue and a larger NTC opening,
and moved a bridge. The final 55 checks cover 85 component envelopes, raised
pack/sensor travel, contact hardware and cavity/attachment geometry. New-solid
gap is 0.224722mm, raised NTC gap 0.222928mm and minimum guaranteed capture area
1.4291mm². The raised-sensor check keeps the cap and PCB on their common carrier
datum while allowing independent component temperature and feature errors.

Both changed meshes are closed, oriented and connected. Four current CAD
intersections are empty; missing component reliefs, a blocked NTC opening and an
undersized cradle give 7.568243, 3.345152 and 326.689565mm³ interference.
The component CAD check includes the same cap tolerance envelope as the
analytic screen; its first nominal-only negative control did not exercise that
condition. Four previews and the actual dimensioned PDF were inspected.
Seven regressions and the 26-file checkpoint pass; the saved handoff includes r12.

Next: controlled harness/dock and pack lead-exit/strain-relief geometry, then
firmware and factory/physical tests. Pouch contact/abrasion, cap strength/creep,
tilt/load, material/thermal behavior and IP68 remain unqualified. No native KiCad
process, PCB edit, repeated JLC upload, order/payment or supplier message occurred.


## 2026-10-26 — r13 charging-dock geometry and external harness

Implemented the two-piece external dock around real Mill-Max 0962 contacts,
a Tensility USB cable, Alpha pigtails, a Littelfuse fuse and a T18R retention bay.
Added positive flange stops and extended the collar's external key to 4.0mm /
Z=7.7–13.2mm. The old 6mm alignment block and short/high key fail the new checks.
PCB/Gerber, seals, boot, pack and original CAD remain unchanged and preserved.

29 conditional checks pass, including 64 spring/seat/head/gap corners, continuous
wire-radius bounds and native J3/J4 pinout. Three actual meshes are closed and
connected with clean CGAL diagnostics. Six CAD controls pass; reversed key and
undersized bore interfere by 3.795 / 2.155mm³. Seven regressions pass. Both actual
previews and the generated PDF were inspected.

Preserved three rejected checks: the boot imported in its print frame, an
intentional jacket/saddle bearing line rejected by an empty-only check, and a
head-pocket/floor tangency that raised a CGAL warning despite valid STL edge counts.
Restored the assembly transform, separated intended bearing from clearance, and
opened the tangent edge with a lower relief. Final export rejects CAD warnings.

This is nominal/conditional geometry, not a production power path. Magnet/positive
holding, pin-motion wire slack, crimp/splice/sleeve process, internal lugs/J3 route,
source/fault behavior, pack supplier/lead exit, firmware and physical acceptance
remain open. No native KiCad process, repeated DFM upload, supplier message,
order/payment or physical test was performed.

## 2026-10-26 — r14 constant-length dock-wire geometry

Replaced the r13 rear-seated straight pigtails with a bounded, constant-length
wire family covering the 2.1421mm conservative contact movement. At the assigned
endpoint/cut limits, residual slack is at least 0.3858mm and the continuous
bend-radius lower bound is 8.6961mm against the wire's 8.382mm requirement.
The external dock grows to 94 x 36 x 16mm; PCB, wearable parts, seals and contact
seats are unchanged. No unused spring/latch catalogue part was selected.

42 analytical checks and twelve regressions pass. The complete interval wire
envelope, stationary harness, seated pins and wearable clear the housing in CAD;
the old housing intersects the envelope by 219.5552mm3. The aligned reverse key
still blocks with 3.7950mm3 intersection. Both new housing meshes are closed and
have clean CAD diagnostics. This is a geometric study: fixed-end restraint,
forming/cut process, repeated flex and dock holding remain unfinished.

Prepared one current review package with the unchanged all-green Gerber, native
PCB source, candidate assembly files, both actual JLC reports, revision-mapped
wearable meshes, new dock evidence and the unsent battery request. The old review
packages remain preserved. The complete tracker is not ready for a working-device
order, and no powered/RF/physical ingress result is claimed.

The actual dock previews and all three review PDF pages were inspected. The
19-file r14 checkpoint, 50-file review archive and full 30-section saved handoff
pass; archive SHA256 is
`17d6c1bcd7c9cb80dcb81152aed5759dd90f17a78eb1396d2eba5fdcbf9193a0`.
Changed-source syntax/JSON, 66 local links, 22 public text credential-pattern
screens and whitespace checks pass. No native KiCad process or repeated JLC
upload was needed. Supplier approval and physical qualification remain open.

## 2026-10-26 — r15 wire clamp and forming fixture

Implemented the previously missing fixed-end clamp with a separate cap, two
closing stops and four converted HT-6210 pad candidates. Added a separate open
forming fixture for the rear-seated nominal pigtails. The dry external dock grows
from 94 to 101.5 x 36 x 16mm to retain the existing free-wire length and make room
for the clamp ahead of the splices. Wearable, r05l PCB, Gerber, seals and contact
seats remain unchanged. The Southco research did not select a latch.

19 clamp and 42 inherited geometry checks pass, with 5.50..43.52% local pad
displacement at the assigned limits. The first nominal-only pad pocket did not
allow the largest converted outline; the final 6.2 x 3.2mm pockets and a negative
control cover that error. Ten regressions pass. Four closed part meshes and
thirteen CAD controls pass: five clear intersections, three specified contact
surfaces, and five deliberately bad assemblies with positive interference.
Contact triangles are checked against their exact planes/footprints; no contact
band is removed from acceptance checks. Binary STL avoids the ASCII coordinate
rounding observed in the first planar-contact evaluator. Deliverable meshes have
no CAD warnings; the zero-thickness analysis surfaces are not exported as parts.

This is a clamp prototype, not measured retention. Pad pressure/friction/creep,
insulation condition, endpoint slip and cyclic flex are unqualified. Position
error and slip share the inherited 0.10mm feature budget. The 5N / 60s pull target
is a proposed acceptance test, not a result. Screw/nut candidates are identified,
but incoming screw-length tolerance, torque and sourcing remain unaccepted.
Dock holding, internal lugs/J3 wiring, complete-pack approval, termination/fault
behavior, firmware and powered/RF/ingress acceptance remain open.

Preserved the r14 review archive. Its embedded STATUS/RESUME documents are dated
snapshots; their archived hashes remain checked without requiring them to equal
current prose. CAD/source/evidence bytes still match their repository inputs.
The new current review includes the unchanged all-green PCB and r15 evidence.
No native KiCad run, repeated JLC upload, supplier message or order was made.

The 22-file r15 checkpoint and full 32-section saved handoff pass. The actual
three-page review PDF was inspected. The current 53-file review ZIP is
9,235,286 bytes; SHA256 `60e835545a58dc3cde28c71ff6c3b959b5b4f32a72354ec0e8de47d6d0c66215`.


## 2026-10-26 — r16 rear contact retention; harness still unfinished

Added custom terminal bearing plates and internal pockets after finding that the
6.4mm round backing reservation could not bridge a 7.34mm bore. The outside shape,
contact positions, radial glands and all-green r05l PCB remain unchanged. Native
J3 polarity is bound to the geometry. 26 dimensional/clearance checks, four closed
meshes, four CAD controls and eight regressions pass. The first terminal mesh
failed topology at an overlapping thickness step; its source/mesh are preserved.
Milling the step from one blank fixed the geometry without relaxing inspection.

Rear bearing is a geometric result, not a load/contact-resistance/IP68 approval.
Both internal wire paths remain HOLD; failed drafts and the exact continuation
are saved in assembly/internal-charge-r01. No full harness, firmware or physical
qualification was completed. Current review/package updated to r16; no new native PCB run, DFM upload, supplier message or order.


## 2026-10-26 — Internal charge harness r02 candidate

Implemented both nominal internal routes, stripped ends and bounded solder-joint
envelopes in the unchanged r16 shell. Selected Alpha 2841/7 30 AWG only for the
internal pair after the 26/28 AWG searches failed the combined constraints. The
external dock wire, PCB and all published manufacturing files are unchanged.

41 geometry checks include continuous Bezier bend/length bounds, native pad/net
identity, copper margins, terminal-hole insertion, insulation transitions, other
components, RF leads, retention parts and self/opposite-wire clearance. Two
closed wire meshes and three actual CAD controls pass; deliberately lowering the
ground wire gives 1.538mm3 interference. Seven regressions pass. The first route
with insufficient component clearance is preserved as evidence.

The simple movement proposal is rejected: only one of 27 poses passes; it needs
up to 0.978mm of length change and some poses fail RF/bend screens. Nominal lengths
43.766/54.921mm are not released cut instructions. Next solve a fixed-length
family, implement restraint and factory/service assembly, then finish the other
working-device gates. No supplier message, order, new PCB DFM upload, powered
test or physical water/dust qualification was performed.

## 2026-10-26 — First r05l factory observation firmware build

- Added a custom nRF9151 board, source-checked native GPIO/I2C mapping and deferred
  external-I/O startup after the 1s VIO allowance. The diagnostic reads LIS2DW12,
  MAX17048 and charger inputs over RTT; it does not initialize the modem.
- Installed a pinned, portable SDK on the mounted SSD and built the actual board
  target: 46,872 bytes flash / 8,256 bytes RAM. Seven native mappings and 14
  compile-time conditions passed. A separate wrong-pin/early-I2C build failed
  on both intended assertions. Saved logs and input/artifact hashes are in
  `firmware/evidence/factory-r01/`.
- No flashing or powered test occurred. Shipping tracking/radio firmware,
  provisioning, updates and full factory/device acceptance remain unfinished.

## 2026-10-26 — Correlated fixed-length internal wire search

- Added portable starting curves and a constrained two-wire search. Both wire
  lengths are fixed at all 27 sampled poses; terminal positions and tangent
  directions stay attached to their owning parts.
- Extended the independent 41-check route screen to correlated PCB/pad poses.
  All 27 length intervals pass the numerical tolerance; 18 geometry poses pass.
  Nine upper poses remain HOLD for black-wire RF clearance, and eight also fail
  the bend bound. The search score is explicitly separate from acceptance.
- Eight regressions pass. Nominal CAD, PCB/Gerber and published r16 bundles are
  unchanged. Next solve RF and charging paths together, then actual restraint
  and installation/service behavior. This is not a production wire cut list.

## 2026-10-26 — Include RF guide blocks in internal harness verification

- Added the four actual lid-guide blocks to both charge-lead screens, including
  the CAD roof overlap. Their bores and entry slits are not exclusions for these
  wires. The route screen now has 49 checks per pose.
- The nominal route and all 27 saved candidates clear the guide blocks; the
  minimum is 0.324mm. The prior 18/27 result is unchanged because the nine upper
  RF/bend failures remain. Nine regressions pass, including a deliberate lead
  through a guide. These are geometric checks, not physical qualification.
- Preserved the PCB, RF paths, enclosure, nominal wire meshes and release ZIPs.
  Work continues on the failing upper poses and a common wire cut length.

## 2026-10-26 — Refine continuous wire bounds and accept explicit RF candidates

- Added bounded refinement for short spline handles. Every acceptance still
  uses a continuous Bezier lower bound and the existing 6.604mm limit, never
  sampled curvature. Clearance sampling can also be refined while retaining
  its derivative-based travel allowance. Both resolutions are recorded.
- The route checker can receive explicit RF curves and physical guide data;
  it records the evaluated inputs and rejects missing identities. Its default
  still checks the preserved r02/r11 combination, which remains 18/27 and HOLD.
- Ten harness regressions pass, including a coarse bound that tightens while
  remaining below independently evaluated dense curvature. Native PCB, nominal
  wire meshes, guide solids and published release archives are unchanged.

## 2026-10-26 — r17 combined RF and charging routes

- Adjusted the GNSS loop and upper-pose black-wire curves. All four cables now
  pass together at 27/27 static PCB poses, with 78 geometry checks per pose and
  common centreline lengths. The actual old guide apertures remain in the model.
  Minimum RF-pair/charge-to-RF gaps are 0.204589/0.214946mm after allowances.
- Retained the 0.2mm separation and 6.604mm charge-wire bend limits. Short-handle
  curves needed tighter continuous bounds; two poses also needed a finer travel
  bound. The checker records those resolutions and pins input identity.
- Seven integration regressions pass in addition to the ten shared harness
  regressions. New-source verification is included in the normal handoff.
- Nominal RF witnesses clear the existing actual lid. Shifted full-cable
  negative controls produced tiny STL slivers at the mesh audit resolution;
  they were not accepted. A known cube inside the guide wall is used for the
  exact-volume Boolean control instead; no mesh-validity check is relaxed.
- PCB, enclosure size, guide solids and published r16 ZIP remain unchanged.
  Next implement restraint/forming and continuous/installation motion. Supplier,
  factory, powered/RF and water/dust acceptance are still open; no order or
  supplier message was sent.

## 2026-10-26 — Primary Turkcell LTE-M evidence

- Inspected Turkcell's 2025 Form 20-F, including the rendered network-evolution
  page. The operator states that LTE-M and NB-IoT are available on request
  throughout its 4.5G footprint and lists mobile tracking applications.
- Added the exact page and PDF identity to the connectivity evidence. This
  supports the nRF9151 prototype choice; it does not establish subscription
  activation, route coverage, completed-device acceptance or measured energy.
  The controlled local-SIM test remains open. No operator was contacted.

## 2026-10-26 — Correct charge-wire thermal and retainer clearance

- Found that r17 used nominal component/retainer solids for charge wires while
  RF used expanded envelopes. Preserved r17 and reproduced failure at all 27
  poses under the expanded charge screen; its earlier 27/27 result remains
  evidence of the narrower calculation only.
- Added two retainer top reliefs with a 0.5mm lower bridge, preserving all tabs
  and radial keys. Adjusted the GNSS lower turn while compensating at the left
  guide, and revised the charge routes. Actual lid guides, PCB, enclosure size
  and numerical wire lengths are unchanged. A sparse-search bend failure was
  rejected; an arc-length-based curve fit resolved the final difficult pose.
- r18 passes 27/27 static poses, 53 charge plus 29 RF checks per pose. Minimum
  thermal-component, swept-retention, charge-to-RF and RF-pair gaps are
  0.204214, 0.289911, 0.232517 and 0.213954mm. The continuous charge-wire bend
  lower bound is 6.605489mm against the unchanged 6.604mm requirement.
- Four closed mesh files and five CAD controls pass: no added frame material,
  3.254999mm³ removed, and empty nominal wire/joint, terminal and GNSS-guide
  intersections. The actual new assembly preview was inspected. Seven new
  regressions pass, and read-only verification is part of the normal handoff.
- Complete-device release remains HOLD. Restraint/forming, continuous and
  service movement, frame strength/creep, pack/supplier/process approval and
  factory/powered/RF/ingress qualification remain open. PCB/JLC, firmware and
  published review archives are unchanged. No supplier message, order, payment,
  flashing or physical test occurred.


## 2026-10-26 — r19 internal wire support and forming tools

Added a shared insulating J3 staking volume and two terminal staking volumes on
the preserved r18 routes. The captured bare sections, actual owning substrates,
combined placement/service allowance and trial cure/handling process are explicit.
PTFE adhesion is not relied on. The changed static geometry passes 27/27 poses
with 52 added checks per pose; the nearest added component gap is 0.22mm at R6.
Six regression tests reject the prior oversized volume/retainer corner, underfill,
missing reliefs and invalid ownership/physical claims.

Exported two separate labelled forming nests, their full-radius fit witnesses and
a two-page reviewed drawing. Seven delivered meshes pass the unchanged closed/
oriented topology check. Three empty CAD intersections and three positive failure
controls pass. Minimum floors are 2.0mm; conservative tool clearances are
0.072991mm red and 0.045949mm black after assigned tool tolerance and continuous
curve/facet bounds. Manifold 3.5.4 builds the solids; OpenSCAD produces labels and
renders the delivered models. The package pins its extra dependency. Official Dow
and historical NASA references were inspected; links/hashes are published and
PDF caches stay local.

The final r19 verifier and full saved handoff pass (39 top-level result keys, not
39 tests). All 49 local Markdown links checked, syntax and whitespace checks pass.
Three final previews and both PDF pages were inspected. The r19 checkpoint is
frozen. Resume output now points to r16's preserved review and the r19 addendum.
No PCB/Gerber/firmware/r16 bundle change, new KiCad/JLC run, supplier message, order,
flashing or physical qualification occurred.

Next: validate continuous and installation motion with the actual attachments.
The black PCB captured section demands up to 0.426mm change across independent
static poses; cured-support compliance is not established. Qualify released shape,
adhesion/creep/fatigue and frame bridges, then continue dock holding/source faults,
approved pack leads, shipping firmware and factory/powered/RF/ingress tests.
The battery enquiry remains unsent; full-device release remains HOLD.


## 2026-10-26 — Tracker r01 firmware and local receiver

Added a separate nRF9151 non-secure board, TF-M memory map and pinned modem SDK
extension without changing the frozen factory firmware or PCB. The application
collects valid GNSS positions, writes a 64-record NVS outbox, uses LTE-M/mTLS and
removes records only after an exact server acknowledgment. An empty default host
and identity leave it offline. Sequence reservations survive reboot without reuse;
full queues reject the newest fix explicitly. A local-only HTTPS/SQLite receiver
binds device identity to the client certificate and commits idempotently before ACK.

The final clean custom-board build passed. Application flash/RAM: 106,020/27,000
bytes; TF-M: 64,816/45,388 bytes; modem shared region reserved separately at 40 KiB.
The merged HEX SHA-256 is
`38f87835aba1709f31c14800926eb89054842885d4b69931a93f28fa7cddcce8`.
Inspection confirmed reset vectors at zero and 0x40000, disabled external UARTs,
non-secure storage access and no programmed bytes in the NVS region. Two valid-
checksum image mutations fail inspection. Earlier SDK defaults left the secure
image at 0x10000 without a bootloader; the explicit standalone map corrects that.
GNSS configuration now follows functional-mode activation, and its ISR only signals
main. An incremental SDK reconfigure produced malformed security-option strings;
the builder requires a new directory. No warnings or checks were disabled.

Seven local receiver tests pass, including real TLS with the actual C-generated
payload, missing certificates, identity mismatch, duplicate/conflicting records and
read-only database failure. Host C tests pass with address/undefined sanitizers:
six injected before/after mutation failures, 40 record-byte corruptions, reboot
replay, stale ACK, capacity/order and protocol boundaries. These do not exercise
physical flash or the modem. Full saved handoff passes (40 top-level result keys,
not 40 tests), as do 51 local documentation links and new Python syntax. A final
license whitespace normalization was followed by the scoped tracker verifier.

Evidence is frozen in `firmware/evidence/tracker-r01`; compiled source and saved
configuration identities are included. Firmware binaries remain local. The r19
assembly, factory firmware, current Gerber/JLC records and r16 review are preserved.
No credentials, private keys, public service deployment, flashing, supplier message,
order or physical test was added.

Next software: bounded DNS and modem/watchdog recovery, credential provisioning,
signed-update/migration design, then actual GNSS/LTE-M/TLS/power-cut/current tests.
The 300-second interval and queue policy are provisional; battery runtime is not
measured. Continue r19 attachment/installation/continuous-motion and physical
qualification separately. The CT-BAT-001-A enquiry remains unsent with authorization
pending. Complete-device and ingress release remain HOLD.

## 2026-10-26 — Tracker r02 DNS deadline and watchdog recovery

Implemented r02 separately from the frozen r01 and factory sources. A permanent
resolver worker retains ownership through timeout, frees late SDK results and
prevents overlapping calls. Main waits 30 seconds by default, then takes the modem
offline and drains the worker under a finite cleanup lease. The supervisor checks
main-progress deadlines every 500ms; fault/expiry stops feeds to a 5-second hardware
watchdog. Late main progress cannot clear failure. A modem fault callback only sets
an atomic flag. Watchdog/lockup boot waits 120 seconds before modem initialization.
Permanent storage validation failure enters service hold without application erase;
uncertain mutations reset for the unchanged outbox's boot reconciliation.

The clean custom NS/TF-M build passed. Fixed a host/ARM enum signedness difference
exposed by `-Werror`; warning handling was not weakened. Application flash/RAM:
110,608/30,560 bytes; TF-M: 64,816/45,388, plus the existing 40KiB modem reservation.
Actual reset vectors remain 0/0x40000 and no programmed bytes enter persistent
storage. The complete image SHA-256 is
`7d7b6d7bad55d9dc22b2e6c40b726065f6b02bc5dd1e17466a976b5d750c11a1`.

Five host scenarios pass with ASAN/UBSAN, including the actual DNS/supervisor sources
under a POSIX adapter. Policy tests cover 30 ordered completion/deadline races.
The shortened 1-second DNS case returned after 1,099ms on this host while its fake
resolver still owned the call; all four test allocations were freed. Fault/expiry
stop feeding and a missing watchdog rejects initialization. Two real HEX mutations
and two compiled-config mutations are rejected. These results do not prove Zephyr
scheduling, modem DNS timing, actual watchdog reset or physical flash recovery.

Saved 59 source/evidence identities in `firmware/evidence/tracker-r02/`, added
read-only handoff verification and updated continuation instructions. Original PCB,
JLC results, r19 assembly, r16 review, factory/r01 sources and SDK pins are unchanged.
No public API deployment, keys, flashing, supplier message or order was performed.
Next implement provisioning and signed-update/migration support in a new revision;
then run actual GNSS/LTE-M/TLS, DNS/AT fault, reset, power-cut and current tests.
Approved pack, assembly, factory/SMT, RF and immersion acceptance remain open.

The full saved handoff passes (41 top-level result fields, not 41 tests). Syntax
checks pass for eight Python files and 90 local Markdown targets resolve. Source
whitespace checks pass; the byte-preserved generated TF-M cache retains three
upstream trailing-space comments. They are kept as captured build evidence.


## 2026-10-26 — Signed tracker r03 and bounded trial

Preserved the PCB, JLC evidence, r19 assembly and factory/r01/r02 firmware. Added
an isolated dual-slot nRF9151 board using the pinned SDK memory map, P-256 MCUboot,
primary validation, boot flash protection and software version downgrade checks.
A trial needs a fresh persisted fix, an upload ACK and 30 seconds of uptime within
600 seconds. Missing evidence or confirmation failure requests watchdog reset;
actual board trial/revert remains untested. No update transport was added.

The final clean ARM build passes: application flash/RAM 113,396/31,776 bytes,
TF-M 64,304/45,388 and MCUboot 26,072/16,048; modem shared RAM remains 40KiB.
Verified both signed outputs with the public key embedded in actual bootloader
bytes, their common payload, vectors at 0/0x10200/0x50000, and no NVS/secondary
writes. Complete local prototype HEX SHA-256:
`babe3feb4888b849945fc905d77a782f7d6efdd54966bb624a438b9221028633`.
The key is development-only; its private half remains ignored and local.

Six host trial scenarios pass under ASAN/UBSAN, using the actual trial code and
an accelerated clock; reset exit 42 is a host sentinel. Nine actual image/key
negative controls pass, including corrupted signatures/payload, another key,
programmed NVS, missing boot vectors and disabled compiled protection. A renamed
copy of the SDK public private key is rejected. The simulator preflight now rejects
`MCUBOOT_SKIP_SLOW_TESTS`; the actual run environment has no skip flag.

The first sysbuild attempts exposed key-argument quoting and nested cache behavior.
Both direct children and TF-M's nested CMake need explicit cache forwarding.
Earlier logs selected the external macOS user cache; all four announcements in the
final build point inside the task SDK. No unrelated external cache was removed.
The TF-M experimental and CMake policy notices are preserved, not disabled.

MCUboot simulation uses the pinned Nordic bootutil source with ECDSA, primary
validation, swap-offset and software downgrade prevention. Its upstream Cargo
feature still restricts downgrade prevention to overwrite mode, although the
pinned C code implements swap prevention; the supported C flag is supplied
explicitly. Two NCS-only configuration constants match the actual target config.
A host-only header supplies MbedTLS OID constants for the SDK's renamed include.
GCC 15 with explicit installed macOS headers preserves upstream -Wall/-Werror;
Apple Clang reported unused SDK stubs and GCC's default fixed headers required an
unavailable SDK header. No SDK source or warning policy was changed. All 18 pinned
module working trees have no tracked modifications. Host TinyCrypt and upstream
flash geometries differ from target Nordic Oberon and the collar flash driver.

Next implement offset-aware staging/delivery in a new revision. Swap-offset writes
start at 0x81000; the pinned NCS FOTA target starts at the slot base and cannot be
connected unchanged. Review production key custody, provisioning/debug protection
and an explicit factory/SWD migration from the standalone r02 layout. Preserve NVS
sequence reservations or change server identity after an intentional full erase.
Real boot/swap/revert/power cuts, watchdog handoff, modem/SIM/TLS, current, factory,
approved battery/assembly, RF and ingress acceptance remain open. No flashing,
deployment, supplier message, order or new KiCad/JLC run occurred.

The MCUboot run completed in 812.69 seconds with 25 registered core tests passing;
feature-inapplicable cases return early and are not counted as exercised hardware
coverage. Basic revert, signature rejection, software downgrade rejection, random
interruptions and exhaustive simulated write-interruption recovery completed.
The wrapper subsequently failed while looking for Cargo.lock under sim/; the lock
is at the workspace root. Corrected metadata collection and preserved the original
traceback alongside the complete passing Cargo output; tests were not rerun.
Saved 84 source/evidence identities in the r03 checkpoint.

Full saved handoff passes (42 top-level fields, not 42 tests). Python syntax,
87 local Markdown targets and source whitespace checks pass. The raw generated
TF-M cache/build/simulator logs retain their original whitespace and blank lines
as captured evidence; source checks exclude only those three raw files.

## 2026-10-26 — Actual supplier assembly review

Returned priority to factory assembly after the PCB delivery/status confusion.
Preserved r05l native sources, its Gerber and two clean PCB DFM reports, all
firmware checkpoints and the r19 mechanical assembly. Added an exact-source
supplier BOM/CPL for 81 fitted references / 44 MPNs, with 58 top and 23 bottom
placements. Verified the actual Gerber origin/bounds rather than recentering or
mirroring coordinates. Exported 23 interface lands, 18 pin-1 lands and 364 native
fitted pad shapes (including unnumbered paste apertures) in one read-only KiCad
load; source bytes and the native net mapping are unchanged.

Actual JLC matching found 43/44 exact MPNs. Q1 DMN62D2UDW-7 did not match, and
manual base-part search returned no exact result. Broader search returned other
parts; no substitute was selected. The initial preview contained only 80 mounted
references and exposed library/native rotation differences. Compared all numbered
lands on 14 IC/discrete references and corrected 13 supplier CPL angles. U1 stays
at zero. Native centres, sides and the complete 81-reference BOM/CPL are retained.
J6 has an exact MPN match but no returned library model; J1/J2 have different
library numbering/origin/land arrangement and remain open for manufacturer review.

The corrected upload's in-browser digest equals the local CPL SHA-256
46f4a72547b5607c65bfd7fb53e33b2f65f599997b18a1b7e72a21b5cbf5f01e.
Reloaded the supplier page because the existing preview retained old models after
reupload. The new downloaded placement data reproduces all 80 available centres,
sides and angles; Q1 is the only missing reference. Inspected both initial and
corrected top/bottom previews and preserved sanitized data/screenshots. Pin-order
agreement is not land/stencil/reflow or supplier process acceptance. No complete
SMT run, placement approval, supplier message, order, powered test or flashing
occurred. Empty SMT counters and an incomplete 80-part preview are not passes.

Packaged native/Gerber sources, PCB reports and the assembly-review evidence in
release/collar-tracker-r05l-pcba-r01-review.zip, SHA-256
ee58b3a4a8cc11abcf11b3aa33862035d5d807bfa9cd464adcbf876da576abab.
The read-only PCBA verifier checks identities, native nets, reference coverage,
unapproved substitutions, unchanged centres/sides and actual supplier read-back.
Full saved handoff passes with 43 top-level fields, not 43 tests. Seven changed
Python files parse and the reviewed Markdown links resolve. No fresh PCB DRC/DFM
was necessary for these unchanged native/Gerber bytes.

Next resolve Q1 sourcing and the three connector-library cases, then accept the
complete 81-part placement and run actual SMT review. Protected-pack approval,
factory programming/testing feasibility and powered/RF/ingress acceptance remain
open; the battery enquiry is still unsent. Further OTA development is deferred
behind manufacturing review. Whole-device release remains HOLD.

## 2026-10-26 — Connector origins and mandatory Q1 sourcing

Created PCBA r02 without changing the frozen r01 evidence, native r05l PCB,
Gerber, BOM or physical placements. Compared the Hirose recommended pattern
with both U.FL footprints: native signal/ground lands match its nominal dimensions.
The JLC library numbers signal/grounds differently and its model centre is
0.6320028mm right of its footprint origin. Applied that supplier-specific X offset
to J1/J2 in a new review CPL, retaining the thirteen prior angle corrections.
Its browser-upload SHA equals local SHA
5aa23f9f2b6a56a33e6bc581511507f6b09b449acc34ac6c0eb6119ab3ffd02f.

Reloaded JLC after upload. The actual downloaded preview reproduces all 80
available references, coordinates, sides and angles; all 43 matched MPNs remain
unchanged. Inspected both sides: U.FL models now align, while J6 still shows a
placeholder and Q1 remains absent. No placement approval or complete SMT run
was submitted. Factory placement-datum and stencil/process acceptance remain open.

Checked all eight native J6 lands against the GCT D6 component-side drawing,
including the no-peg variant, unused C6/VPP and both grounded shields. The socket
opening faces Gerber +Y; insertion proceeds toward -Y. Checked Q1's six terminal
functions and standard SOT363 lands. Added an original one-page placement drawing,
source provenance and a candidate screen for DMN62D0UDW-7. Its pin arrangement
agrees and its 25C 1.8V RDS limit is lower, but the inherited hot/falling-rail
assumptions remain unqualified. JLC's exact candidate search at 07:21 UTC showed
only one unit. No substitute was selected; original Q1 stays mandatory in the BOM.

The read-only verifier reproduces manufacturer/native dimensions and functions,
rejects the prior U.FL origins on both references and checks the actual corrected
supplier read-back. Full saved handoff passes with 44 top-level fields, not 44
tests. Five changed Python files parse, 108 local Markdown targets resolve and
source whitespace checks pass. Clarified the insertion-arrow label after the full
run, rebuilt the drawing/package and reran the affected r02 verifier successfully.
Review ZIP release/collar-tracker-r05l-pcba-r02-review.zip has 39 members and SHA
0a56cff3d99c196ac2c967f5055e3c1eda5d70446295cf4aa8c010bb14a1b4a5.
Its root START-HERE identifies the current BOM/CPL and remaining release gates.

Next obtain Q1 sourcing and the J6 model/placement decision, confirm factory datums,
then review all 81 fitted references and run SMT analysis. Approved protected pack,
factory programming/testing and physical qualification remain open. No supplier
message, order, payment, flashing or powered test occurred. The browser was closed;
account/session data remains ignored. Firmware work stays deferred.

## 2026-10-26 — Prepared PCBA engineering enquiry

Inspected the saved JLC bottom placement page with J6 selected. It still has a
placeholder; no custom-model upload control was found in that page. This does
not exclude a supplier engineering route. Reviewed JLC's sourcing, global
sourcing, programming and contact-form guidance. The original Q1 distributor
listing is not normally stocked; the previous one-unit D0 observation remains
insufficient. An onsemi NTJD4401N direct swap was not accepted because its
datasheet does not guarantee on-resistance at the existing 1.8V screening point.
No original BOM, native placement or frozen evidence was changed.

Prepared assembly/supplier-r01/request.txt for JLC PCBA Engineering, covering Q1,
J6, placement datums, programming/testing and complete-device assembly scope.
The exact existing r02 ZIP is its single attachment: 6,997,076 bytes, 39 members,
SHA-256 0a56cff3d99c196ac2c967f5055e3c1eda5d70446295cf4aa8c010bb14a1b4a5.
Its integrity passes and it fits the contact form's displayed 10MB limit.
Full saved handoff passes; 51 local Markdown targets resolve and source
whitespace checks pass. These checks do not add SMT or physical acceptance.

Next obtain separate authorization to send this reviewable enquiry, then record
the actual supplier response before changing sourcing or approving placement.
The previous battery enquiry remains unsent with its authorization unanswered.
No supplier message, order, payment, placement approval, flashing or physical
test occurred. Closed the browser and kept raw/account data ignored.
