# README media

The root README is a project overview; current engineering state remains in
[STATUS](../STATUS.md). These illustrations reuse the preserved CAD and describe
implemented source behavior without claiming a built or qualified product.

| Asset | Source and scope |
| --- | --- |
| `assembly.gif` | Eight-second CAD loop: closed enclosure → separated layers → closed enclosure. |
| `mount.gif` | Eight-second CAD loop: flat 25 × 3, 8 × 1, 60 × 8 mm and round Ø8 mm collar examples. |
| `pcb.webp` | Resized current KiCad render; four package bodies use dimensional visual substitutes. |
| `architecture.svg` | Hand-authored delivery/acknowledgment diagram, grounded in tracker and receiver source documentation. |
| `*-poster.png` | First animation frames for static reuse. |
| [provenance.json](provenance.json) | Source identity, rendering settings, sampled states and output hashes. |

The existing CAD viewer supplies all 3D meshes and materials. The renderer creates
an ignored capture copy, injects deterministic camera/layer poses, and captures
96 frames at 960 × 600 for each 12 fps GIF. External network access is blocked.
FFmpeg uses a 128-color palette; both animations together are about 3.2 MB.
The native PCB, CAD source, original viewer and released ZIPs are unchanged.

## Regenerate

Requires Node.js, Playwright with Chromium, FFmpeg and ImageMagick. Set
`COLLAR_PLAYWRIGHT_MODULE` to a Playwright installation if needed; the shared
project runtime helper handles the existing workstation setup.

```sh
node scripts/render_readme_media.cjs
```

Frames and the capture HTML go under `.runtime/readme-media/`; only reviewed
assets and provenance are committed. Renderer/encoder versions can change bytes,
so the saved hashes identify this delivery rather than promising identical output
from every tool version. The diagram remains editable SVG.

The installed bands show routing envelopes, not deformed button/keeper overlap.
The animations are CAD illustrations; physical grip, comfort, strength and IP68
qualification remain open. Firmware builds and host tests are separate from a
powered collar demonstration.
