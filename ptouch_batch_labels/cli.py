import argparse
import csv
import subprocess
import sys
from pathlib import Path

from .icons import ICONS
from .render import fit_uniform_font_sizes, render_label


def _slug(text):
    return "".join(c if c.isalnum() else "_" for c in text).strip("_") or "label"


def _print_files(paths, cutmark, final_cut):
    """One ptouch-print invocation for every label, not one per label.
    Each separate invocation re-feeds tape past the print head and cutter,
    so N calls waste tape (and pad every label past its requested length)
    with N times the feed overhead. Chaining --image/--cutmark pairs onto a
    single command line prints them as one continuous job with only real
    cut lines between labels.

    Our patched ptouch-print defaults to feed-without-cut at the end of the
    job (not cutting), so this print run's tape stays attached to the roll
    and the *next* print picks up right where it left off - no wasted
    feed-to-cutter margin between separate invocations either. Only pass
    --final-cut when you actually want to pull the tape free right now."""
    cmd = ["ptouch-print"]
    for p in paths:
        cmd += ["--image", str(p)]
        if cutmark:
            cmd.append("--cutmark")
    if final_cut:
        cmd.append("--final-cut")
    subprocess.run(cmd, check=True)


def cmd_single(args):
    img = render_label(
        text=args.text,
        subtext=args.subtext,
        icon=args.icon,
        bit_size=args.bit_size,
        ref_mm=args.ref_mm,
        thread=args.thread,
        tape_mm=args.tape,
        length_mm=args.length,
    )
    out = Path(args.out or f"{_slug(args.text or args.icon)}.png")
    img.save(out)
    print(f"wrote {out} ({img.width}x{img.height}px)")
    if args.print:
        _print_files([out], args.cutmark, args.final_cut)


def cmd_batch(args):
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with open(args.csv, newline="") as f:
        raw_rows = list(csv.DictReader(f))

    rows = []
    for row in raw_rows:
        rows.append(
            {
                "text": row.get("text") or "",
                "subtext": row.get("subtext") or None,
                "icon": row.get("icon") or None,
                "bit_size": row.get("bit_size") or None,
                "ref_mm": float(row["ref_mm"]) if row.get("ref_mm") else None,
                "thread": row.get("thread") or args.thread,
                "tape": int(row["tape"]) if row.get("tape") else args.tape,
                "length": float(row["length"]) if row.get("length") else args.length,
            }
        )

    # One main-text size (and one subtext size) for the whole batch, so
    # "M3" and "M4x16" don't each auto-fit to a different size.
    main_size, sub_size = fit_uniform_font_sizes(rows)

    out_paths = []
    for i, row in enumerate(rows):
        img = render_label(
            text=row["text"],
            subtext=row["subtext"],
            icon=row["icon"],
            bit_size=row["bit_size"],
            ref_mm=row["ref_mm"],
            thread=row["thread"],
            tape_mm=row["tape"],
            length_mm=row["length"],
            font_size=main_size,
            subtext_font_size=sub_size,
        )
        out = outdir / f"{i:03d}_{_slug(row['text'] or row['icon'])}.png"
        img.save(out)
        print(f"wrote {out} ({img.width}x{img.height}px)")
        out_paths.append(out)

    if args.print:
        _print_files(out_paths, args.cutmark, args.final_cut)


def main():
    p = argparse.ArgumentParser(description="Generate Brother P-touch labels as PNGs for ptouch-print.")
    sub = p.add_subparsers(dest="mode", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tape", type=int, default=12, help="tape width in mm (default: 12)")
    common.add_argument("--length", type=float, default=35, help="label length in mm (default: 35)")
    common.add_argument(
        "--thread",
        choices=["bolt", "screw"],
        default="bolt",
        help="shaft style: 'bolt' (default) - flush shank meant to pair with a nut; 'screw' - thinner core with the thread crests poking out, threads directly into the material",
    )
    common.add_argument("--print", action="store_true", help="pipe each label straight to ptouch-print --image")
    common.add_argument("--cutmark", action="store_true", help="add --cutmark when printing")
    common.add_argument(
        "--final-cut",
        action="store_true",
        help="actually cut the tape free after this print (default: hold it uncut so the next print continues on the same tape with no wasted margin)",
    )

    one = sub.add_parser("single", parents=[common], help="render one label")
    one.add_argument("--text", help="main label text (bold); use \\n for multiple lines if no --subtext")
    one.add_argument("--subtext", help="smaller detail line under --text, e.g. 'bolts' or 'OD9 x t0.8'")
    one.add_argument("--icon", choices=sorted(ICONS), help="icon to draw on the left")
    one.add_argument("--bit-size", help="drive-bit size label under the bit icon, e.g. '3' or 'PH2' (only shown for heads with a bit - see BIT_FOR_HEAD)")
    one.add_argument("--ref-mm", type=float, help="reserve a bottom strip for a measurement line exactly this many mm long, to check a real part against (works up to roughly 30mm)")
    one.add_argument("--out", help="output PNG path")
    one.set_defaults(func=cmd_single)

    batch = sub.add_parser("batch", parents=[common], help="render many labels from a CSV")
    batch.add_argument("csv", help="CSV with columns: text,subtext,icon,bit_size,ref_mm,thread,tape,length (all but text optional; thread/tape/length override --thread/--tape/--length per row)")
    batch.add_argument("--outdir", default="labels_out", help="directory to write PNGs into (default: labels_out)")
    batch.set_defaults(func=cmd_batch)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
