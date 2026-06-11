"""Multimodal starters — batch 2: VLM document extraction, video keyframe summarization."""

RECORDS = [
    {
        "slug": "vlm-document-data-extraction",
        "title": "Vision-Model Document Extraction to Validated JSON (Receipts/Invoices)",
        "tldr": "Photo or scan in, validated structured data out. Send the image to a vision model with a Pydantic schema, validate the response, repair once on error, and flag mismatched arithmetic for human review.",
        "category": "multimodal",
        "language": "python",
        "framework": "Anthropic vision + Pydantic",
        "tags": ["vision", "extraction", "pydantic", "structured-output"],
        "best_for_tags": ["document-processing", "invoices-receipts", "structured-extraction"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Turning document images (receipts, invoices, forms) into typed, validated JSON your code can trust. The Pydantic schema plus an arithmetic cross-check catches hallucinated totals instead of silently passing them downstream.",
        "when_not_to_use": "Skip for clean digital PDFs with a text layer (parse the text directly — cheaper). Skip if you only need raw text dump rather than a validated schema.",
        "quick_start": "pip install anthropic pydantic && python extract.py receipt.jpg",
        "full_code": '''"""VLM document extraction: image -> schema-validated Invoice JSON with one repair round."""
from __future__ import annotations

import base64
import json
import os
import sys

from anthropic import Anthropic
from pydantic import BaseModel, Field, ValidationError

# ----------------- CONFIG + SCHEMA -----------------

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
TOLERANCE = 0.02  # currency rounding slack for the arithmetic cross-check

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


class LineItem(BaseModel):
    description: str
    qty: float
    unit_price: float
    total: float


class Invoice(BaseModel):
    vendor: str
    # Force ISO 8601 so downstream date parsing is deterministic.
    date: str = Field(description="Invoice date as ISO 8601, YYYY-MM-DD")
    currency: str = Field(description="ISO 4217 code, e.g. USD")
    line_items: list[LineItem]
    subtotal: float
    tax: float
    total: float


# ----------------- LLM CALL -----------------

def _image_block(path: str) -> dict:
    media = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    data = base64.standard_b64encode(open(path, "rb").read()).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}}


def _call(path: str, repair_note: str = "") -> str:
    schema = json.dumps(Invoice.model_json_schema())
    instruction = (
        "Extract the invoice into JSON matching this schema. "
        "Return ONLY JSON, no markdown fences, no commentary.\\n\\n"
        f"SCHEMA:\\n{schema}"
    )
    if repair_note:
        instruction += f"\\n\\nYour previous output failed validation:\\n{repair_note}\\nFix it."
    resp = client.messages.create(
        model=MODEL, max_tokens=1500,
        messages=[{"role": "user", "content": [_image_block(path), {"type": "text", "text": instruction}]}],
    )
    return resp.content[0].text


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].removeprefix("json").strip()
    return raw


# ----------------- EXTRACT + VALIDATE + CROSS-CHECK -----------------

def extract(path: str) -> dict:
    raw = _strip_fences(_call(path))
    try:
        invoice = Invoice.model_validate_json(raw)
    except ValidationError as err:
        # ONE repair round: hand the validation errors back to the model.
        raw = _strip_fences(_call(path, repair_note=str(err)))
        invoice = Invoice.model_validate_json(raw)

    line_sum = sum(item.total for item in invoice.line_items)
    needs_review = abs(line_sum - invoice.subtotal) > max(TOLERANCE, TOLERANCE * abs(invoice.subtotal))
    return {
        "invoice": invoice.model_dump(),
        "line_item_sum": round(line_sum, 2),
        "needs_review": needs_review,
        "review_reason": "line items do not sum to subtotal" if needs_review else "",
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python extract.py <image-path>")
        raise SystemExit(2)
    try:
        result = extract(sys.argv[1])
    except ValidationError as err:
        print("extraction failed validation after repair:", err)
        raise SystemExit(1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.39", "purpose": "Vision model call with base64 image block"},
            {"name": "pydantic", "version": ">=2.7", "purpose": "Schema definition + JSON validation"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key for the vision call", "example": "sk-ant-..."},
            {"name": "ANTHROPIC_MODEL", "required": False, "description": "Override the vision model id", "example": "claude-sonnet-4-5"},
        ],
        "setup_steps": [
            "pip install anthropic pydantic",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "Save extract.py",
            "Run: python extract.py path/to/receipt.jpg",
            "Inspect needs_review in the output; route flagged docs to a human queue",
        ],
        "variations": [
            {"label": "PDF pages to images", "description": "Render each PDF page and extract per page.", "code_snippet": "import pypdfium2 as pdfium\\npdf = pdfium.PdfDocument('doc.pdf')\\nfor i, page in enumerate(pdf):\\n    page.render(scale=2).to_pil().save(f'page_{i}.png')  # then extract(page_i.png)"},
            {"label": "Local Qwen2.5-VL", "description": "Swap to an OpenAI-compatible local endpoint.", "code_snippet": "from openai import OpenAI\\nclient = OpenAI(base_url='http://localhost:8000/v1', api_key='local')\\n# send image_url content blocks; keep the same schema + validate loop"},
            {"label": "Batch directory mode", "description": "Process a folder, write JSONL + a review queue CSV.", "code_snippet": "import csv, glob, json\\nfor p in glob.glob('inbox/*.jpg'):\\n    r = extract(p)\\n    open('out.jsonl','a').write(json.dumps(r)+'\\n')\\n    # append rows where r['needs_review'] to review.csv"},
        ],
        "common_errors": [
            {"error_text": "json.JSONDecodeError on the response", "cause": "Model wrapped the JSON in markdown fences.", "fix_snippet": "Strip ```json fences before parsing (see _strip_fences); if it still fails, the repair round re-prompts for raw JSON."},
            {"error_text": "Totals look plausible but are wrong", "cause": "Model hallucinated a subtotal that doesn't match the line items.", "fix_snippet": "Cross-check sum(line_items.total) against subtotal within a tolerance and set needs_review; never trust the total blindly."},
            {"error_text": "anthropic.BadRequestError: image too large", "cause": "Image exceeds the API size/dimension limit.", "fix_snippet": "Resize/compress before sending: PIL Image.thumbnail((1568,1568)) and save at JPEG quality ~80."},
            {"error_text": "Dates come back in mixed formats", "cause": "No format constraint, so the model echoes whatever the document shows.", "fix_snippet": "Put 'ISO 8601, YYYY-MM-DD' in the Field description (it lands in the schema) and validate the format if strictness matters."},
        ],
        "production_checklist": [
            "Validate every response with Pydantic; treat unvalidated output as failed.",
            "Cross-check line-item arithmetic and flag mismatches for review.",
            "Resize/compress images under the API limit before sending.",
            "Constrain date and currency formats in the schema descriptions.",
            "Cap repair rounds at one; alert on documents that fail twice.",
            "Log confidence/needs_review so a human queue catches edge cases.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["anthropic==0.39", "pydantic==2.7"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["qwen2-5-vl"],
        "related_glossary_slugs": ["vision-language-model", "structured-output", "json-schema-enforcement", "multimodal", "ocr-llm"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from OCR?", "answer": "OCR gives you raw text and leaves parsing to you. This produces a typed, validated Invoice object with an arithmetic check — the model reads the layout and emits structured fields, so you get data you can act on, not a transcription."},
            {"question": "Why embed the schema in the prompt and still validate?", "answer": "The schema steers the model toward the right shape, but models still drift. Pydantic validation is the hard gate; the embedded schema just raises the first-pass success rate so the repair round fires rarely."},
            {"question": "What does the repair round actually do?", "answer": "On a ValidationError it re-sends the same image plus the exact error text and asks the model to fix its output. One round resolves most format slips (wrong types, missing fields); a second failure is logged for human review instead of looping."},
            {"question": "Can I run this fully locally?", "answer": "Yes — point an OpenAI-compatible client at a local Qwen2.5-VL server and send image_url blocks. Keep the same Pydantic schema and validate/repair loop; only the client and image-block format change."},
        ],
        "github_url": "https://github.com/pydantic/pydantic",
        "meta_title": "VLM Document Extraction to Validated JSON",
        "meta_description": "Receipts and invoices to typed JSON with a vision model: Pydantic validation, one repair round, arithmetic cross-check, human-review flag.",
    },
    {
        "slug": "video-keyframe-summarizer",
        "title": "Video Understanding via Keyframes (ffmpeg Scene Detect + VLM)",
        "tldr": "Most video QA doesn't need a video model — sample the right frames. ffmpeg scene detection pulls keyframes with timestamps, a vision model captions each, and one call merges them into a timeline summary plus an answer.",
        "category": "multimodal",
        "language": "python",
        "framework": "ffmpeg + Anthropic vision",
        "tags": ["video", "ffmpeg", "vision", "summarization"],
        "best_for_tags": ["video-understanding", "scene-detection", "cost-control"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Summarizing or answering questions about a video without a dedicated video model. Scene-based keyframes capture the content at a fraction of frame-by-frame cost, scaling with scene count rather than runtime.",
        "when_not_to_use": "Skip when fine motion or audio is essential (lip-sync, fast action, spoken dialogue) — add a transcript or a true video model. Skip for very short clips where one frame suffices.",
        "quick_start": "pip install anthropic && python summarize_video.py clip.mp4 'What happens?'",
        "full_code": '''"""Keyframe video understanding: ffmpeg scene detect -> caption frames -> merged timeline."""
from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile

from anthropic import Anthropic

# ----------------- CONFIG -----------------

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
SCENE_THRESHOLD = float(os.environ.get("SCENE_THRESHOLD", "0.3"))
MAX_FRAMES = 12

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ----------------- FRAME EXTRACTION -----------------

def extract_keyframes(video: str, out_dir: str) -> list[tuple[float, str]]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH — install it (see setup_steps)")
    pattern = os.path.join(out_dir, "frame_%03d.jpg")
    # select scene-change frames; showinfo prints pts_time to STDERR.
    cmd = [
        "ffmpeg", "-i", video,
        "-vf", f"select='gt(scene,{SCENE_THRESHOLD})',showinfo,scale=768:-1",
        "-vsync", "vfr", pattern, "-hide_banner",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    times = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", proc.stderr)]
    frames = sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".jpg"))

    pairs = list(zip(times, frames))
    if len(pairs) < 3:  # static video: fall back to fixed-interval sampling
        pairs = _interval_sample(video, out_dir)
    if len(pairs) > MAX_FRAMES:  # cap cost: evenly subsample
        step = len(pairs) / MAX_FRAMES
        pairs = [pairs[int(i * step)] for i in range(MAX_FRAMES)]
    return pairs


def _interval_sample(video: str, out_dir: str) -> list[tuple[float, str]]:
    pattern = os.path.join(out_dir, "iv_%03d.jpg")
    subprocess.run(["ffmpeg", "-i", video, "-vf", "fps=1/5,scale=768:-1",
                    pattern, "-hide_banner"], capture_output=True, text=True)
    frames = sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("iv_"))
    return [(i * 5.0, f) for i, f in enumerate(frames)]


# ----------------- CAPTION + MERGE -----------------

def _caption(path: str) -> str:
    data = base64.standard_b64encode(open(path, "rb").read()).decode("ascii")
    resp = client.messages.create(
        model=MODEL, max_tokens=120,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}},
            {"type": "text", "text": "Describe this frame in one short factual sentence."},
        ]}],
    )
    return resp.content[0].text.strip()


