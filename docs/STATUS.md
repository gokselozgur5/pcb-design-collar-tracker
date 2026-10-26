# Current state — 2026-10-26

**Latest user-directed work: the 3D enclosure and adjustable collar mount are delivered as a prototype design.**
[Open the offline 3D viewer](../mechanical/universal-mount-r01/viewer.html) ·
[Design overview](../mechanical/universal-mount-r01/design-overview.png) ·
[Portable CAD/mesh/image ZIP](../release/collar-tracker-3d-universal-mount-r01.zip) ·
[Dimensions, assembly and limits](../mechanical/universal-mount-r01/README.md).
The user explicitly redirected work to enclosure visualization and attachment
across collar sizes. The new flexible holder uses two adjustable wrap straps and
flat/V-groove pads. Six nominal collar examples, 25 interference queries and
33 closed meshes are checked. Native r05m PCB, existing rigid enclosure and
manufacturing artifacts are unchanged. This supersedes the prior instruction
to defer new mechanical work; it does not resolve manufacturing acceptance.
Next mechanical step is an inert fit sample for threading, grip, closure and
comfort. No animal-worn, strength, RF or ingress qualification is claimed.

**Active r05m: stocked ROHM Q1 selected; native DRC/ERC/parity clean; copper and Gerber identical to r05l. All 44 MPNs / 81 placements read back from JLC. Actual SMT findings remain unresolved.**
**Working-device / RF / manufacturing release: HOLD. IP68 remains unqualified.**

Continue from `experiments/pcba-r05m-rohm-q1/hardware/`.
The preserved r05l and earlier sources remain immutable. All authored repository/GitHub
content is English. Run `python3 scripts/resume.py` before making another revision.

[Gerber ZIP](../experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip) ·
[JLC report 1](../experiments/power-r05l-charge-interlock/evidence/jlc-check1/report.pdf) ·
[JLC report 2](../experiments/power-r05l-charge-interlock/evidence/jlc-check2/report.pdf) ·
[Published r16 review](../release/r16-current-review/review.pdf) ·
[Published r16 bundle](../release/collar-tracker-r05l-r16-review.zip)

Latest manufacturing work: [PCBA r03](../assembly/pcba-r03/README.md) and
[review ZIP](../release/collar-tracker-r05m-pcba-r03-review.zip).
Q1 is now ROHM UM6K34NTCN / C510056; live JLC stock was 828 at 09:12 UTC,
26 October 2026, unreserved. Native geometry and nets are byte-equivalent after
reversing the MPN/datasheet substitutions. Q1 supplier angle is 270 degrees;
the earlier 13 corrections and U.FL model-origin offsets remain unchanged.
Actual supplier BOM/CPL downloads match the local bytes. All 81 references,
44 exact MPNs, sides, centres and angles match; both previews were inspected.

**PCBA order readiness is NO.** The first actual SMT run has unresolved pin-edge,
paste-overlap and board-edge findings. [Disposition and coverage limits](../assembly/pcba-r03/smt-disposition.md)
retain the non-passing report; several categories were truncated at 50 results.
J6 body spacing appears in backend results, but its visual model and explicit pin
coverage remain incomplete. The native eight-land/manufacturer review still holds.
The [r04 datum experiment](../assembly/pcba-r04/README.md) rejected removal of the
U.FL origin correction: minimum overlap fell from 61.78% to 4.05%, four extra
ground-overlap warnings appeared, and J2 gained a lead-to-hole finding. Keep the
r03 CPL. All 81 diagnostic placements were verified; native source/rules stayed
unchanged. Combining the unchanged IC findings resolves the returned left/outer
coverage to 57/57 and 23/23, but 20 inner/right measurements remain unreturned.
Manufacturer comparisons support retaining the current land and split-paste
geometry; they do not establish factory process acceptance.
**Next:** complete terminal/model coverage (including J6), stencil/reflow and
board-edge handling acceptance for the exact assembly. These are supplier model
and process gates; another unmodified local check is not evidence of acceptance.
Preserve all frozen revisions; do not repeat unchanged PCB DFM or restart
firmware. The user-requested mount study above is a separate mechanical task.
Supplier messaging is set aside at the user's request.
No message, order, payment or powered test was made. The old supplier-r01 enquiry
is now historical and must not be sent unchanged with its superseded Q1 questions.

