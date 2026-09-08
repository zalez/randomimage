"""Command line entry point."""

import argparse
import sys
from pathlib import Path

from . import __version__, sheet
from .backends import BACKENDS, Refused
from .prompts import GENERATORS


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="randomimage",
        description="Feed random data to an image generator and see what it makes of it.",
        epilog=(
            "examples:\n"
            "  randomimage --backend openai\n"
            "  randomimage --backend gemini --mode int uuid long --count 3 --sheet\n"
            "  randomimage --backend stability --mode rand64 --count 5\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--backend", choices=sorted(BACKENDS), required=True)
    parser.add_argument(
        "--mode",
        nargs="+",
        choices=list(GENERATORS),
        default=["int"],
        help="which kind of random prompt to send; one contact-sheet row per mode",
    )
    parser.add_argument("--count", type=int, default=1, help="images per mode (default 1)")
    parser.add_argument("--out", type=Path, default=Path("images"), help="output directory")
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="extra attempts when the service declines to draw (default 3)",
    )
    parser.add_argument("--sheet", action="store_true", help="also write contact-sheet.png")
    parser.add_argument("--version", action="version", version=f"randomimage {__version__}")
    return parser.parse_args(argv)


def generate_one(backend, mode, out_dir, retries):
    """Return the written path, or None if the service kept refusing."""
    for attempt in range(retries + 1):
        slug, prompt = GENERATORS[mode]()
        try:
            data = BACKENDS[backend](prompt)
        except Refused as exc:
            print(f"  refused ({exc}){' - retrying' if attempt < retries else ''}")
            continue

        path = out_dir / f"{mode}_{slug}.png"
        path.write_bytes(data)
        # Long prompts do not fit in a filename, so keep the full text beside it.
        if slug != prompt:
            path.with_suffix(".txt").write_text(prompt)
        print(f"  {path}")
        return path
    return None


def main(argv=None):
    args = parse_args(argv)
    out_dir = args.out / args.backend
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, refused = [], 0
    for mode in args.mode:
        print(f"{args.backend} / {mode}:")
        row = []
        for _ in range(args.count):
            path = generate_one(args.backend, mode, out_dir, args.retries)
            if path:
                row.append(path)
            else:
                refused += 1
        rows.append(row)

    if args.sheet and any(rows):
        print(f"\nwrote {sheet.build(rows, out_dir / 'contact-sheet.png')}")
    if refused:
        print(f"\n{refused} image(s) never arrived -- the service declined.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
