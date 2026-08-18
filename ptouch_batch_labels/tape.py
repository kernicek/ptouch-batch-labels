"""Brother P-touch tape geometry, from the ptouch-print driver's tape_info table
(https://github.com/enachb/ptouch-print/blob/main/src/libptouch.c)."""

DPI = 180
PX_PER_MM = DPI / 25.4

# tape width (mm) -> usable print height (px), out of a 128px head
TAPE_HEIGHT_PX = {
    6: 32,
    9: 52,
    12: 76,
    18: 120,
    24: 128,
    36: 192,
}


def mm_to_px(mm):
    return round(mm * PX_PER_MM)


def tape_height_px(tape_mm):
    try:
        return TAPE_HEIGHT_PX[tape_mm]
    except KeyError:
        raise ValueError(
            f"unsupported tape width {tape_mm}mm, known widths: "
            f"{sorted(TAPE_HEIGHT_PX)}"
        )
