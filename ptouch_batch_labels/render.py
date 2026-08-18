"""Compose an icon + text label into a PNG ptouch-print will accept:
palette mode, exactly 2 colors, height <= the tape's usable print px."""

from PIL import Image, ImageDraw, ImageFont

from .icons import NEEDS_BIT, render_bit_icon, render_icon
from .tape import mm_to_px, tape_height_px

BOLD_FONT = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"
REGULAR_FONT = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"
MARGIN_PX = 3


_dummy_draw = ImageDraw.Draw(Image.new("L", (1, 1)))


def _fit_font_size(draw, lines, font_path, max_width, max_line_height):
    lo, hi = 4, max(4, max_line_height)
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        font = ImageFont.truetype(font_path, mid)
        widths = [draw.textbbox((0, 0), line, font=font)[2] for line in lines]
        if max(widths) <= max_width:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _fit_font(draw, lines, font_path, max_width, max_line_height):
    return ImageFont.truetype(font_path, _fit_font_size(draw, lines, font_path, max_width, max_line_height))


def _layout(icon, width, height):
    """Where everything goes: bolt icon on the left, hex-key bit icon (if
    this head type needs one) flush against the right edge, text in
    whatever's left between them. Shared by render_label and by
    fit_uniform_font_sizes so both agree on the available text width.

    The icon always gets a fixed SQUARE zone (avail_height wide), with the
    actual icon image - narrower for bolts (BOLT_ASPECT < 1), full-width for
    nut/washer/locknut - centered inside it. Without this, bolt icons (being
    narrower) would leave text starting at a different x than nut/washer
    rows, so the text column wouldn't line up label to label.
    """
    text_x0 = MARGIN_PX
    right_edge = width - MARGIN_PX
    avail_height = height - 2 * MARGIN_PX
    icon_img = icon_x = bit_img = bit_x = None
    if icon:
        icon_img = render_icon(icon, avail_height)
        icon_zone_w = avail_height  # square
        icon_x = MARGIN_PX + (icon_zone_w - icon_img.width) // 2
        text_x0 = MARGIN_PX + icon_zone_w + MARGIN_PX
        if icon in NEEDS_BIT:
            bit_img = render_bit_icon(round(avail_height * 0.4))
            bit_x = width - MARGIN_PX - bit_img.width
            right_edge = bit_x - MARGIN_PX
    max_width = right_edge - text_x0
    return text_x0, max_width, avail_height, icon_img, icon_x, bit_img, bit_x


def label_geometry(icon, tape_mm, length_mm):
    """Pixel geometry for a label, without drawing any text - shared by
    render_label and by batch callers that need to fit one font size across
    many labels with different icons/widths."""
    height = tape_height_px(tape_mm)
    width = mm_to_px(length_mm)
    text_x0, max_width, avail_height, _, _, _, _ = _layout(icon, width, height)
    return width, height, text_x0, max_width, avail_height


def _text_budgets(avail_height):
    """(gap, main_budget, sub_budget) for a text+subtext stack: `gap` is
    real inserted spacing between the lines (see _draw_centered_block), not
    just a font-size reduction, so this can stay a modest fraction - it's no
    longer fighting to "read as" separation, it actually is one."""
    gap = max(2, round(avail_height * 0.09))
    main_budget = round((avail_height - gap) * 0.62)
    sub_budget = avail_height - gap - main_budget
    return gap, main_budget, sub_budget


def fit_uniform_font_sizes(rows, font_path=None, subtext_font_path=None):
    """rows: dicts with text/subtext/icon/tape/length (as produced by the CLI).
    Returns (main_size, subtext_size) - the largest sizes that fit every row,
    so a whole batch prints at one consistent main-text size instead of each
    label auto-filling its own width independently."""
    font_path = font_path or BOLD_FONT
    subtext_font_path = subtext_font_path or REGULAR_FONT
    main_sizes, sub_sizes = [], []
    for r in rows:
        text, subtext = r.get("text"), r.get("subtext")
        if not text:
            continue
        _, _, _, max_width, avail_height = label_geometry(r.get("icon"), r["tape"], r["length"])
        if max_width <= 0:
            raise ValueError("icon leaves no room for text at this label length")
        if subtext:
            _, main_budget, sub_budget = _text_budgets(avail_height)
            main_sizes.append(_fit_font_size(_dummy_draw, [text], font_path, max_width, main_budget))
            sub_sizes.append(_fit_font_size(_dummy_draw, [subtext], subtext_font_path, max_width, sub_budget))
        else:
            lines = text.split("\n")
            max_line_height = avail_height // len(lines)
            main_sizes.append(_fit_font_size(_dummy_draw, lines, font_path, max_width, max_line_height))
    main_size = min(main_sizes) if main_sizes else None
    sub_size = min(sub_sizes) if sub_sizes else None
    return main_size, sub_size


