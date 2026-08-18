"""Small vector-drawn icon set for fastener labels.

Bolts are drawn in SIDE profile, head on top / shaft below (like a standard
fastener-type chart) - that's what actually distinguishes socket / button /
countersunk heads; from above they're all just "circle with a hex hole". All
four head shapes share the same top-aligned reference line, so they line up
next to each other. The hex-key bit (for the three hex-socket types) is a
separate small icon - see `NEEDS_BIT` / `render_bit_icon()` - meant to sit on
the far side of the label text, not against the head. Nuts/washers are drawn
top-down instead, where their shape is distinctive.

Each icon function takes a target pixel height and returns a PIL 'L' image
(255 = blank tape, 0 = ink). Drawn at 4x and downsampled so curves stay
smooth even at small sizes.
"""

from PIL import Image, ImageDraw

SUPERSAMPLE = 4
BOLT_ASPECT = 0.62  # bolt icon width relative to its height


def _canvas(w, h):
    return Image.new("L", (w * SUPERSAMPLE, h * SUPERSAMPLE), 255), w * SUPERSAMPLE, h * SUPERSAMPLE


def _finish(img, w, h):
    """Downsample from the supersampled canvas and snap straight back to
    pure black/white. BOX is a plain area-average with no ringing (unlike
    LANCZOS), and since the output is strictly 2-color anyway, hard
    thresholding right here avoids leftover gray specks surviving into the
    final palette conversion as stray noise pixels."""
    small = img.resize((w, h), Image.BOX)
    return small.point(lambda p: 0 if p < 128 else 255)


THREAD_PITCH_FRAC = 0.22  # thread tick spacing, as a fraction of icon height H


def _shaft(d, x0, x1, y0, y1, lw, pitch):
    """Threaded shank, running from y0 to y1, with diagonal thread ticks
    rising left-to-right ("/"), matching a right-hand thread helix. No top
    edge - the head shape above already closes that junction.

    `pitch` is an absolute pixel spacing (pass the SAME value - some fraction
    of H - for every head type), not a fixed tick count: heads have
    different heights, so a fixed count of ticks would get crammed into
    whatever shaft length was left over and end up a different density/angle
    per head. A fixed pitch keeps the thread ticks visually identical
    everywhere, how ever much shaft each head leaves."""
    d.line([x0, y0, x0, y1], fill=0, width=lw)
    d.line([x1, y0, x1, y1], fill=0, width=lw)
    d.line([x0, y1, x1, y1], fill=0, width=lw)
    dx = (x1 - x0) * 0.4
    n = max(1, round((y1 - y0) / pitch) - 1)
    step = (y1 - y0) / (n + 1)
    for i in range(1, n + 1):
        y = y0 + step * i
        d.line([x0 + dx, y + pitch * 0.3, x1 - dx, y - pitch * 0.3], fill=0, width=max(1, lw - 1))


def _bolt_canvas(height):
    w = round(height * BOLT_ASPECT)
    img, W, H = _canvas(w, height)
    return img, ImageDraw.Draw(img), W, H, w


