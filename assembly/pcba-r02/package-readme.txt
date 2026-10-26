COLLAR TRACKER — r05l / PCBA r02 ASSEMBLY REVIEW

REVIEW ONLY — NOT AN ORDER OR PRODUCTION PROGRAMMING RELEASE

Start with assembly/pcba-r02/README.md.

Current files for this dated JLC model review:
  BOM: assembly/pcba-r01/bom.csv (unchanged)
  CPL: assembly/pcba-r02/cpl-jlc-review.csv
  Pin/centre reference: assembly/pcba-r02/placement-reference.pdf
  Delivery scope: docs/pcba-delivery.md
  Gerber: experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip

The native CPL at assembly/pcba-r01/cpl.csv preserves actual physical centres
and native angles. The older r01 supplier CPL is retained as historical evidence.
Do not use all CPL files together or apply the JLC model offset to native CAD.

J1/J2's r02 X correction is specific to the inspected JLC library origin.
The factory must confirm its placement datum before generating machine programs.
No actual PCB component centre, copper, Gerber or BOM part was changed.

Q1 DMN62D2UDW-7 remains mandatory and unmatched. The DMN62D0UDW-7 candidate
has not been selected or approved. J6 has no usable supplier model. The actual
80-reference preview is incomplete and has not passed complete SMT analysis.

Battery/NTC approval, factory harness assembly, programming/provisioning,
powered/RF testing and whole-device ingress qualification remain open.
Two clean PCB DFM reports do not establish a working-device release.
No supplier message, order or payment has been made.
