"""The prompts under test, shared by both backends.

Each generator returns (slug, prompt): the slug names the output file, the
prompt goes to the model. They differ when the prompt is too long or too
sentence-like to be a sane filename.
"""

import hashlib
import random
import string
import uuid


def gen_int():
    n = random.randint(0, 1_000_000_000)
    return str(n), str(n)


def gen_uuid():
    u = str(uuid.uuid4())
    return u, u


def gen_long():
    # 256 chars is far too long to engrave on a plaque, which is where the
    # models keep putting shorter strings. Forces them off that strategy.
    s = "".join(random.choices(string.ascii_letters + string.digits, k=256))
    return f"{s[:16]}-{hashlib.sha1(s.encode()).hexdigest()[:8]}", s


def gen_rand64():
    # Stability's prompt filter reads long high-entropy strings as adversarial
    # and blocks them; the threshold sits between 64 and 128 chars. 64 is the
    # longest meaningless string that reliably gets through.
    s = "".join(random.choices(string.ascii_letters + string.digits, k=64))
    return f"{s[:16]}-{hashlib.sha1(s.encode()).hexdigest()[:8]}", s


def gen_inspired():
    # Explicit licence to invent. Note Gemini reads this as conversation and
    # returns no image at all unless an imperative is added -- see gen_inspired_img.
    n = random.randint(0, 1_000_000_000)
    return str(n), f"Let yourself be inspired by this number: {n}"


def gen_inspired_img():
    n = random.randint(0, 1_000_000_000)
    return str(n), f"Create an image. Let yourself be inspired by this number: {n}"


GENERATORS = {
    "int": gen_int,
    "uuid": gen_uuid,
    "long": gen_long,
    "rand64": gen_rand64,
    "inspired": gen_inspired,
    "inspired_img": gen_inspired_img,
}


def pick(argv):
    """Resolve the mode from argv, returning (mode, slug, prompt)."""
    mode = argv[1] if len(argv) > 1 else "int"
    if mode not in GENERATORS:
        raise SystemExit(f"usage: {argv[0]} [{'|'.join(GENERATORS)}]")
    slug, prompt = GENERATORS[mode]()
    return mode, slug, prompt