def _draw_centered_block(draw, lines_and_fonts, x0, y0, max_width, total_height, gaps=None):
    """lines_and_fonts: [(text, font), ...]. Centers the whole stack vertically
    within total_height starting at y0 (the top margin - `draw` is on the
    FULL label canvas, not one already cropped to the text area, so this
    offset has to be added explicitly or the block sits high by y0 px), each
    line horizontally centered within max_width.

    `gaps`, if given, is a list of length len(lines_and_fonts)-1: explicit
    pixel spacing inserted BETWEEN each pair of lines. Without this the block
    is just the lines stacked flush - shrinking each line's own font (as a
    "budget" during fitting) does NOT by itself add space between them, it
    only pads the block's top/bottom margins equally once centered."""
    gaps = gaps or [0] * (len(lines_and_fonts) - 1)
    bboxes = [draw.textbbox((0, 0), t, font=f) for t, f in lines_and_fonts]
    heights = [b[3] - b[1] for b in bboxes]
    y = y0 + (total_height - sum(heights) - sum(gaps)) / 2
    for i, ((t, f), bbox, h) in enumerate(zip(lines_and_fonts, bboxes, heights)):
        w = bbox[2] - bbox[0]
        x = x0 + max(0, (max_width - w) / 2)
        draw.text((x, y - bbox[1]), t, fill=0, font=f)
        y += h
        if i < len(gaps):
            y += gaps[i]


def render_label(
    text=None,
    subtext=None,
    icon=None,
    tape_mm=12,
    length_mm=35,
    font_path=BOLD_FONT,
    subtext_font_path=REGULAR_FONT,
    font_size=None,
    subtext_font_size=None,
):
    """Returns a PIL 'P' image ready to hand to ptouch-print --image.

    A single `text` line is centered and sized to fill the full label height.
    `text` + `subtext` renders as a bold main line over a smaller detail line
    (matching e.g. "M3x12mm" / "bolts" on existing labels).

    `font_size`/`subtext_font_size` pin the text to an explicit point size
    instead of auto-fitting to this label's own width - use
    `fit_uniform_font_sizes()` to compute one size shared across a batch, so
    labels with different text lengths don't each end up a different size.
    """
    height = tape_height_px(tape_mm)
    width = mm_to_px(length_mm)

    canvas = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(canvas)

    text_x0, max_width, avail_height, icon_img, icon_x, bit_img, bit_x = _layout(icon, width, height)
    if icon_img:
        canvas.paste(icon_img, (icon_x, MARGIN_PX))
    if bit_img:
        canvas.paste(bit_img, (bit_x, (height - bit_img.height) // 2))

    if text and max_width <= 0:
        raise ValueError("icon leaves no room for text at this label length")

    if text and subtext:
        gap, main_budget, sub_budget = _text_budgets(avail_height)
        main_font = (
            ImageFont.truetype(font_path, font_size)
            if font_size
            else _fit_font(draw, [text], font_path, max_width, main_budget)
        )
        sub_font = (
            ImageFont.truetype(subtext_font_path, subtext_font_size)
            if subtext_font_size
            else _fit_font(draw, [subtext], subtext_font_path, max_width, sub_budget)
        )
        _draw_centered_block(
            draw,
            [(text, main_font), (subtext, sub_font)],
            text_x0,
            MARGIN_PX,
            max_width,
            avail_height,
            gaps=[gap],
        )
    elif text:
        lines = text.split("\n")
        max_line_height = avail_height // len(lines)
        font = (
            ImageFont.truetype(font_path, font_size)
            if font_size
            else _fit_font(draw, lines, font_path, max_width, max_line_height)
        )
        _draw_centered_block(
            draw, [(line, font) for line in lines], text_x0, MARGIN_PX, max_width, avail_height
        )

    out = Image.new("P", (width, height))
    out.putpalette([255, 255, 255, 0, 0, 0] + [0, 0, 0] * 254)
    mask = canvas.point(lambda p: 1 if p < 128 else 0)
    out.putdata(list(mask.getdata()))
    return out
