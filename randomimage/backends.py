"""One adapter per image service.

Each backend is a function taking a prompt and returning PNG bytes. They raise
Refused when the service declines to draw -- which happens often enough in this
experiment to be a result in itself, not an error.

Credentials always come from each vendor's own standard mechanism, so no keys
are ever stored in this repo. See the README for how to set each one up.
"""

import base64
import json
import os

# Every backend renders 16:9. The exact pixel counts differ because the three
# APIs express size differently -- see the notes on each function.
ASPECT_RATIO = "16:9"


class Refused(Exception):
    """The service returned no image. Carries the reason it gave."""


def gemini(prompt: str) -> bytes:
    """Google Gemini 3 Pro Image ("Nano Banana Pro") on Vertex AI, ~2752x1536.

    Auth is Application Default Credentials, the standard Google Cloud
    convention. A service account key names its own project; a user credential
    from `gcloud auth application-default login` does not, so we fall back to
    the quota project written into the same file.
    """
    import google.auth
    from google import genai
    from google.genai import types

    credentials, project = google.auth.default()
    project = project or credentials.quota_project_id
    if not project:
        raise Refused(
            "no Google Cloud project found -- run:\n"
            "  gcloud auth application-default set-quota-project YOUR_PROJECT_ID"
        )

    client = genai.Client(
        vertexai=True,
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        project=project,
        credentials=credentials,
    )
    response = client.models.generate_content(
        model=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image"),
        contents=prompt,
        config=types.GenerateContentConfig(
            # Without this the model replies in words instead of pixels.
            response_modalities=["IMAGE"],
            # Sizes here are tiers, not pixel dimensions.
            image_config=types.ImageConfig(aspect_ratio=ASPECT_RATIO, image_size="2K"),
        ),
    )
    candidate = response.candidates[0]
    for part in candidate.content.parts or []:
        if part.inline_data:
            return part.inline_data.data
    raise Refused(f"finish_reason={candidate.finish_reason}")


def openai(prompt: str) -> bytes:
    """OpenAI gpt-image-2, 1344x768.

    Auth is the OPENAI_API_KEY environment variable, which the SDK reads by
    itself. gpt-image-2 accepts any WIDTHxHEIGHT whose edges divide by 16.
    """
    from openai import OpenAI, OpenAIError

    if not os.environ.get("OPENAI_API_KEY"):
        raise Refused("OPENAI_API_KEY is not set")

    try:
        response = OpenAI().images.generate(
            model=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"),
            prompt=prompt,
            size=os.environ.get("OPENAI_IMAGE_SIZE", "1344x768"),
            n=1,
        )
    except OpenAIError as exc:
        raise Refused(str(exc)) from exc

    image = response.data[0]
    if not image.b64_json:
        raise Refused("no image data returned")
    return base64.b64decode(image.b64_json)


def stability(prompt: str) -> bytes:
    """Stable Diffusion 3.5 Large via AWS Bedrock, 1344x768.

    Auth uses boto3's own credential resolution: $AWS_PROFILE if set, otherwise
    the "default" profile, including SSO sessions from ~/.aws/config. Only
    us-west-2 carries the active Stability text-to-image models.
    """
    import boto3

    session = boto3.Session(region_name=os.environ.get("AWS_REGION", "us-west-2"))
    response = session.client("bedrock-runtime").invoke_model(
        modelId=os.environ.get("BEDROCK_IMAGE_MODEL", "stability.sd3-5-large-v1:0"),
        body=json.dumps(
            {
                "prompt": prompt,
                "mode": "text-to-image",
                "aspect_ratio": ASPECT_RATIO,
                "output_format": "png",
            }
        ),
    )
    payload = json.loads(response["body"].read())
    reason = payload.get("finish_reasons", [None])[0]
    if reason is not None:
        raise Refused(str(reason))
    return base64.b64decode(payload["images"][0])


BACKENDS = {"gemini": gemini, "openai": openai, "stability": stability}