def render_bit_icon(height):
    """Hex-key drive bit, as its own standalone icon."""
    img, H = Image.new("L", (height * SUPERSAMPLE, height * SUPERSAMPLE), 255), height * SUPERSAMPLE
    d = ImageDraw.Draw(img)
    lw = max(2, H // 20)
    c, r = H / 2, H * 0.42
    d.regular_polygon((c, c, r), n_sides=6, outline=0, width=lw)
    return _finish(img, height, height)


JUNCTION_FRAC = 0.4  # head/shaft junction, shared by all 4 heads - see below


def hex_head(height):
    """Wrench-driven hex head bolt (ISO 4017) - short block with 2 facet
    lines. No bit icon: the head's own facets are the drive, not an internal
    recess."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    head_h = H * 0.27
    top = junction - head_h
    x0, x1 = W * 0.06, W * 0.94
    d.rectangle([x0, top, x1, junction], outline=0, width=lw)
    for frac in (1 / 3, 2 / 3):
        x = x0 + frac * (x1 - x0)
        d.line([x, top, x, junction], fill=0, width=lw)
    shaft_w = W * 0.42
    _shaft(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def socket_head(height):
    """Hex socket cap head (DIN 912) - plain flat-topped block. This is the
    tallest of the 4 heads, so it sets JUNCTION_FRAC (its top lands at y=0;
    the other 3, being shorter, hang from the same junction with blank space
    above)."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    head_h = H * 0.4
    top = junction - head_h
    x0, x1 = W * 0.06, W * 0.94
    d.rectangle([x0, top, x1, junction], outline=0, width=lw)
    shaft_w = W * 0.42
    _shaft(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def button_head(height):
    """Hex socket button head (ISO 7380) - true semicircular dome, bottom
    (flat chord) pinned to the shared junction line."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    x0, x1 = W * 0.04, W * 0.96
    r = (x1 - x0) / 2
    top = junction - r
    d.pieslice([x0, top, x1, top + 2 * r], start=180, end=360, outline=0, width=lw)
    shaft_w = W * 0.42
    _shaft(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def countersunk_head(height):
    """Hex socket countersunk / flat head (ISO 10642) - flush cone, bottom
    (narrow end, meeting the shank) pinned to the shared junction line.
    Flat top (flush with the surface) flaring to the full head width, over a
    short cone down to the shaft width."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    head_h = H * 0.22
    top = junction - head_h
    x0, x1 = 0, W
    shaft_w = W * 0.42
    sx0, sx1 = (W - shaft_w) / 2, (W + shaft_w) / 2
    d.polygon([(x0, top), (x1, top), (sx1, junction), (sx0, junction)], outline=0, width=lw)
    _shaft(d, sx0, sx1, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def nut(height):
    w = height
    img, W, H = _canvas(w, height)
    d = ImageDraw.Draw(img)
    lw = max(2, H // 24)
    c, r, hole = W / 2, W * 0.42, W * 0.18
    d.regular_polygon((c, c, r), n_sides=6, outline=0, width=lw)
    d.ellipse([c - hole, c - hole, c + hole, c + hole], outline=0, width=lw)
    return _finish(img, w, height)


def locknut(height):
    """Nylon-insert (nyloc) nut: hex nut with a filled insert ring round the hole."""
    w = height
    img, W, H = _canvas(w, height)
    d = ImageDraw.Draw(img)
    lw = max(2, H // 24)
    c, r, hole, ring = W / 2, W * 0.42, W * 0.16, W * 0.24
    d.regular_polygon((c, c, r), n_sides=6, outline=0, width=lw)
    d.ellipse([c - ring, c - ring, c + ring, c + ring], fill=0)
    d.ellipse([c - hole, c - hole, c + hole, c + hole], fill=255)
    return _finish(img, w, height)


def washer(height):
    w = height
    img, W, H = _canvas(w, height)
    d = ImageDraw.Draw(img)
    lw = max(2, H // 24)
    c, r, hole = W / 2, W * 0.42, W * 0.22
    d.ellipse([c - r, c - r, c + r, c + r], outline=0, width=lw)
    d.ellipse([c - hole, c - hole, c + hole, c + hole], outline=0, width=lw)
    return _finish(img, w, height)


ICONS = {
    "hex_head": hex_head,
    "socket_head": socket_head,
    "button_head": button_head,
    "countersunk_head": countersunk_head,
    "nut": nut,
    "locknut": locknut,
    "washer": washer,
}

# Head types with an internal hex-key recess - these get a separate bit icon
# drawn on the far side of the label (past the text), not against the head.
NEEDS_BIT = {"socket_head", "button_head", "countersunk_head"}


def render_icon(name, height):
    try:
        return ICONS[name](height)
    except KeyError:
        raise ValueError(f"unknown icon '{name}', known icons: {sorted(ICONS)}")
