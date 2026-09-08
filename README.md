# I wonder what happens if we feed random data to an image generator?

No adjectives. No scene. No style. Just a random number, a UUID, or 256
characters of noise, handed to a state-of-the-art image model.

Years ago, doing this to Amazon's Titan Image Generator produced glorious
nonsense — the model couldn't read the string, so it drew something arbitrary.
Modern image models have a language model bolted to the front. Does that change
what happens?

It does. Here is what nine images from each of three services look like.

---

## The short answer

The three services fail in three completely different ways.

| | Google Gemini 3 Pro Image | OpenAI gpt-image-2 | Stable Diffusion 3.5 Large |
|---|---|---|---|
| **Reads the string?** | Yes — 36 characters, perfectly | Yes | No, never |
| **Interprets it?** | Compulsively | Sometimes, as documentation | Not at all |
| **Typical output** | An invented object carrying the string | A spec sheet *or* a stock landscape | An arbitrary photograph |
| **Visual variety** | Narrow — one house style | Bimodal, nothing between | Wide — nothing in common |
| **Fails by** | Comprehension breaking down | — | A guardrail firing first |

Only Stable Diffusion behaves the way Titan used to. The two models with a
language front-end cannot stop trying to make sense of the input — and they
reach for opposite strategies to do it. Gemini **narrativises**. OpenAI
**documents**.

---

## What we tested

Three prompt types, three samples each, per service:

| Mode | Prompt | Why |
|---|---|---|
| `int` | `763530653` | Short. Meaningless, but still parseable as a quantity. |
| `uuid` | `354974e2-1bc6-41a5-a432-e834ac716cef` | Longer, structured, obviously an identifier. |
| `long` | 256 random letters and digits | Too long to fit on a sign. Breaks the "put it on a label" strategy. |

Everything renders 16:9. Gemini outputs 2752×1536 (its API takes size *tiers*,
not pixels); the other two output 1344×768.

---

## Google Gemini 3 Pro Image

![Gemini contact sheet](images/gemini/contact-sheet.jpg)

*Rows: integers, UUIDs, 256-char strings.*

**It always finds something to write the string on.** A brass house number on a
door. A plaque screwed to a weathered gate. An antique key with the digits
stamped into the shaft. A UUID embroidered on a hoodie sleeve; another engraved
on a skeleton clock.

**And it renders the text perfectly.** We cropped and checked: the 36-character
UUID `354974e2-1bc6-41a5-a432-e834ac716cef` is exact, hyphens and all. So is
the one that wrapped across two lines on the hoodie. Diffusion models smear long
strings; reproducing 36 characters means holding the string *symbolically*.

**There is a house style, and it is oddly specific.** Across the first six
images: wood in 6 of 6, aged brass in 5 of 6, warm amber palette in 6 of 6,
shallow depth of field in 6 of 6. Never a screen, a receipt, a barcode or a
licence plate — all far more common homes for a nine-digit number than a
Victorian clock. Nothing about `809164269` implies patina. That is raw
weight-prior, not interpretation.

**At 256 characters it breaks.** The antique look vanishes and is replaced by
green terminals and circuit boards — the string now reads as *code*, not as an
identifier. Transcription holds for roughly the first 70 characters, then
decays: a duplicated `3x`, a dropped `u`, and eventually a 7-character run
(`ETRvWVu`) simply missing. Half of all attempts at this length returned
`finish_reason=NO_IMAGE` — a flat refusal that never happened at 9 or 36
characters.

