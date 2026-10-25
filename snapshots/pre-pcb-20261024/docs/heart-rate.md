# Heart-rate sensing — research status

Heart-rate measurement is requested. Operation across dog sizes, coat types and
movement states has not been demonstrated. Filtering and peak-interval calculation
do not require on-device AI, but a usable physical signal must come first.

## Evidence inspected

The abstract of a study in 12 healthy dogs, published online in November 2024 and
in the February 2025 issue, reported close agreement between collar and Holter
24-hour mean heart rates but poor agreement over two-minute intervals. The collar
produced no heart-rate output for 43% of possible recording time. This does not
establish that every collar behaves alike or that our proposed sensor will work.
Only the abstract was inspected here.

[Assessment of heart rate measurements obtained from a smart collar compared to
24-h Holter monitoring in healthy dogs](https://pubmed.ncbi.nlm.nih.gov/39675258/)

A 2019 mechanocardiography study evaluated resting measurements with a phone on
the chest, reporting limitations involving fur, sliding and signal quality. This
does not prove a neck collar works; it supports starting with rest and explicit
signal-quality checks.

[Cardiac monitoring of dogs via smartphone mechanocardiography](https://pmc.ncbi.nlm.nih.gov/articles/PMC6480821/)

## Candidate methods

| Method | Mechanical requirement | Open issue |
|---|---|---|
| Optical PPG | LED/photodiode, controlled skin contact and light isolation | Fur, movement and contact pressure |
| ECG | Separate skin contacts, electrode geometry and protected analog input | Signal at collar position, fur and movement |
| Mechanical/acoustic | Contact transmitting small cardiac motion/sounds | Separating cardiac activity from walking and breathing |

MAX86176 is a roughly 2.73 × 2.71 mm PPG+ECG analog-front-end candidate, not a
complete sensor. PPG needs LEDs, photodiodes and optical mechanics; ECG needs
electrodes and an appropriate input circuit. Human-wearable specifications do not
prove canine accuracy. The manufacturer indicates an NDA process for full document
access, so this part has not been selected.

[Analog Devices MAX86176](https://www.analog.com/en/products/MAX86176.html)

## First prototype work

Expose I2C/SPI, interrupt, reset and supply to an experimental sensor board. Do not
connect electrodes directly to the general digital connector; design the analog
protection/front end separately.

Verify signal path and power on the bench, then compare against suitable reference
ECG, reporting rest and motion separately. Report valid-output coverage and error
distribution, not only mean error. Include different sizes/coats. Suppress readings
when signal quality is inadequate; do not present an activity-derived estimate as
measured heart rate.
