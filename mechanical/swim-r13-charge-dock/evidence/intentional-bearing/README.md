# Intentional jacket support contact

The harness intersection had two vertices, one edge and zero facets at the
nominal jacket/saddle bearing line. The original empty-only assertion rejected
that intentional contact. The current screen checks wires/pins/splices against
the complete shell, and the jacket against the shell excluding only its explicit
bearing saddle. Jacket diameter/position/exit are checked analytically. No
clearance threshold or PCB DFM rule was relaxed.