Latest firmware: [tracker r03 prototype](../firmware/tracker-r03/README.md) adds
P-256 signed boot and a bounded trial to r02's GNSS/LTE-M, persistent outbox,
authenticated uploads, DNS deadline and watchdog recovery. The real target build,
embedded-key signature inspection, six trial scenarios and nine image/key negative
controls pass. A trial needs a fresh persisted fix and upload ACK within 600 seconds.
Hardware boot, swap/revert, modem DNS and power behavior are untested. The separate
[local reference receiver](../firmware/receiver/README.md) commits idempotent records
before acknowledging them. Default configuration has no host, identity or keys;
it only collects offline records. This is not a shipping firmware release.
Deferred software work is offset-aware staging/delivery, production key custody/
provisioning and an explicit r02 factory/SWD migration. That software work remains
deferred. Swap-offset images start at `0x81000`; the pinned NCS FOTA target writes
at the slot base and cannot be connected unchanged. Only a local development
signing key exists; no credentials or endpoint are configured. The receiver is
not deployed. Preserve factory/r01/r02/r03 and the unchanged PCB/Gerber/r19 assembly.

Latest assembly: [r19 charge-wire support and forming nests](../assembly/internal-charge-r03/README.md)
and [two-page drawing](../assembly/internal-charge-r03/restraint-sheet.pdf).
Three insulating staking volumes and two separate bench tools are defined. All
27 static poses pass 52 added checks; the closest added component gap is 0.22mm.
Six regressions pass. Physical adhesion, springback, installation and continuous
motion remain open; the imposed captured-curve change reaches 0.426mm at the
black PCB lead. This is prototype geometry, not a qualified restraint or release.
Continue with those actual attachments and the existing r18 routes. The published
r16 bundle remains preserved; the r19 drawing is a separate current addendum.

Latest battery work: [CT-BAT-001-A request sheet](../assembly/pack-r03/request-sheet.pdf),
[unsent supplier enquiry](../assembly/pack-r03/supplier-request.txt), and
[r09 requested-pack fit study](../mechanical/swim-r09-pack-request/README.md).
This study is not an approved battery substitution. Supplier-message authorization
has been requested separately; no response or sending authorization is recorded yet.

Preserved battery-retention work: [r12 battery-retention prototype](../mechanical/swim-r12-pack-retention/README.md)
and its [dimensioned drawing](../mechanical/swim-r12-pack-retention/pack-retention-sheet.pdf).
The shell now has a cradle and the removable PCB carrier has a retaining cap.
The requested pack sits on the existing floor, 0.3mm below the r09 visualization;
external dimensions, PCB, seals and antenna geometry are unchanged.
These are conditional dimensional results, not pack or physical qualification.

Preserved mechanical work: [r13 charging dock](../mechanical/swim-r13-charge-dock/README.md),
[dimensioned drawing](../mechanical/swim-r13-charge-dock/dock-sheet.pdf), and
[controlled external harness](../assembly/charge-harness-r01/README.md).
The dock now has actual spring-contact envelopes, captured flange shoulders,
a fuse/wire compartment and a jacket-retention bay. Its aligned reverse-key
screen includes unloaded pin movement. The external collar key projects 4.0mm;
PCB, shell cavity, pack, seals and boot are unchanged. This is a conditional
geometry prototype, with holding force and electrical/process qualification open.

