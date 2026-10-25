# Joint Freerouting trial — not selected

This starts from r05c. Splitting long traces preserved all native terminal groups
and allowed 1,340 noncritical items to move while retaining 1,158 local or critical
items. Ground, RF and SIM stayed protected.

The first DSN loaded 74 opens although KiCad reported eight. That run was stopped
without importing its result. An explicit same-net center contact and exact-copper
contact normalization made the second DSN load the correct eight opens.

Eight strict router passes still left eight opens. **No SES was imported.** The
saved board has eight native opens, 21 dangling-via warnings and no other native
violations or schematic mismatches. Do not repeat this unchanged router input.

The router's clearance inventory includes conservative shape-model differences;
it is not a list of demonstrated KiCad clearance violations. Neither this trial
nor its input inspection is supplier or electrical approval.

The saved native source and `joint-contacts-result.json` record the final input
and result. r05c remains unchanged; r05e explores a separate native reroute.
