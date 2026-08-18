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

Every head also takes `screw=True` to swap its shaft from a bolt's flush
shank (thread marked as ticks on a full-width surface, meant to pair with a
nut) to a screw's: a thinner core with the thread crests actually poking out
past it, since a screw threads directly into the material rather than
against a nut - see `_shaft` vs `_screw_shaft`.
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


THREAD_PITCH_FRAC = 0.15  # thread tick spacing, as a fraction of icon height H
# (with the shared JUNCTION_FRAC, every head now has the same shaft length,
# so this pitch gives the same 3 ticks everywhere rather than needing a
# fixed count.)


def _screw_shaft(d, x0, x1, y0, y1, lw, pitch):
    """Machine-screw shaft: a thin core with thread crests poking OUT to the
    full bolt-shaft width at every half pitch, instead of a bolt's flush
    shaft with ticks marked on its surface - a saw-tooth silhouette is the
    standard way to read "threaded" at a glance, vs a bolt's plain shank.
    The two sides are a half-pitch out of phase with each other (one pokes
    out while the other tucks in to the core), tracing the same slant a real
    thread helix does when seen from the side - a bolt's ticks, by contrast,
    are deliberately in-phase left/right, since those mark a plain surface
    rather than an actual 3D thread profile."""
    core_half = (x1 - x0) * 0.25
    cx = (x0 + x1) / 2
    cx0, cx1 = cx - core_half, cx + core_half
    half_pitch = pitch / 2
    n = max(2, round((y1 - y0) / half_pitch))
    if n % 2:
        n += 1
    step = (y1 - y0) / n
    left_pts, right_pts = [], []
    for i in range(n + 1):
        y = y0 + step * i
        left_pts.append((x0 if i % 2 == 1 else cx0, y))
        right_pts.append((x1 if i % 2 == 0 else cx1, y))
    d.line(left_pts, fill=0, width=lw, joint="curve")
    d.line(right_pts, fill=0, width=lw, joint="curve")
    d.line([left_pts[-1][0], y1, right_pts[-1][0], y1], fill=0, width=lw)


def _shaft(d, x0, x1, y0, y1, lw, pitch):
    """Threaded shank, running from y0 to y1, with shallow, mostly-horizontal
    thread ticks rising left-to-right ("/"), matching a right-hand thread
    helix. No top edge - the head shape above already closes that junction.

    `pitch` is an absolute pixel spacing (pass the SAME value - some fraction
    of H - for every head type), not a fixed tick count: heads have
    different heights, so a fixed count of ticks would get crammed into
    whatever shaft length was left over and end up a different density/angle
    per head. A fixed pitch keeps the thread ticks visually identical
    everywhere, how ever much shaft each head leaves."""
    d.line([x0, y0, x0, y1], fill=0, width=lw)
    d.line([x1, y0, x1, y1], fill=0, width=lw)
    d.line([x0, y1, x1, y1], fill=0, width=lw)
    dx = (x1 - x0) * 0.2
    n = max(1, round((y1 - y0) / pitch) - 1)
    step = (y1 - y0) / (n + 1)
    for i in range(1, n + 1):
        y = y0 + step * i
        d.line([x0 + dx, y + pitch * 0.15, x1 - dx, y - pitch * 0.15], fill=0, width=max(1, lw - 1))


def _bolt_canvas(height):
    w = round(height * BOLT_ASPECT)
    img, W, H = _canvas(w, height)
    return img, ImageDraw.Draw(img), W, H, w


