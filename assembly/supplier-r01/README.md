# PCBA engineering enquiry — prepared, not sent

The [English draft](request.txt) asks JLCPCB to confirm sourcing, placement and
factory capabilities before any prototype order.

Recipient: JLCPCB PCBA Engineering, through its [official contact form](https://jlcpcb.com/help/contact).

Attach the existing [PCBA r02 review ZIP](../../release/collar-tracker-r05l-pcba-r02-review.zip):

- Filename: `collar-tracker-r05l-pcba-r02-review.zip`
- Size: 6,997,076 bytes
- SHA256: `0a56cff3d99c196ac2c967f5055e3c1eda5d70446295cf4aa8c010bb14a1b4a5`
- Contains 39 members, including `START-HERE.txt`, unchanged Gerber/native sources,
  current BOM/CPL, both PCB DFM reports, placement-reference PDF and delivery scope.
- No firmware binary, credentials, private key or browser state is attached.

The contact form inspected on 2026-10-26 permits ZIP files up to 10MB each, so
this single attachment fits its displayed limit.

The user has authorized local work, commits/pushes and JLC manufacturing uploads.
[AGENTS.md](../../AGENTS.md) explicitly excludes supplier messages and orders from
that scope; this draft must not be submitted without separate sending authorization.
The separate [battery enquiry](../pack-r03/supplier-request.txt) is also unsent;
its pending authorization is not changed by this draft.

## What the reply must resolve

| Item | Evidence supplied | Required supplier answer |
|---|---|---|
| Mandatory Q1 | Exact MPN, native pin map and unselected D0 screen | Available original or proposed alternate with traceable manufacturer, quantity/attrition and lead time; no automatic substitution |
| J6 nano-SIM | Exact no-peg MPN, D6 pin/land comparison and card-entry direction | Correct model or controlled manual placement review, including pin 1 and bottom-side orientation |
| J1/J2 and full placement | Native centres, dated model-origin correction and 80-reference preview | Machine datum, all 81 fitted references, stencil and two-sided process acceptance |
| Programming and test | nRF9151 MPN, 1.8V J7 mapping and proposed functional scope | Supported probe/fixture, image process, test scope, per-unit records and costs |
| Complete device | Harness/pack/antenna/enclosure responsibilities | Supported operations and named responsibilities for anything outside PCBA service |

The first response may request more engineering information; it cannot qualify
the battery, RF behavior, waterproofing or an unbuilt prototype.
No approved production image or purchase quantity is implied by this request.

## Checks behind the enquiry

Inspected the existing JLC Component Placements page and selected J6 on the bottom
side on 2026-10-26. It still showed a placeholder and an exact-MPN table entry.
No custom-model upload control was found in the inspected page. This is a bounded
UI observation, not proof that JLC cannot add a model through engineering support.
No Save & Close, order, message or complete SMT analysis was submitted.

[JLC's sourcing guide](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction)
describes new-part requests, global sourcing and consignment.
Its [global-sourcing procedure](https://jlcpcb.com/help/article/how-to-use-jlcpcb-global-sourcing-parts-service)
requires review and warehouse receipt before parts can be used; a public catalogue
entry does not reserve assembly stock.
The [programming service](https://jlcpcb.com/help/article/pcba-programming-service)
is subject to engineering review and Standard PCBA; its existence does not confirm
nRF9151 support or the requested whole-device tests.

The [DigiKey original-part listing](https://www.digikey.com/en/products/detail/diodes-incorporated/DMN62D2UDW-7/22158372)
said the part is not normally stocked when inspected on 2026-10-26.
The r02 JLC search found one unit of the unselected D0 candidate at 07:21 UTC.
These dated observations leave procurement open; neither is a supplier quotation.

The [onsemi NTJD4401N datasheet](https://www.onsemi.com/pdf/datasheet/ntjd4401n-d.pdf),
February 2026 revision 8, specifies maximum on-resistance at 2.5V and 4.5V gate
drive on page 2, with no guaranteed 1.8V value. It was not accepted as a direct
Q1 replacement under the existing 1.8V screening basis. Typical curves and
distributor stock do not fill that rating gap. The original BOM remains unchanged.

## Resume

After explicit authorization, submit this draft with the exact attachment and
record the supplier case ID and sent contents. Do not place an order or pay.

On a reply, reconcile each answer with the table above. Record component/model
changes in a new revision, retain the native physical-coordinate baseline, and
complete placement/SMT review before any manufacturing release. A reply permitting
assembly does not replace powered, RF or whole-assembly ingress tests.