Preserved work: [r14 wire-movement study](../mechanical/swim-r14-wire-motion/README.md)
and [drawing](../mechanical/swim-r14-wire-motion/wire-motion-sheet.pdf).
Constant-length pigtails cover the conservative 2.1421mm contact movement with
0.3858mm minimum slack and a 8.6961mm continuous bend-radius lower bound.
The full interval envelope clears the new housing; the old housing fails.
Only the external dry dock grows, to 94 x 36 x 16mm. The wearable is unchanged.
r14 assumed controlled end planes and loop shape without implementing a clamp.
Its preserved calculation remains conditional on those positions and shapes.

Latest work: [r15 wire clamp and assembly fixture](../mechanical/swim-r15-wire-clamp/README.md)
and [drawing](../mechanical/swim-r15-wire-clamp/wire-clamp-sheet.pdf).
The dock now has a separate cap, two closing stops and four silicone pads at the
fixed wire ends, plus a separate factory forming fixture. The external dry dock
grows to 101.5 x 36 x 16mm; wearable/PCB/seals are unchanged. Physical grip,
pad creep, insulation condition and cyclic motion are still unqualified.
The 1.93mm hard gap and assigned service bounds give 5.50..43.52% local pad
displacement; this is a geometry screen, not a friction or retention result.

Preserved work: [r16 contact rear retention](../mechanical/swim-r16-contact-retention/README.md)
and [review sheet](../mechanical/swim-r16-contact-retention/contact-retention-sheet.pdf).
Two custom terminal plates now provide defined rear bearing around the contact
bores. Two internal pockets and shorter stems/longer rear threads accommodate
that stack. Outside size, contact positions, seal glands and PCB are unchanged.
26 geometric checks, four closed meshes, four CAD controls and eight regressions
pass. This closes the missing rear-bearing geometry only; load, torque, resistance,
plating and physical ingress remain unqualified.

**r18 passes all 27 static poses with expanded charge-wire envelopes; complete harness assembly is still HOLD.**
The [r18 correction](../mechanical/swim-r18-charge-clearance/README.md) fixes an
omission in r17: charge wires had been checked against nominal components and
retention, while RF used thermal/movement envelopes. The old geometry fails the
expanded charge screen at all 27 poses. Its saved 27/27 result establishes only
the earlier, narrower calculation.

Two top reliefs in the retainer and revised GNSS/charge routes resolve those
screens. The reliefs retain a 0.5mm lower bridge and preserve all capture tabs
and radial keys. The unchanged lid guides, PCB, enclosure size and numerical
wire-length targets are retained. Each pose now has 53 charge and 29 RF checks;
the 0.2mm gap and 6.604mm charge-wire bend limits are unchanged. Four closed
meshes, five CAD controls and seven regressions pass. The nominal wire/joint
assembly and changed GNSS witness clear the actual parts.

Source: `mechanical/swim-r18-charge-clearance/routing.json` and
`retainer-reliefs.json`. r19 adds the charge-wire support and forming nests;
next validate continuous/installation/service behavior with those attachments. The remaining
bridge needs physical strength/creep acceptance. A numerical fixed length is
not a production cutting tolerance. The old r02 18/27 and r17 27/27 results and
the published r16 ZIP remain preserved historical evidence, not complete
thermal or physical harness acceptance.

The first [factory observation firmware](../firmware/README.md) now builds for the
actual r05l nRF9151 board. It delays external I/O by 1s, reports accelerometer,
gauge and charger inputs over RTT, and leaves the modem uninitialized. The native
pin contract and 14 compile-time conditions pass; deliberate wrong-pin/early-I2C
changes fail compilation. Flash/RAM use is 46,872/8,256 bytes. No board has been
flashed. The new tracker prototype implements the first LTE/GNSS/uplink/storage
flow; shipping firmware, provisioning, updates and physical tests remain open.