def _fmt(ts: float) -> str:
    return f"{int(ts // 60):02d}:{int(ts % 60):02d}"


def summarize(video: str, question: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        pairs = extract_keyframes(video, tmp)
        timeline = [f"{_fmt(ts)} - {_caption(path)}" for ts, path in pairs]
    merge_prompt = (
        "Captions from sampled video frames, in order:\\n" + "\\n".join(timeline) +
        f"\\n\\nWrite a 3-sentence summary, then answer: {question}"
    )
    resp = client.messages.create(
        model=MODEL, max_tokens=600,
        messages=[{"role": "user", "content": merge_prompt}],
    )
    return "TIMELINE:\\n" + "\\n".join(timeline) + "\\n\\n" + resp.content[0].text


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: python summarize_video.py <video> <question>")
        raise SystemExit(2)
    print(summarize(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.39", "purpose": "Vision captioning + text merge calls"},
            {"name": "ffmpeg", "version": ">=6.0", "purpose": "System binary for scene detection + frame export (not a pip package)"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key for captions and merge", "example": "sk-ant-..."},
            {"name": "SCENE_THRESHOLD", "required": False, "description": "ffmpeg scene-change sensitivity (0-1, lower = more frames)", "example": "0.3"},
        ],
        "setup_steps": [
            "pip install anthropic",
            "Install ffmpeg: macOS 'brew install ffmpeg', Debian/Ubuntu 'apt-get install ffmpeg', Windows 'winget install ffmpeg'",
            "Verify: ffmpeg -version (and that it is on PATH)",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "Run: python summarize_video.py clip.mp4 'What happens in this video?'",
        ],
        "variations": [
            {"label": "Add an audio transcript", "description": "Merge Whisper speech with the visual timeline.", "code_snippet": "import whisper\\nsegments = whisper.load_model('base').transcribe('clip.mp4')['segments']\\n# interleave (start, text) with the frame captions by timestamp before the merge call"},
            {"label": "Single multi-image call", "description": "Send all frames in one message for cross-frame reasoning.", "code_snippet": "content = [img_block(p) for _, p in pairs] + [{'type':'text','text':'Summarize across these frames.'}]\\nclient.messages.create(model=MODEL, max_tokens=800, messages=[{'role':'user','content':content}])"},
            {"label": "YouTube input", "description": "Download then process.", "code_snippet": "import yt_dlp\\nyt_dlp.YoutubeDL({'outtmpl':'in.%(ext)s'}).download(['https://youtu.be/ID'])\\n# then summarize('in.mp4', question)"},
        ],
        "common_errors": [
            {"error_text": "FileNotFoundError: 'ffmpeg'", "cause": "ffmpeg is not installed or not on PATH.", "fix_snippet": "Install per-OS (see setup_steps) and guard with shutil.which('ffmpeg') before running, as the code does."},
            {"error_text": "Zero or one keyframe extracted", "cause": "Scene threshold too high for a fairly static video.", "fix_snippet": "Lower SCENE_THRESHOLD, or rely on the built-in interval fallback that samples one frame every 5s when scenes < 3."},
            {"error_text": "Huge bill / slow run on long video", "cause": "No frame cap, so every scene gets its own captioning call.", "fix_snippet": "Keep MAX_FRAMES (subsample beyond it) and downscale frames with scale=768:-1 to cut tokens per image."},
            {"error_text": "Timestamps are empty", "cause": "Parsed pts_time from stdout instead of stderr.", "fix_snippet": "ffmpeg showinfo writes to stderr — capture proc.stderr and regex pts_time from there, not stdout."},
        ],
        "production_checklist": [
            "Guard with shutil.which('ffmpeg') and surface a clear install message.",
            "Cap frames (MAX_FRAMES) and subsample to bound LLM cost.",
            "Downscale frames (scale=768:-1) to reduce tokens per image.",
            "Keep the interval-sampling fallback for low-motion videos.",
            "Parse pts_time from stderr, not stdout.",
            "Add an audio transcript when dialogue carries the meaning.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["anthropic==0.39", "ffmpeg==6.1"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["openai-whisper", "faster-whisper"],
        "related_glossary_slugs": ["video-llm", "multimodal", "vision-language-model", "multimodal-embedding"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why keyframes instead of a video model?", "answer": "A 10-minute clip is ~18,000 frames; scene detection might surface 8-20 meaningful ones. Captioning those costs a fraction of a video model and runs on any vision model, while still capturing what changed on screen."},
            {"question": "When does this approach break down?", "answer": "When the signal is between frames: fast motion, precise timing, or spoken dialogue. Add a Whisper transcript for speech, or switch to a true video model when sub-second visual continuity matters."},
            {"question": "Per-frame captions vs one multi-image call?", "answer": "Per-frame is cheaper and parallelizable and keeps each caption focused. A single multi-image call reasons across frames (e.g. 'the person who entered at 00:10 leaves at 01:20') but costs more tokens; pick by whether cross-frame reasoning is needed."},
            {"question": "How do I keep cost predictable?", "answer": "Two levers: MAX_FRAMES caps how many images you ever caption, and scale=768:-1 shrinks each image's token cost. Cost then scales with scene count up to the cap, independent of video length."},
        ],
        "github_url": "https://github.com/anthropics/anthropic-sdk-python",
        "meta_title": "Video Keyframe Summarizer (ffmpeg + VLM)",
        "meta_description": "Summarize and query video without a video model: ffmpeg scene-detect keyframes, vision captions, one merge call. Cost scales with scenes.",
    },
]
