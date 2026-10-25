# Rejected assembly frame

The first intersection contained 94.7644mm³ because the imported boot STL was
in its print frame (Z=0..25.8), rather than the assembly frame (Z=-4..21.8).
The corrected assembly applies the source exporter's -4mm translation.
This was a screening setup error, not evidence that the physical r12 boot
needed changing. The failed source and intersection are preserved here.
