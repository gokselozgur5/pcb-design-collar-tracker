# Türkiye connectivity evidence — 2026-10-26

**Keep nRF9151 as the prototype candidate; local SIM/service and moving-device
acceptance remain open.** Public evidence does not justify either assuming that
it cannot connect in Türkiye or promising that any 4G SIM will work.

| Evidence inspected | What it supports | What it does not establish |
|---|---|---|
| [Nordic operator certification list](https://www.nordicsemi.com/Products/Wireless/Low-power-cellular-IoT/nRF91-Series-certifications/Mobile-network-operator) | nRF9151's Vodafone listing includes Türkiye among countries using NB-IoT and/or LTE-M | Which radio mode a particular Turkish site and subscription enables; approval of this finished collar |
| [Turkcell NB-IoT service](https://www.turkcell.com.tr/kurumsal/dijital-is-servisleri/iot-nesnelerin-interneti/nb-iot) | Activated corporate M2M service, compatible LTE SIM and NB-IoT APN; the page emphasizes stationary/small-message applications | LTE-M availability on our intended route, rapid reporting or moving-dog performance |
| [Turkcell 2025 Form 20-F, printed page 58 / PDF page 60](https://s.turkcell.com.tr/SiteAssets/Hakkimizda/yatirimci-iliskileri/documents/pdf/20F2025.pdf#page=60) | The operator states that NB-IoT and LTE-M are available on request throughout its 4.5G footprint, and identifies LTE-M uses including fleet/asset tracking and micromobility | Activation for a specific subscription, route coverage, nRF9151 end-product acceptance, actual latency or energy consumption |
| [Firsthand nRF9151-DK support case](https://devzone.nordicsemi.com/f/nordic-q-a/127191/nrf9151-dk-not-establishing-an-lte-m-or-nb-iot-connection-neither-with-wireless-logic-nor-onomondo-sims-in-turkiye) | The author reports internet access with a local Vodafone phone SIM after roaming-SIM failures | An independently reproduced result, a stated successful radio mode, a permitted production tariff or coverage guarantee |

The support thread's roaming explanations remain participants' reports; they are
not a legal or universal network conclusion. The search also found an old GSMA
Turkcell rollout snippet, but its full page returned HTTP 403. That snippet is not
used as present-day service acceptance.

The 2025 filing is stronger primary evidence for Turkcell LTE-M availability
than the older search snippet. The full PDF and the rendered network-evolution
page were inspected on 2026-10-26; its SHA256 is
`21379c60757aa5450f7e7b1108eca0f93e46b9653003ee972bbbf24b3a887aa4`.
This is an operator statement, not an observed modem or moving-collar result.
The next step is the controlled local-subscription test below, not replacing the
modem based on an assumption that Türkiye has no LTE-M service.

The [nRF9151 product specification](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/product_overview.html)
describes LTE Cat-M1/NB1/NB2 operation. A nano-SIM socket does not add Cat-1 support.
No modem substitution or carrier purchase was made from these web results.

## Discriminating prototype check

Use the intended local subscription on an nRF9151 development kit before committing
to a pack/antenna production assembly. Record the SIM's 1.8 V compatibility and
service authorization without publishing SIM identifiers or credentials.

Capture modem/SDK versions, enabled radio mode, serving PLMN/band, registration
and reject causes, APN, data-session success, signal quality and timestamps.
Evaluate LTE-M and NB-IoT separately; successful registration alone is insufficient.

Then repeat actual location uploads while moving between cells, after loss of
coverage, after sleep/wake and after a network rejection. Compare reporting delay
and energy with the intended product interval. A desk test does not establish
moving-animal coverage. The final enclosure/body antenna test remains separate.

No SIM was purchased, operator contacted, modem powered or account configured.
