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

Batch from CSV (columns: `text,subtext,icon,bit_size,ref_mm,thread,tape,length` - all but
`text` optional, `thread`/`tape`/`length` fall back to `--thread`/`--tape`/`--length`):

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
apart. All heads share one junction line with the shaft (see `JUNCTION_FRAC`),
so they line up label to label regardless of head shape.

- `hex_head` - wrench-driven hex head (ISO 4017), short block + 2 facet lines
- `socket_head` - hex socket cap screw (DIN 912), flat-topped cylinder
- `button_head` - hex socket button head (ISO 7380), low dome
- `countersunk_head` - hex socket countersunk/flat head (ISO 10642), flush cone
- `pan_head` - slotted/Phillips pan head, shallow rounded-top cylinder
- `carriage_head` - round head + square neck (chamfer marks hint the square
  cross-section), no bit - held by the neck while a nut is tightened
- `flange_head` - hex head with an integrated washer-like flange at the base

Every head above defaults to a **bolt** shaft: a flush shank with the thread
marked as ticks on its surface, since a bolt is meant to be torqued against a
nut rather than into the material itself. Pass `--thread screw` to draw a
**screw** shaft instead - a thinner core with the actual thread crests
poking out past it - for a fastener that threads directly into a tapped hole.

Heads with a drive recess (see `BIT_FOR_HEAD`) get a separate small bit-shape
icon flush against the *right* edge of the label, past the text - not crammed
inside the head outline, so it stays legible at 12mm-tape sizes:
`socket_head`/`button_head`/`countersunk_head` get a hex-key outline,
`pan_head` gets a Phillips cross. `hex_head`/`flange_head`/`carriage_head`
get none - wrench-driven or (for carriage bolts) not driven by the head at
all. Pass `--bit-size "3"` (a hex key size) or `--bit-size "PH2"` (a Phillips
size) to add a small label under that bit icon.

Nuts and washers stay top-down, where their shape is the distinctive part:
`nut`, `locknut` (nyloc - filled insert ring round the hole, vs. `nut`'s open
hole), `washer`. Washer OD/thickness aren't encoded in the icon (too small to
read) - put them in `--subtext` instead, e.g. `--subtext "OD9 x t0.8"`.

See `ptouch_batch_labels/icons.py` - adding a new head is a small function
using `PIL.ImageDraw`, registered in the `ICONS` dict (and `BIT_FOR_HEAD` if
it needs a bit icon).

## Measurement reference line

`--ref-mm 20` reserves a strip along the bottom of the label for a thin line,
with caliper-style end-ticks, exactly 20mm long - check a loose bolt's length,
a nut's thickness, a washer's OD, etc. against the printed label directly,
no caliper needed. Only fits up to roughly 30mm on a typical label (raises a
clear error if the line would be longer than the label itself - use a longer
`--length` instead of guessing).
