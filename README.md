# ptouch-batch-labels

Generate Brother P-touch labels (text + a small vector fastener-icon set) as
2-color PNGs, sized for any tape width/label length, ready to hand to
[ptouch-print](https://github.com/enachb/ptouch-print) `--image` for printing
on Linux (tested against a PT-P710BT).

Built for labelling Gridfinity bins, but the renderer is generic.

## Why PNGs instead of ptouch-print's `--text`/`--image` directly

`ptouch-print` can print text or a single image per invocation, but has no
layout control (no icon + text together, no auto column/spreadsheet input).
This renders the full label - icon and text together, auto-sized - to a PNG
in the exact palette format `ptouch-print --image` expects, so batches can be
driven from a spreadsheet/CSV.

## Tape geometry

From `ptouch-print`'s own tape table (180dpi, 128px max head width):

| tape (mm) | usable px |
|-----------|-----------|
| 6         | 32        |
| 9         | 52        |
| 12        | 76        |
| 18        | 120       |
| 24        | 128       |
| 36        | 192       |

Tape *color* (white-on-black, black-on-white, black-on-transparent) doesn't
matter here - `ptouch-print` auto-detects which of the two palette colors is
"ink" at print time, so the same PNG works on any tape.

## Usage

```
pip install -r requirements.txt
```

Single label:

```
python3 -m ptouch_batch_labels.cli single --text "M4x20" --subtext "bolts" --icon socket_head --tape 12 --length 35 --out m4x20.png
```

A lone `--text` (no `--subtext`) is centered and sized to fill the whole
label height. With both, `--text` renders bold and larger, `--subtext`
smaller underneath - matching the existing "M3x12mm / bolts" label style.

Batch from CSV (columns: `text,subtext,icon,tape,length` - `subtext`/`icon`/`tape`/`length`
optional, `tape`/`length` fall back to `--tape`/`--length`):

```
python3 -m ptouch_batch_labels.cli batch example_gridfinity_hardware.csv --tape 12 --length 35 --outdir labels_out
```

Add `--print` to pipe each generated label straight to `ptouch-print --image`
(printer must be connected over USB); add `--cutmark` to insert a guide line
between labels within one print run (dashed print marks only, not a cut).

By default nothing gets physically cut - this expects
[kernicek/ptouch-print](https://github.com/kernicek/ptouch-print) (forked
from [enachb/ptouch-print](https://github.com/enachb/ptouch-print)), which
feeds but doesn't cut at the end of a job, so a *later* `--print` run's
labels continue on the same held tape with no wasted feed-to-cutter margin
in between. Add `--final-cut` when you actually want to pull the tape free.

## Icons

Bolt heads are drawn in **side profile** (head shape + a short threaded-shaft
stub), not from above - from above a socket/button/countersunk head is just
"circle with a hex hole", so the side silhouette is what actually tells them
apart. The three hex-socket types also get a separate small hexagon icon
next to the head for the hex key ("bit") they need - drawn as its own shape
rather than crammed inside the head outline, so it stays legible at 12mm-tape
sizes:

- `hex_head` - wrench-driven hex head (ISO 4017), short hex prism. No bit
  icon - the head's own hex shape is the drive, not an internal recess.
- `socket_head` - hex socket cap screw (DIN 912), flat-topped cylinder + hex bit
- `button_head` - hex socket button head (ISO 7380), low dome + hex bit
- `countersunk_head` - hex socket countersunk/flat head (ISO 10642), flush cone + hex bit

Nuts and washers stay top-down, where their shape is the distinctive part:
`nut`, `locknut` (nyloc - filled insert ring round the hole, vs. `nut`'s open
hole), `washer`. Washer OD/thickness aren't encoded in the icon (too small to
read) - put them in `--subtext` instead, e.g. `--subtext "OD9 x t0.8"`.

See `ptouch_batch_labels/icons.py` - adding a new one is a small function using
`PIL.ImageDraw`, registered in the `ICONS` dict.

## Ideas for later (not implemented)

- **Printed length/size reference line.** For a bolt, a thin line at the
  bottom of the label exactly as long as the bolt itself, so you can check a
  loose bolt against the label without a caliper. Only works up to roughly
  30mm (label length limit before it'd need a second row or a much longer
  tape). Same idea could apply to other dimensions already in `--subtext` -
  e.g. a nut's thickness, a washer's OD - as a small reference mark/line
  sized to that measurement rather than just stating the number.
