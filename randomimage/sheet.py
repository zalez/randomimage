"""Build a contact sheet: one row per prompt mode, one column per sample."""

from pathlib import Path

CELL_WIDTH = 620
PAD = 8


def build(rows, out_path, cell_width=CELL_WIDTH):
    """rows: list of lists of image paths. Returns the written path."""
    from PIL import Image

    rows = [r for r in rows if r]
    if not rows:
        raise SystemExit("nothing to put on a contact sheet")

    # Keep every cell the same shape, taken from the first image, so rows line
    # up even when backends render at different native sizes.
    with Image.open(rows[0][0]) as probe:
        cell_height = round(cell_width * probe.height / probe.width)

    columns = max(len(r) for r in rows)
    sheet = Image.new(
        "RGB",
        (columns * cell_width + (columns + 1) * PAD, len(rows) * cell_height + (len(rows) + 1) * PAD),
        (24, 24, 26),
    )
    for y, row in enumerate(rows):
        for x, path in enumerate(row):
            with Image.open(path) as im:
                cell = im.convert("RGB").resize((cell_width, cell_height), Image.Resampling.LANCZOS)
            sheet.paste(cell, (PAD + x * (cell_width + PAD), PAD + y * (cell_height + PAD)))

    out_path = Path(out_path)
    sheet.save(out_path)
    return out_path
