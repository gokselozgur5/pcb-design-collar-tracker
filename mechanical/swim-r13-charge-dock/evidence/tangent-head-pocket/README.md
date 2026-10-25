# Rejected tangent pocket

The 9mm head pocket touched the nose floor at one line. CGAL reported
Simple: no, even though the exported STL passed the edge-count inspector.
A local 1.2mm-wide lower relief opens that contact instead of leaving a
zero-thickness tangent. The corrected probe reports Simple: yes. The final
exporter also rejects CGAL manifold warnings; STL topology alone is insufficient.
