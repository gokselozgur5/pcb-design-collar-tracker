# Native joint-routing trial — not selected

The saved result has **17 opens**, 51 dangling-track warnings and 15 dangling-via
warnings, with no other native violations or schematic mismatches. This is worse
than the preserved r05c candidate and is not the continuation board.

1,003 noncritical trunk items were removed while preserving local exits, original
power backbones, local grounds, RF and SIM. The first two native passes connected
the enable and supply branches but left 20 other opens. A 41.816 mm VIO_ENABLE
proposal was reviewed before raising the planner's detour screen from 40 to 60 mm;
native and supplier design rules were unchanged.

Twenty-five return-only ground vias were then removed; 83 local/RF ground vias
were retained. Of the old trunk pieces, 409 cleared the new copper. Removing 174
isolated pieces in 36 groups preserved every native terminal group and left 19
opens. The final pass closed two more. Fresh geometry, power, ground, RF and SIM
reports belong to the final saved source.

Return coverage is deliberately unfinished. Restoring it is required before DFM.
The failed initial recovery stopped before saving because the native UUID field
was read-only; the corrected recovery uses `SetUuid` and a fresh source-bound plan.
The early interrupted native pass saved only its completed routes. These events
are not accepted clean runs or native crashes.

No Gerber, supplier result or electrical acceptance is claimed. The individual
receipts retain their own source hashes; only `native-drc.json` describes the final
board. r05f instead starts from r05c and preserves the working original signals.
