# Working delivery without user soldering

The supplier must deliver assembled, programmed and function-tested units.
The owner must not be left with battery, charging or antenna soldering work.
This requirement includes the complete device and its enclosure.

The current r05l PCB is 40 x 32mm with six copper layers. Native DRC/ERC/connectivity
and two real JLC PCB DFM runs pass. Full-device release remains **HOLD**.
See [STATUS](STATUS.md) and the [current PCBA review](../assembly/pcba-r02/README.md).

| Delivery condition | Current evidence | Remaining work |
|---|---|---|
| All board parts assembled | 81 fitted references / 44 exact MPNs; JLC matched 43 MPNs | Source mandatory Q1; approve all placements and SMT/stencil/reflow |
| Correct component orientation | 13 angle corrections and J1/J2 model-origin correction verified in actual preview; connector/Q1 manufacturer lands checked | J6 model, complete preview/SMT acceptance and factory placement-datum confirmation |
| Battery and charging ready | J3/J4 coordinates, hardware interlock, pack request and r19 wire support | Approved protected pack/NTC, factory harness attachments and powered charge tests |
| Working cellular SIM | Fitted physical nano-SIM socket; eSIM deferred | SIM/operator/service and real network qualification for Türkiye |
| Antennas fitted | CAPH LTE and ZETA GNSS candidates, r18 routes and four lid guides | Cable tolerances, assembly, continuity and RF/body tests |
| Firmware programmed | Factory observation and development-signed tracker r03 builds; J7 coordinates | Approved production image, provisioning, fixture and actual flash/verify/boot |
| Function test passed | Host checks and target builds; no powered prototype | Physical rail/current/charging/sensor/modem/GNSS tests and per-unit records |
| Heart rate | J5 digital expansion contacts only | Sensor/contact design and validation; not implemented |
| Swimming enclosure | Retention, dock and thermal-fit prototypes; IP68 target | Material/process approval, assembly validation and whole-device ingress tests |

The requested battery is not an approved supplier part. Its enquiry is prepared
but unsent. No order, payment, supplier communication or production programming
approval is implied by these files.

## Factory handoff

Use [bom.csv](../assembly/pcba-r01/bom.csv) and
[cpl-jlc-review.csv](../assembly/pcba-r02/cpl-jlc-review.csv) for review with the
unchanged r05l Gerber ZIP. The native-angle/physical-centre baseline is retained
separately. The r02 J1/J2 offset belongs to the dated JLC model; the factory must
confirm its placement datum before machine programming. The board did not move.
Q1 must remain fitted: the current 80-part preview excludes it and cannot establish
complete SMT acceptance. Exact library matching does not prove stock or model
accuracy. Resolve model disagreements against the manufacturer's drawing and
native copper before placement approval.

The [placement-reference drawing](../assembly/pcba-r02/placement-reference.pdf)
gives connector/Q1 physical centres and pin functions. The alternative Q1 screen
does not authorize a BOM substitution; it remains an unselected candidate.

The [interface table](../assembly/pcba-r01/interface-pads.csv) contains all 23 bare
interface lands. J7 is VIO_1V8, SWDIO, GND, SWDCLK, DEBUG_RESET and VSYS on pins
1 through 6. Use the actual 1.8V logic reference and the required external-I/O
startup sequence. Contact force/access, power and ESD handling need qualification;
coordinates alone do not make a working fixture.

[JLC's programming service](https://jlcpcb.com/help/article/pcba-programming-service)
is subject to engineering review. Confirm nRF9151 support, interface/fixture,
image format and verification procedure. Its
[testing description](https://jlcpcb.com/help/article/smt-inspection-and-testing-capabilities)
does not establish that battery wiring, enclosure assembly or the requested
powered tests are included for this board. Confirm responsibility for each
operation before ordering.

## First-prototype powered acceptance

1. Current-limited first power-up, rails and VDD_GPIO startup/low-cell recovery.
2. SWD flash/verify, boot identity, serial/provisioning record and failure recovery.
3. Charge current, termination, sensor open/short/hot/cold and pack protection
   against the approved complete-pack specification. Design settings are
   4.2V / 100mA charging and a 500mA input limit; actual behavior is unmeasured.
4. Accelerometer/fuel-gauge communication and relevant device self-tests.
5. SIM detection, registration and authenticated upload/ACK using suitable factory
   service. A Turkish SIM cannot be assumed to work at the factory.
6. Controlled GNSS/RF conditions and measured active/sleep current; random indoor
   acquisition attempts are not acceptance criteria.
7. Whole-assembly tests using the agreed immersion and dust conditions.

Numeric pass/fail limits, approved hardware, fixture feasibility and actual
factory records remain open. PCB DFM, SMT review and full-device functional
acceptance are separate claims.
