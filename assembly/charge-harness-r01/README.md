# Charging harness candidate

This defines the external dock circuit and component envelopes. It is not a
working-device release. The internal contact lugs, J3 wire route and pack lead
exit are still unresolved. No supplier enquiry, purchase or physical test was made.

## Wiring

| From | Through | To |
|---|---|---|
| Tensility 10-03388 USB-A pin 1, red | F1, Littelfuse 0251.750MXL; red 26 AWG pigtail | Dock pin at Y=-6; collar contact to J3.1 `/VIN_5V` |
| USB-A pin 4, black | Black 26 AWG pigtail | Dock pin at Y=+6; collar contact to J3.2 `/GND` |
| USB-A pins 2/3, white/green | Individually insulated, no connection | No data or enumeration |
| USB shell/drain | Insulated separately | No connection to charging contacts |

Coordinates are the enclosure coordinates, not an arbitrary front-facing view.
The native netlist and exported pad geometry establish J3.1 at case
(-16.75,-12.20), J3.2 at (-14.25,-12.20), on the top PCB surface.
Do not infer a left/right connection from a mirrored bottom-view picture.

J4 remains red `/VBAT`, black protected-pack `/GND`, white `/BAT_NTC` on
pins 1/2/3. Never bypass the pack protection to obtain the NTC return.

## Factory assembly requirements

- Two Mill-Max **0962-0-15-20-75-14-11-0** wire-mount spring contacts, captured
  between the dock halves. This is not a press-fit qualification.
- Alpha Wire **2843/7**, red and black, 26 AWG stranded PTFE pigtails. The
  source gives a 0.8382mm maximum insulation diameter and a 10-diameter bend
  requirement. Do not substitute solid 2842/1. Conductor dimensions alone do
  not qualify a crimp; tooling, strip/insertion length and pull acceptance need
  Mill-Max's process approval and factory trials. Never crimp solder-tinned wire.
- F1 is a **0.75A fuse**, not a 0.5A electronic current limiter. Its 1.5A
  opening limit is 1s under the manufacturer's test conditions. The source may
  limit below that current, in which case the fuse is not guaranteed to open.
  Normal current, fault current, temperature derating and voltage drop need
  assembled measurements. The 0.175ohm cold resistance is nominal.
- Keep the fuse and all three splices insulated. The CAD allocates a maximum
  4mm fuse sleeve diameter, 7.5mm body length and three 4 x 2.4mm splice
  envelopes. These are incoming assembly limits, not guaranteed tubing sizes.
  Exact sleeve/termination process selection remains open. The 251 fuse is not
  recommended for IR/convection reflow. Agree an automated factory joining
  process; no end-user soldering or rework is intended.
- The USB cable's original 25±5mm fanout and 5±2mm tinned ends are not accepted
  automatically. Prepare leads to the checked path, including straight splice
  overlap, without nicked strands. The nominal centerline from X=34 to 52 is
  a smooth 18mm splay; the continuous bend-radius lower bound is 10.370mm.
  The 1.2mm individual-lead diameter and 10mm radius are engineering receiving
  requirements; the cable drawing does not guarantee those individual-lead limits.
  The tail screen allows ±0.28mm jacket-center movement on its saddle.
  The drawn pigtails are nominal rear-seated paths; slack for the full unloaded
  pin movement and subsequent reseating has not been qualified. Do not cut a
  production harness to these centerlines without that movement check.
- Reserve the center of the jacket retention bay for the cable. Use a
  HellermannTyton **T18R, 111-01980** tie through the two floor slots, with
  its head beside the cable. The manufacturer's 80N tie tensile rating does
  not establish this assembly's pull-out strength. Qualify installation tension,
  jacket damage, head clearance, pull and repeated flex before release.
- Four M2 x 16 screws and captive M2 nuts close the dry indoor dock. The
  model provides 2.3mm holes and 4.3mm across-flat nut pockets. Exact hardware
  drawings, torque and retention remain unqualified.

## Power and use limits

Use a dedicated regulated 5V SELV supply with documented short-circuit protection.
A generic computer USB port is not approved: this circuit does not enumerate or
negotiate current. The 500mA design load is not a measured charge-current result.
USB input resistance, source tolerance, transient behavior and charger undervoltage
must be checked together. Do not claim the complete path is rated from wire voltage
rating, a typical spring-current curve or a fuse marking.

The dock is a **dry indoor prototype**. The collar must be dry before connection;
no claim covers charging in water or mud. The collar's existing seals are unchanged.
The current 3 x 1mm magnet candidates have no demonstrated holding force through
their plastic walls. At midstroke the two selected springs can require 1.569N;
their force at the maximum tolerance stroke is not bounded by that number.
Positive dock retention or measured magnet selection is the next mechanical gate.

## Factory acceptance still required

Verify continuity/polarity against the native netlist before applying power.
Measure resistance through both complete paths and insulation between them;
exercise the keyed interface in correct, reversed and skewed approaches.
Check voltage/current/temperature at minimum input and maximum intended load,
shorted and contaminated contacts, separating contacts, and a disconnected pack.
Qualify crimp/splice retention and cable flex without transmitting pull to the pins.
Record actual results; this document is a procedure, not a test certificate.

Sources and inspected revisions are in [sources.json](sources.json).
The dimensioned model and controls are in
[r13](../../mechanical/swim-r13-charge-dock/README.md).