**One image ignored the prompt entirely** and produced a sunrise mountain lake
with a red canoe. No text, no connection, nothing. What that means is genuinely
unclear — see [Open questions](#open-questions).

### Bonus: asking it to hallucinate

We tried `Let yourself be inspired by this number: <n>`, expecting free
invention. We got **zero images, nine times in a row**. The phrasing reads as
conversation, so the model wants to *talk about* the number; with the API
restricted to image output it has nothing it is allowed to emit.

What it says instead is the most revealing thing in this repo. Unprompted, it
offered `931360149` as a Unix timestamp — "Wednesday, July 7, 1999, 15:09:09
UTC" — and factored `309324004` into `2² × 11 × 7,030,091`. **Both are exactly
correct**, weekday included, and 7,030,091 really is prime. Given licence to
invent, it did verified number theory instead.

Adding `Create an image.` restores the pictures, and finally breaks the antique
attractor:

![Gemini inspired sheet](images/gemini/inspired-sheet.jpg)

The first one is the single best artifact we produced. For `186561909` the model
**split the digits** — `1865` and `1909` — read them as a date range, and built
a genealogy office around it: ledger, pocket watch, family portrait, a plaque
reading "EST. 1865 – 1909". Then it hung a September 1909 calendar on the wall,
and the weekday grid is historically correct. September 1909 did begin on a
Wednesday.

---

## OpenAI gpt-image-2

![OpenAI contact sheet](images/openai/contact-sheet.jpg)

*Rows: integers, UUIDs, 256-char strings.*

**It is bimodal, with no middle ground.** Either the string is treated as pure
typography or technical content with no scene at all, or it is ignored
completely in favour of a stock landscape. Gemini's move — embedding the string
inside an invented world — never happens here.

Two of three integers came back as **black digits on plain white**. The third
was a sunset lake with no text. Two of three UUIDs were a puppy and an alpine
village, with no string anywhere.

**And then there is the third UUID.** It rendered an **RFC 4122 field diagram**:
the UUID split into `time_low` / `time_mid` / `time_hi_and_version` /
clock-sequence / node, each group colour-coded, annotated with Version 4
(random), Variant RFC 4122, Format UUID.

We checked it. The version and variant are **correct** — parsing `aa` as binary
`10101010` to identify the RFC 4122 variant is real work. But it labelled `aa83`
as `clock_seq_hi_and_reserved`, which is actually two fields, and called the
node `clock_seq_low_and_node`.

That is the only factual error any model made in this entire experiment. It got
the hard bit-level parsing right and fumbled the easy field boundaries — real
knowledge, imperfectly recalled.

**No content filter.** All three 256-character prompts went straight through.

---

## Stable Diffusion 3.5 Large

![Stability contact sheet](images/stability/contact-sheet.jpg)

*Rows: integers, UUIDs, 64-char strings (see below).*

**This is the control the experiment needed.** Nine images: a coastal stone
gateway, a container ship, ranks of hard-hatted workers, men in suits on a
hillside, two women leaping over water, a golden robotic bee in a snowy forest.

**Not one contains text. Not one relates to its prompt.** Integers and UUIDs are
indistinguishable in the output, which is the tell — neither carries meaning the
model can reach. The string lands at an arbitrary point in conditioning space
and the model renders whatever lives there.

Note what "random" actually looks like: not noise, but perfectly coherent,
well-composed photographs *of nothing in particular*.

**The 256-character row is missing, and the reason is interesting.** All three
attempts — and ten retries — were rejected with `Filter reason: prompt`. A
content filter, not a model refusal. Since "long" and "random" were confounded,
we ran a ladder:

| Prompt | Result |
|---|---|
| 32 random chars | passes |
| 64 random chars | passes |
| **128 random chars** | **blocked** |
| 256 random chars | blocked |
| **211 chars of English prose** | **passes** |

So it keys on **entropy, not length** — a long high-entropy string looks like a
jailbreak attempt. The threshold sits between 64 and 128 characters, which is
why this repo has a `rand64` mode.

Both Gemini and Stable Diffusion return nothing at 256 characters, for
completely unrelated reasons: Gemini's *comprehension* degrades, while Stable
Diffusion's *guardrail* fires before the model ever sees the string.

---

## Run it yourself

Requires [uv](https://docs.astral.sh/uv/) and credentials for whichever service
you want to use. No keys are ever stored in this repo — each backend uses its
vendor's own standard mechanism.

```bash
git clone https://github.com/zalez/randomimage.git
cd randomimage
uv run randomimage --backend openai
```

Reproduce a full 3×3 with a contact sheet:

```bash
uv run randomimage --backend gemini --mode int uuid long --count 3 --sheet
```

Images land in `images/<backend>/`, one row per mode on the sheet.

```
--backend  gemini | openai | stability          (required)
--mode     int | uuid | long | rand64 | inspired | inspired_img
--count    images per mode                      (default 1)
--out      output directory                     (default images/)
--retries  extra attempts when a service declines to draw (default 3)
--sheet    also write contact-sheet.png
```

Services decline fairly often in this experiment, so `--retries` is on by
default. A refusal prints the reason the service gave.

### Credentials

**OpenAI** — the SDK reads `OPENAI_API_KEY` by itself. Create a key at
[platform.openai.com/api-keys](https://platform.openai.com/api-keys). In fish:

```fish
set -Ux OPENAI_API_KEY sk-...
```

(`-U` persists it across shells and reboots; `-x` exports it so the SDK can see
it. In bash or zsh, add `export OPENAI_API_KEY=sk-...` to your shell profile.)

**Google** — Application Default Credentials, and a Google Cloud project with
billing and the Vertex AI API enabled:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

The second command matters: user credentials are tied to a person, not a
project, so without it the SDK has no project to bill. A service account key
dropped at `~/.config/gcloud/application_default_credentials.json` works too and
skips that step, because a key names its own project.

**Stability via AWS Bedrock** — a named AWS profile with Bedrock access, and
model access granted for Stable Diffusion in **us-west-2** (other regions do not
carry it):

```bash
export AWS_PROFILE=your-profile   # defaults to "personal"
```

Every model choice, region and size can be overridden by environment variable —
see the docstrings in [`randomimage/backends.py`](randomimage/backends.py).

---

## Layout

```
randomimage/
  cli.py        argument parsing, retry loop
  backends.py   one adapter per service, ~30 lines each
  prompts.py    the random prompt generators
  sheet.py      contact sheet builder
images/
  gemini/       9 images + contact sheet + the "inspired" bonus run
  openai/       9 images + contact sheet
  stability/    9 images + contact sheet
```

Prompts longer than a filename are saved as a `.txt` beside their image, so
every result can be traced back to its exact input.

---

## Open questions

**Sample size is three.** Everything here is an observation, not a measurement.
The three behaviours we saw from Gemini at 256 characters appeared under
identical settings, so they are *sampled*, not deterministic — telling those
apart properly needs 20–30 runs per condition, not three.

**What happened with the canoe?** One 256-character prompt produced a serene
mountain lake with no text and no discernible link to the input. "The model gave
up" is the easy explanation and probably the wrong one — this is a model that
writes 900 unprompted words about an eight-digit number. Something produced that
image. The way to find out is to request text *and* image together and read what
it says while it draws.

**Why brass and wood?** The aesthetic convergence is the least explained result
here. It is not interpretation — nothing about a random integer implies patina.

---

## Prior art that no longer exists

This started as an attempt to reproduce old Amazon Titan Image Generator
behaviour. That is no longer possible: Titan Image Generator v1 and v2 are
end-of-life on Bedrock, and its successor Nova Canvas is marked LEGACY and
refuses invocation. Stable Diffusion 3.5 Large stands in as the diffusion-model
control — a different and more capable model, which makes it more striking, not
less, that it never read a single string.

---

## Licence

MIT — see [LICENSE](LICENSE).
