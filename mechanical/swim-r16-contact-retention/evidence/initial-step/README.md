# Rejected first terminal mesh

The positive terminal passed the CAD `Simple: yes` diagnostic but failed the
actual binary-STL topology check: three bad edges and two collapsed faces at
the unchanged 0.00001mm inspection grid. Two vertices at the slanted tail's
9.25mm thickness transition differed by approximately 0.000003mm.

The original source and rejected mesh are preserved here. The final source
cuts the thickness step from one full blank, instead of uniting two overlapping
cut extrusions. It preserves the intended dimensions and inspection threshold.
This directory is evidence, not an alternative manufacturing part.