| Check | Current result |
|---|---|
| Tracker r02 recovery | Custom NS/TF-M build passes; 5 host scenarios, 30 ordered DNS races and 4 image/configuration controls pass; no flashing, actual modem test or observed watchdog reset |
| Preserved tracker r01 | GNSS/outbox/mTLS prototype; 7 local receiver tests, 6 simulated mutation failures, 40 corrupted record bytes and 2 image controls pass; no powered test |
| Factory observation firmware | Actual custom-board build passed; two negative compile controls passed; no flashing or powered test |
| Integrated cable routes r18 | 27/27 static poses; 82 checks per pose including expanded charge envelopes; retainer reliefs and GNSS/charge routes revised; continuous movement and physical qualification open |
| Internal charge support r19 | Three staking regions and two forming nests; 27/27 static poses and 52 added checks per pose; adhesion, released shape, installation and continuous movement unqualified |
| Internal harness r02 | Both nominal routes and joints fit; continuous radius bounds 7.438/6.905mm; 18/27 searched static poses pass; upper-pose RF/bend interference and restraint still HOLD |
| Contact retention r16 | Two custom rear terminals; defined lateral bearing, four meshes and CAD controls; internal harness still HOLD |
| Board | 40 × 32mm; six Cu layers; 87 footprints |
| Assembly candidates | 81 fitted references / 44 exact MPNs; BOM/CPL exported |
| Actual JLC assembly review | 44/44 MPNs and all 81 placements verified; Q1 now ROHM; actual SMT findings and J6 complete model/pin acceptance remain open |
| Native DRC / ERC / opens / parity | Zero findings |
| Charge circuit | Two VSYS-powered TLV3012B comparators and SN74LVC1G00 NAND drive /CE independently of MCU/VIO |
| Temperature model | Conditional pass; nominal 6.29–36.21°C sensor window; original 50°C case disabled |
| Original source preservation | 71 footprints/lands, 27 RF segments, stack, rules and keepouts unchanged; only U3.4 original pin changes net |
| Local routing | New charge nets and supply/sensor branches; local VIN escape rerouted |
| Ground / returns | 109 physical GND pads have local via paths; 122 GND vias; two dedicated planes; 154/154 signal-via return screens |
| JLC PCB DFM | Records `637366592129687553` / `637366801595977730`; same ZIP/rules; 29 rows; SMT off |
| Preserved mechanical r08 | 85 populated envelopes pass four thickness cases; eight closed meshes; current CAD intersections empty, old carrier and undersized cable guides rejected |
| Requested-pack study r09 | Same PCB; requested pack/NTC envelope fits with a 0.4mm height increase; no supplier pack approval |
| Captive-PCB prototype r10 | 85 swept component envelopes, 27 cable poses, four tab contacts and nine closed meshes; current CAD intersections empty and reversed key rejected |
| Thermal-fit prototype r11 | 85 swept envelopes; 27 cable poses; nine closed meshes; four radial keys; conditional -10 to +45°C screen with independently varying part temperatures |
| Charging-dock prototype r13 | 29 analytical checks, three closed meshes, six CAD controls and seven regressions; actual harness candidates |
| Dock-wire prototype r14 | 42 analytical checks, two closed meshes, six CAD controls and twelve regressions; continuous constant-length wire-family bound |
| Wire-clamp prototype r15 | Separate cap, four silicone pads and factory fixture; saved geometry and regression evidence; physical restraint remains unqualified |
| Pack-retention prototype r12 | 85 component envelopes plus raised pack/NTC checks; two changed closed meshes; seven CAD controls; seven regressions |
| Antenna candidates | Synzen CAPH SZK-C-3L30 LTE and ZETA SZK-C-0G04 GNSS; separate nominal 100mm cable assemblies and four internal lid guides |

PCB SHA256: `241c84d6ba98793c37344e1e46ddc4918e7b05322ba87daea7c9a90ffb8379b3`.
Gerber SHA256: `c736c5d35ddfe4c4662e57606120f00f7358492e11d5fbb32eaf1d0ff6caf5d2`.
Stack candidate: JLC06081H-7628, nominal 0.8mm class, explicit CAD thickness 0.84088mm.
In1/In4 are dedicated GND planes; F/In2/In3/B carry signals.

