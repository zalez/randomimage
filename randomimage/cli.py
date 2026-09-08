"""Command line entry point."""

import argparse
import hashlib
import sys
import time
from pathlib import Path
from uuid import uuid4

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
    parser.add_argument(
        "--prompt",
        help="send this exact text instead of a generated one; --mode is ignored",
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


def generate_one(backend, mode, out_dir, retries, fixed_prompt=None):
    """Return the written path, or None if every attempt came back empty."""
    backoff = 5
    for attempt in range(retries + 1):
        if fixed_prompt is None:
            slug, prompt = GENERATORS[mode]()
        else:
            # Same prompt every time, so make the filename unique by attempt.
            prompt = fixed_prompt
            slug = f"{hashlib.sha1(prompt.encode()).hexdigest()[:8]}-{uuid4().hex[:4]}"
        try:
            data = BACKENDS[backend](prompt)
        except Refused as exc:
            reason = f"refused ({exc})"
        except Exception as exc:  # noqa: BLE001 - rate limits and transient API errors
            # Quota exhaustion is common when running a series, and it is
            # transient, so it should cost an attempt rather than the run.
            reason = f"{type(exc).__name__}: {str(exc).splitlines()[0][:100]}"
        else:
            path = out_dir / f"{mode}_{slug}.png"
            path.write_bytes(data)
            # Long prompts do not fit in a filename, so keep the full text beside it.
            if slug != prompt:
                path.with_suffix(".txt").write_text(prompt)
            print(f"  {path}")
            return path

        print(f"  {reason}{' - retrying' if attempt < retries else ''}")
        if attempt < retries:
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
        continue
    return None


def main(argv=None):
    args = parse_args(argv)
    out_dir = args.out / args.backend
    out_dir.mkdir(parents=True, exist_ok=True)

    modes = ["custom"] if args.prompt else args.mode
    rows, refused = [], 0
    for mode in modes:
        print(f"{args.backend} / {mode}:")
        row = []
        for _ in range(args.count):
            path = generate_one(args.backend, mode, out_dir, args.retries, args.prompt)
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