def render_bit_icon(kind, height):
    """Drive-bit icon, as its own standalone shape."""
    img, H = Image.new("L", (height * SUPERSAMPLE, height * SUPERSAMPLE), 255), height * SUPERSAMPLE
    d = ImageDraw.Draw(img)
    c = H / 2
    if kind == "hex":
        r = H * 0.42
        d.regular_polygon((c, c, r), n_sides=6, outline=0, width=max(2, H // 12))
    elif kind == "phillips":
        a = H * 0.36
        lw = 2 * SUPERSAMPLE  # fixed final-resolution 2px, not scaled with H -
        # scaling it made the two crossing strokes overlap into a blob at
        # the center instead of a clean thin cross.
        d.line([c - a, c, c + a, c], fill=0, width=lw)
        d.line([c, c - a, c, c + a], fill=0, width=lw)
    else:
        raise ValueError(f"unknown bit kind '{kind}'")
    return _finish(img, height, height)


JUNCTION_FRAC = 0.4  # head/shaft junction, shared by all 4 heads - see below


def hex_head(height, screw=False):
    """Wrench-driven hex head bolt (ISO 4017) - short block with 2 facet
    lines. The two lines sit closer to the edges than a plain three-way
    split, since the middle section is the hex's front face (what you're
    actually looking at) and the two outer strips are its side facets
    receding away - the face reads wider, not equal thirds. No bit icon:
    the head's own facets are the drive, not an internal recess."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    head_h = H * 0.27
    top = junction - head_h
    x0, x1 = W * 0.06, W * 0.94
    d.rectangle([x0, top, x1, junction], outline=0, width=lw)
    for frac in (0.22, 0.78):
        x = x0 + frac * (x1 - x0)
        d.line([x, top, x, junction], fill=0, width=lw)
    shaft_w = W * 0.42
    shaft_fn = _screw_shaft if screw else _shaft
    shaft_fn(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def socket_head(height, screw=False):
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
    shaft_fn = _screw_shaft if screw else _shaft
    shaft_fn(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def button_head(height, screw=False):
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
    shaft_fn = _screw_shaft if screw else _shaft
    shaft_fn(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def countersunk_head(height, screw=False):
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
    shaft_fn = _screw_shaft if screw else _shaft
    shaft_fn(d, sx0, sx1, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def pan_head(height, screw=False):
    """Pan head (slotted/Phillips machine screw) - a low rounded-top
    cylinder: a shallow dome cap (flatter than button_head's full
    semicircle) over straight cylindrical sides. Phillips bit."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    x0, x1 = W * 0.06, W * 0.94
    dome_h = H * 0.09
    body_h = H * 0.17
    top = junction - dome_h - body_h
    body_top = top + dome_h
    d.arc([x0, top, x1, top + 2 * dome_h], start=180, end=360, fill=0, width=lw)
    d.line([x0, body_top, x0, junction], fill=0, width=lw)
    d.line([x1, body_top, x1, junction], fill=0, width=lw)
    d.line([x0, junction, x1, junction], fill=0, width=lw)
    d.line([x0, body_top, x1, body_top], fill=0, width=max(1, lw - 2))
    shaft_w = W * 0.42
    shaft_fn = _screw_shaft if screw else _shaft
    shaft_fn(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def carriage_head(height, screw=False):
    """Carriage bolt - round head, square neck. A full rounded dome (fuller
    than button_head's flatter one) sits on a short square-shouldered neck
    that bites into the material to stop the bolt turning. No bit icon: it's
    driven by holding the head still while a nut is tightened from below,
    not by anything in the head itself."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    x0, x1 = W * 0.06, W * 0.94
    r = (x1 - x0) / 2
    dome_h = r * 0.8
    neck_h = H * 0.16
    top = junction - dome_h - neck_h
    neck_top = top + dome_h
    d.pieslice([x0, top, x1, top + 2 * dome_h], start=180, end=360, outline=0, width=lw)
    neck_w = W * 0.72
    nx0, nx1 = (W - neck_w) / 2, (W + neck_w) / 2
    d.rectangle([nx0, neck_top, nx1, junction], outline=0, width=lw)
    chamfer = neck_h * 0.4
    d.line([nx0, neck_top + chamfer, nx0 + chamfer, neck_top], fill=0, width=lw)
    d.line([nx1 - chamfer, neck_top, nx1, neck_top + chamfer], fill=0, width=lw)
    shaft_w = W * 0.42
    shaft_fn = _screw_shaft if screw else _shaft
    shaft_fn(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def flange_head(height, screw=False):
    """Flanged button head - a button_head dome with an integrated
    washer-like spacer/collar between the head and the shaft (like a
    shoulder screw's shoulder). Hex key bit, same as button_head."""
    img, d, W, H, w = _bolt_canvas(height)
    lw = max(2, H // 20)
    junction = H * JUNCTION_FRAC
    x0, x1 = W * 0.04, W * 0.96
    r = (x1 - x0) / 2
    collar_h = H * 0.1
    collar_top = junction - collar_h
    dome_top = collar_top - r  # dome height above its own flat chord is r,
    # same convention as button_head - not 2r, that's the full bbox height
    d.pieslice([x0, dome_top, x1, dome_top + 2 * r], start=180, end=360, outline=0, width=lw)
    # the collar is the actual flange/washer, so it has to visibly stick out
    # past the head - that's the entire point of one - not match its width.
    d.rectangle([0, collar_top, W, junction], outline=0, width=lw)
    shaft_w = W * 0.42
    shaft_fn = _screw_shaft if screw else _shaft
    shaft_fn(d, (W - shaft_w) / 2, (W + shaft_w) / 2, junction, H, lw, H * THREAD_PITCH_FRAC)
    return _finish(img, w, height)


def nut(height, screw=False):
    w = height
    img, W, H = _canvas(w, height)
    d = ImageDraw.Draw(img)
    lw = max(2, H // 24)
    c, r, hole = W / 2, W * 0.42, W * 0.18
    d.regular_polygon((c, c, r), n_sides=6, outline=0, width=lw)
    d.ellipse([c - hole, c - hole, c + hole, c + hole], outline=0, width=lw)
    return _finish(img, w, height)


def locknut(height, screw=False):
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


def washer(height, screw=False):
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
    "pan_head": pan_head,
    "carriage_head": carriage_head,
    "flange_head": flange_head,
    "nut": nut,
    "locknut": locknut,
    "washer": washer,
}

# Head types with a drive recess - these get a separate bit icon (value =
# which shape) drawn on the far side of the label, not against the head.
# hex_head/carriage_head aren't here: wrench-driven or (for carriage bolts)
# not driven by the head at all, so there's no recess to show.
BIT_FOR_HEAD = {
    "socket_head": "hex",
    "button_head": "hex",
    "countersunk_head": "hex",
    "flange_head": "hex",  # it's a button_head variant - same drive
    "pan_head": "phillips",
}


def render_icon(name, height, screw=False):
    try:
        return ICONS[name](height, screw=screw)
    except KeyError:
        raise ValueError(f"unknown icon '{name}', known icons: {sorted(ICONS)}")