Read the [r05l evidence](../experiments/power-r05l-charge-interlock/README.md),
[charge review](../assembly/charge-interlock-r01/README.md) and
[r08 antenna enclosure](../mechanical/swim-r08-antennas/README.md).
The first supplier run failed 3 Danger / 4 Warning; full-size label moves and a
VIN-via relocation fixed them without weakening rules or shrinking lands.
The final ZIP passed two fresh analyses. Preserve those exact bytes.

The [r05k battery finding](../assembly/pack-charge-r01/README.md) remains historical
evidence: that source grounded /CE and permitted 50°C charging with a direct
10k/B3435 sensor. The new source implements the interlock. SEMITEC 103JT-025 is a
candidate sensor; no protected pack or factory cell attachment is selected.
The reviewed EEMB PCM supports 350mA continuous despite its 700mA bare-cell rating.

**Next:** obtain a controlled supplier response to [CT-BAT-001-A](../assembly/pack-r03/README.md)
before selecting a complete protected pack. The requested body is 32 x 30.5 x 5.3mm,
including PCM, insulation and service swelling; the supplier must confirm this bound.
The request asks for 600mA continuous as engineering headroom, not a Nordic requirement.
Nordic's typical TX tables average a 1ms TX subframe and explicitly exclude higher
microsecond peaks; neither those averages nor a reporting interval prove the load.
The old EEMB 350mA PCM is still unapproved. The Jauch and VARTA alternatives and their
specific charge/size constraints are recorded; do not restart an open-ended catalogue
search or silently promote the request into a supplier specification.

The r09 study includes a flat NTC and bond/cover budgets in a 33 x 31.5 x 6.2mm
assembly envelope. Board/antennas/cables and shell height increase by 0.4mm;
rigid size is 57.4 x 49.4 x 21.0mm, boot 60.4 x 52.4 x 25.8mm. Contact/seal geometry
and the r05l PCB are unchanged. The original board height fails the wider-pack
clearance control. No supplier part, wire route, adhesive strength or physical
thermal result is approved by this fit calculation.

**Next independent local step:** close the remaining charging interface: positive
dock retention or measured magnetic holding, continuous internal J3 wire motion and qualified r19 support,
crimp/splice/insulation process and source/fault-current behavior. The r13
USB cable/fuse/contact selection is a prototype definition, not a qualified power
path. r15 implements a clamp and assembly fixture, but endpoint slip, pad creep,
forming accuracy and cyclic flex require physical acceptance. Midstroke pair
force can be 1.569N; force at the largest tolerance stroke and
magnetic holding through the walls are not yet established. Pack lead exit and
supplier approval remain open; the enquiry is still unsent. Then implement firmware
and factory tests. Do not repeat unchanged-byte PCB DFM or call the device ready.

r12 adds a 33 x 31.5mm cradle opening and a 0.75mm cap with component reliefs and
a central NTC opening. Its minimum complete-pack requirement is 30.5 x 29 x 4.8mm;
this is not a supplier-confirmed part. New-solid/component gap is at least 0.225mm,
raised-NTC/component gap 0.223mm and the four guaranteed capture regions each have
at least 1.429mm² overlap. The lifted-sensor calculation uses the common carrier
datum, independent component temperature and a 0.10mm total feature-error chain.
Two changed meshes and seven CAD controls pass; seven unchanged r11 meshes are
reused by hash. Pack/PCB tilt, pouch contact pressure/abrasion, cap strength/creep,
lead routing, thermal attachment and physical ingress remain unqualified.

r11 preserves the PCB and outside size. Under the declared CTE bounds, the r10
comparison shows calculated guide and closing-stack interference. r11 widens the
cavity and guides, uses a PC retainer candidate with four radial carrier keys,
opens the SIM lane, enlarges component reliefs and adjusts the antenna paths.
The custom contact stem is shortened 0.20mm to match the wider cavity; its seal
land and thread are unchanged. No previously released CAD file is overwritten.

