# Working delivery without user soldering

Requirement recorded 2026-10-24: the owner wants a working device from the supplier,
without manual soldering where possible. This is the design/procurement target.
0.3.4 passed two JLC PCB DFM runs with 0 Danger / 0 Warning, but is not a production
ready product. See [order readiness](order-readiness-0.3.4.md) and
[the DFM fix](clearance-revision-0.3.4.md). Paul's return-via/two-inner-GND approach
was not completed on 0.3.4; subsequent work is tracked in [STATUS](STATUS.md).

| Delivery condition | Baseline status | Required work |
|---|---|---|
| All board parts factory assembled | 46 physical parts; 30 missing exact MPNs | Exact BOM, sourcing, CPL/orientation and double-sided assembly |
| Battery/charging connection ready | J3/J4 bare PCB contacts; cell/NTC open | Compatible protected cell and connection; factory wiring/assembly or a plug-in connection |
| Working cellular SIM | Baseline J6 only provides contacts; r04 adds nano-SIM, eSIM deferred | Actual SIM/service/operator selection, Turkish use and factory test |
| GNSS/LTE antennas fitted | J1/J2 U.FL; antennas unselected | Antenna/cable selection, RF/body testing and final-assembly responsibility |
| Firmware programmed | J7 bottom-side SWD contacts | Pogo fixture, firmware and programming/verification instructions |
| Function test passed | No powered prototype or test software | Measured acceptance limits, supplier feasibility and per-unit test records |
| Heart-rate function | J5 digital interface; no selected sensor | Sensor/contact design and reference comparison; absent from this board |
| Ready in its enclosure | Old mockup used a 30 × 22 mm PCB | 35 × 28 mm board/battery/antenna fit, assembly and sealing validation |

**PCB assembly alone does not establish a fully assembled, working product.**
Battery, antenna and enclosure assembly by the same supplier has not been confirmed.
If another assembler is needed, retain the requirement that soldering must not be
passed back to the owner. The factory's assembly process and user hand soldering
are different concerns.

[JLC's programming service](https://jlcpcb.com/help/article/pcba-programming-service)
offers post-assembly programming for Standard PCBA, subject to engineering review.
It requires the part number, interface, firmware and procedure. Support for this
nRF9151/J7 fixture is unconfirmed. Its [testing description](https://jlcpcb.com/help/article/smt-inspection-and-testing-capabilities)
describes customized powered tests against customer criteria; this is not assumed
to be included automatically or guaranteed for this design.

## Production acceptance criteria to define

1. Current-limited first power-up; rails, leakage/sleep current and loaded behavior.
   Resolve and measure UVLO and VDD_GPIO sequencing first.
2. SWD programming, image verification, serial number and boot record. J7 pins:
   VIO, SWDIO, GND, SWDCLK, DEBUG_RESET, VSYS. Fixture access still needs design.
3. Charge current/termination, NTC and cell behavior against the chosen cell's limits.
   The present 100 mA setting is a draft assumption.
4. Accelerometer communication and manufacturer self-test.
5. SIM/profile reading, network or appropriate test-system registration, and real
   transmission to a test server. Do not assume a Turkish profile works at a
   factory in China; arrange suitable test access.
6. Controlled antenna/signal/test method for GNSS fix and RF measurements. Random
   indoor acquisition attempts are not acceptance tests.
7. If fitted, heart-rate sensor communication plus separate on-animal measurement
   validation. Factory electronics testing does not establish clinical/contact accuracy.

Numeric limits and the fixture are unfinished. Prototype assembly/testing may be
outsourced, but the first design is not guaranteed to need no revision. The order's
concrete delivery terms must prevent failed boards being sent to the owner as repair work.

The last two supplier reports cover 0.3.4, dated 2026-10-25 06:39:36 and 06:41:25:
0 Danger / 0 Warning, PCB DFM only, no SMT analysis. ZIP identity and reports are in
`release/collar-tracker-0.3.4-verification.json`. All 268 pads are mask-exposed.
U1 stencil, U2's JLC-adapted mask and U5's 0.010 mm narrowed lands still need
assembly qualification. DFM files were uploaded; no order, payment or supplier
message has been made.