At the assigned bounds, minimum component gap is 0.205mm, tab overlap 0.162mm²,
and closing clearance 0.058mm. The sampled cable/component minimum is 0.235mm;
cable shape search changes initial tangent length and plug azimuth by up to 30°.
These sampled shapes do not establish permissible connector force/rotation,
continuous cable flex or physical thermal behavior. Guide rotation allocation,
board tilt/load, moisture, creep and actual material/process capability remain
unqualified. The selected PC and PCB CTE intervals are engineering requirements,
not guaranteed datasheet limits. All previous r10 evidence remains preserved.

Charge bounds depend on sensor R/T and full-temperature leakage assumptions and a
2°C cell-to-sensor allocation including lag. Startup, brownout, low-cell recovery,
sensor-insertion transients, actual current and thermal coupling require assembled
measurements. The prior component-selection model still requires a provisional
1s firmware VIO wait; 600ms fails that model. Review the
[sequencing exception](power-sequence-followup.md) before adding hardware.
Supplier procurement, CPL rotations, SMT/reflow, actual stack/impedance and RF
qualification remain open. A conditional calculation is not an electrical release.

IP68 swimming/dust resistance is the design target; 2m fresh water / 60 minutes
and magnetic charging remain engineering assumptions. The preserved r08 retains the r07 U12
carrier relief and shifts neither the PCB nor the contact/seal geometry. The taller
shell accommodates the two cable layers: rigid envelope 57.4 × 49.4 × 20.6mm,
excluding the 1.3mm docking key; boot 60.4 × 52.4 × 25.4mm. A 20mm M2 screw
candidate and blind boot pockets replace the former length assumption. Exact
fastener tolerance, torque, clip strength and lid-opening motion are unqualified.
Its battery remains a 34 × 23.5 × 5.8mm reservation; the antennas have sourced
candidate dimensions with explicitly provisional cable/placement allowances.
No physical water/dust, powered or RF result exists. This is not yet a complete
working-PCBA order package.

## Preserved tested PCB

Source: `experiments/paul-nanosim-r04i-sim-access-40x32/hardware/`.
PCB SHA256: `f4be0288708733aaa6092a703ffa1bfebb3dc059fd21112a8cfed94028acc3b0`.
Final ZIP: `experiments/paul-nanosim-r04i-sim-access-40x32/evidence/collar-tracker-04i-final-40x32-dfm.zip`.
ZIP SHA256: `6304b66623a473e4c5405c6db7181b3f1879fa93088f9812802d43e814f90898`.

| Check | Result |
|---|---|
| Outline / layers | 40 × 32 mm; four copper layers; 55 footprints |
| Native DRC/ERC/parity | Zero violations, warnings, opens or schematic mismatches |
| Ground | All 82 GND pads have local track paths to vias; 91 GND vias join both continuous inner planes |
| Return screen | All 93 non-GND vias within the inherited 2 mm screen; no inner-layer tracks |
| RF identity | All 24 baseline RF segments retained; impedance/body performance still unqualified |
| SIM access | All 19 other bottom-side bodies/lands clear the projected card lane, including 0.20 mm lateral margin |
| SIM topology | All four connector paths pass through their clamp land; no same-net copper bypass |
| JLC PCB DFM | Records `637245503244296194` and `637247002053398530`; 29 analyzed rows and 442 green measurements each |
| JLC rules | Unchanged SHA256 `f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`; SMT off |

D1/C10 moved beside the card lane; D1 CLK/RST channels were exchanged in both
schematic and PCB. R12 moved to open a short protected reset crossing. The unused
old clock branch was removed. R12's two copper attachments are both 0.2 mm.
The first supplier run found 5 Danger / 2 Warning at the SIM legend; moving that
legend 1.476 mm resolved them. The failed package/report is preserved separately.
A later browser attempt never uploaded a file and is not counted as an analysis.
The helper now detects that condition instead of returning apparent success.

All final evidence is indexed in the trial's `evidence/routing-checkpoint.json`.
Preserve the tested bytes. Any later PCB change needs a new package and fresh checks.

## Electrical and connectivity review

The [power review](../evidence/power-review-r04i/README.md) compares 148 unique
power-related pins between a fresh native schematic export and the saved PCB.
It reproduces three open findings: no guaranteed modem undervoltage margin,
uncontrolled GPIO supply sequencing, and a battery-divider feed path when GPIO
power is absent. The calculations are illustrative; no powered failure or repair
is claimed. Nominal charger settings are 4.2 V / 500 mA input / 100 mA charging.

`python3 scripts/audit_power_architecture.py` reproduces the evidence and returns
exit code 2 for electrical HOLD. Standard handoff verification checks this report
as well as the unchanged PCB/mechanical artifacts; its evidence PASS is not
electrical acceptance. The tested Gerber and mechanical bundle remain unchanged.

The [Türkiye connectivity review](turkiye-connectivity.md) identifies manufacturer
Vodafone certification coverage and a firsthand local-SIM connection report.
Neither establishes this collar's activated service or moving-device performance.
Keep nRF9151 as the prototype candidate; verify a local subscription and both
radio modes on a development kit before production antenna/pack release.

## Preserved mechanical baselines

The user selected swimming / an IP68 design target. The provisional condition is
2 m fresh water for 60 minutes; depth/time and magnetic charging remain engineering
assumptions pending the user's preference replies.

`mechanical/swim-r02-fit/` is the preserved r04i populated-board fit revision. It retains
the shell, lid, lift-out carrier, independently sealed charging targets, magnet
plugs, dock alignment shell and required TPU boot. Rigid size remains
57.4 × 49.4 × 17.6 mm, 58.7 mm including the key; boot 60.4 × 52.4 × 22.4 mm.

The actual native placements now have 49 drawing-derived component-height
envelopes, two factory wire-termination requirements and two bare test-pad areas;
C11/C12 remain DNP. Maximum height including solder/warp allowances is 2.75 mm
above and 1.75 mm below the board. All 53 entries pass the declared fit screen;
the narrowest component gap is C10 to the carrier, 0.24 mm against a 0.20 mm target.
These are dimensional screens, not component or PCBA purchasing approval.

D1's tolerance envelope required a local carrier relief. The original M4 backing
hardware envelope failed floor/board clearance; r02 uses a dimensional M3 thin-nut
candidate, a 3.5 mm M3 × 0.5 contact thread and Z=5.5 mm contact centers. Two shallow
carrier reliefs clear the backing stack while retaining 1 mm connecting bridges.
The terminal/washer stack is still a constrained reservation, not a selected harness.

Six regressions pass, including the original interference cases and an oversized
J4 wire termination. An independent CAD boolean is empty for the revised geometry
and nonempty when the original carrier is restored. All eight exported meshes
are closed, oriented and connected; four previews and both review sheets were
inspected. The 30 inherited shell/seal checks also pass. r01 and its bundle remain
byte-preserved.

This is a **prototype, not a completed production design**. The
[selection review](../mechanical/swim-r02-fit/selection-review.md) explains why the
researched protected packs and antennas are not yet released: size alone does not
prove modem pulse capability or RF performance. The 30 × 5 mm antenna rectangles
still represent reservations. Dock electronics, harness routing/strain relief,
positive PCB retention, material/seal grades, actual lid fasteners and torque remain
open. No physical ingress, powered or RF result exists.

The preserved `mechanical/swim-r06-six-layer-fit/` uses the r05h PCB and
nominal 0.8 mm thickness. All 69 populated envelopes and 30 shell checks pass;
the smallest checked gap is C10/carrier at 0.24 mm. Nine resistor-height limits
remain component requirements in that snapshot. The r05k fit profile replaces them
with sourced heights and also checks the larger C25; its 69 envelopes pass. Actual supplier stack/thickness tolerances,
positive retention and physical tests remain open. The inspected preview is a
conservative volume model; r02 mesh acceptance does not transfer automatically.
