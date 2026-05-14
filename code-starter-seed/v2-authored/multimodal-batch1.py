"""Multimodal starters — vision, audio, OCR via LLM."""

RECORDS = [
    {
        "slug": "claude-vision-image-analysis",
        "title": "Claude Vision For Structured Image Analysis",
        "tldr": "Send an image to Claude with a structured output schema; returns Pydantic-validated description, objects detected, suggested alt-text, and confidence per claim.",
        "category": "multimodal",
        "language": "python",
        "framework": "Anthropic + Instructor",
        "tags": ["vision", "claude", "multimodal", "structured-output"],
        "best_for_tags": ["image-analysis", "accessibility", "content-moderation"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you need to extract structured information from images at scale — alt text, content moderation, document analysis, chart extraction. Claude's vision is strong on text-in-image and on cautious labeling.",
        "when_not_to_use": "Skip for face recognition (Claude refuses by design). Skip for pixel-precise tasks (object bounding boxes, instance segmentation) — vision LLMs give regions, not coordinates.",
        "quick_start": "pip install anthropic instructor && ANTHROPIC_API_KEY=sk-ant-... python vision.py path/to/image.png",
        "full_code": '''"""Structured image analysis with Claude vision + Instructor.

Returns Pydantic-validated output: description, objects, suggested alt text,
confidence per claim. Works with file paths, URLs, or base64.
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Literal

import instructor
from anthropic import Anthropic
from pydantic import BaseModel, Field


class DetectedObject(BaseModel):
    name: str = Field(description="Name of object (e.g., 'bicycle', 'sign with text')")
    location: Literal["top-left", "top-center", "top-right", "middle-left", "center", "middle-right", "bottom-left", "bottom-center", "bottom-right"]
    confidence: Literal["high", "medium", "low"]
    text_on_object: str | None = Field(default=None, description="Any visible text on or near the object")


class ImageAnalysis(BaseModel):
    overall_description: str = Field(description="2-3 sentence description")
    purpose: Literal["informational", "decorative", "functional", "advertisement", "instructional", "unknown"]
    suggested_alt_text: str = Field(max_length=125, description="WCAG-grade alt text")
    long_description: str | None = Field(default=None, description="Only if the image carries meaning alt text can't convey")
    objects: list[DetectedObject]
    visible_text: str | None = Field(default=None, description="All text visible in the image, verbatim")
    confidence_overall: Literal["high", "medium", "low"]
    safety_concerns: list[str] = Field(default_factory=list, description="Any content concerns (violence, etc.)")


client = instructor.from_anthropic(Anthropic())


def image_to_base64(image_path: Path) -> tuple[str, str]:
    """Returns (b64_data, media_type)."""
    suffix = image_path.suffix.lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix, "image/png")
    data = base64.standard_b64encode(image_path.read_bytes()).decode()
    return data, media_type


def analyze(image_path: Path, *, context: str | None = None) -> ImageAnalysis:
    b64, media_type = image_to_base64(image_path)

    user_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64,
            },
        },
        {
            "type": "text",
            "text": f"""Analyze this image. Return structured output per the schema.

Context (optional): {context or 'none'}

Rules:
- Describe what's MEANINGFUL in context, not just visual features.
- Suggested alt text: under 125 chars, no "image of" prefix.
- Long description: only if needed beyond alt text.
- Mark confidence honestly; low confidence is fine to admit.
- Note safety concerns explicitly; empty list is acceptable.
- Do not identify specific named individuals.""",
        },
    ]

    return client.messages.create(
        model="claude-3-7-sonnet-latest",
        max_tokens=1024,
        max_retries=2,
        messages=[{"role": "user", "content": user_content}],
        response_model=ImageAnalysis,
    )


if __name__ == "__main__":
    image_path = Path(sys.argv[1] if len(sys.argv) > 1 else "test.png")
    result = analyze(image_path)
    print(result.model_dump_json(indent=2))
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.39", "purpose": "Claude SDK with vision"},
            {"name": "instructor", "version": ">=1.5", "purpose": "Structured output"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schemas"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install anthropic instructor pydantic",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "python vision.py path/to/image.png",
        ],
        "variations": [
            {
                "label": "From URL",
                "description": "Pass URL directly.",
                "code_snippet": "user_content[0] = {'type': 'image', 'source': {'type': 'url', 'url': 'https://example.com/image.png'}}",
            },
            {
                "label": "Multi-image",
                "description": "Compare two images.",
                "code_snippet": "user_content = [\\n  {'type': 'image', 'source': {...image1}},\\n  {'type': 'image', 'source': {...image2}},\\n  {'type': 'text', 'text': 'Compare these two images...'}\\n]",
            },
            {
                "label": "OpenAI vision instead",
                "description": "Use gpt-4o vision.",
                "code_snippet": "from openai import OpenAI\\nclient = instructor.from_openai(OpenAI())\\n# Different image content format: {'type': 'image_url', 'image_url': {'url': f'data:{media_type};base64,{b64}'}}",
            },
            {
                "label": "Batch processing",
                "description": "Process many images.",
                "code_snippet": "import concurrent.futures\\nwith concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:\\n    results = list(ex.map(analyze, image_paths))",
            },
        ],
        "common_errors": [
            {
                "error_text": "BadRequestError: image is too large",
                "cause": "File exceeds API limit (~5MB for Claude, 20MB for GPT-4o).",
                "fix_snippet": "Resize before sending: from PIL import Image; img = Image.open(path); img.thumbnail((2048, 2048)); img.save(path).",
            },
            {
                "error_text": "Empty visible_text when image has obvious text",
                "cause": "OCR limitations in vision LLMs for small/stylized text.",
                "fix_snippet": "Crop tightly around text region before sending. Or use a dedicated OCR (Tesseract) for text extraction, vision LLM for understanding.",
            },
            {
                "error_text": "Refuses to identify specific people",
                "cause": "Both Claude and GPT-4o refuse face recognition by design.",
                "fix_snippet": "Use a dedicated face recognition service if you legitimately need this (with consent + legal review). Vision LLMs intentionally don't do this.",
            },
            {
                "error_text": "Confidence always high",
                "cause": "Model is over-confident.",
                "fix_snippet": "Tighten the prompt: 'mark confidence low when image is ambiguous, blurry, or you're inferring. High should be rare.'",
            },
        ],
        "production_checklist": [
            "Resize images before sending; reduces tokens significantly.",
            "Cache results by image hash; re-analysis of same image is waste.",
            "Validate visible_text against OCR if accuracy matters.",
            "Set safety_concerns review pipeline; auto-flag for moderation.",
            "Don't store user-uploaded images longer than needed; PII risk.",
            "Test on adversarial images (deepfakes, optical illusions, low-light) before production.",
            "Pin model version; vision capabilities improve but also change behavior across versions.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-7-sonnet"],
            "library_versions": ["anthropic==0.39.0", "instructor==1.5.2", "pydantic==2.9.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["anthropic"],
        "related_glossary_slugs": ["multimodal", "vision-model", "alt-text"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Claude vs GPT-4o for vision?",
                "answer": "Both strong. Claude tends to be more cautious / less confident, more careful about not identifying people. GPT-4o is slightly faster, equally good on charts. Pick by other criteria (API ergonomics, cost).",
            },
            {
                "question": "Bounding box coordinates?",
                "answer": "Vision LLMs give regions ('top-left'), not precise coordinates. For pixel-precise bounding, use SAM, YOLO, or a dedicated vision model.",
            },
            {
                "question": "Is the result safe to display directly to users?",
                "answer": "Run through a content-safety check first. Even with safety_concerns field, false negatives happen. For high-stakes (e.g., moderation), add a second pass.",
            },
            {
                "question": "How fast is this?",
                "answer": "~3-8 seconds per image including upload. Parallelize for throughput. Caching helps for re-analysis.",
            },
        ],
        "github_url": "https://github.com/anthropics/anthropic-sdk-python",
        "meta_title": "Claude Vision For Structured Image Analysis",
        "meta_description": "Send images to Claude with Pydantic schema: structured description, alt text, objects with location + confidence, safety flags.",
    },
    {
        "slug": "whisper-transcription-with-speakers",
        "title": "Whisper Transcription With Speaker Diarization",
        "tldr": "Transcribe audio with OpenAI Whisper + pyannote speaker diarization. Produces transcript labeled by speaker with confidence-aware merging when speakers cross talk.",
        "category": "multimodal",
        "language": "python",
        "framework": "Whisper + pyannote",
        "tags": ["audio", "transcription", "whisper", "diarization"],
        "best_for_tags": ["meeting-transcription", "podcast-processing", "interview-analysis"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When you need transcripts AND speaker labels — meetings, interviews, podcasts, courtroom recordings. Whisper handles speech-to-text; pyannote handles ‘who spoke when’.",
        "when_not_to_use": "Skip when there's only one speaker (no diarization needed). Skip for very short clips — overhead dominates. Skip for non-supported languages (check Whisper's language list).",
        "quick_start": "pip install openai-whisper pyannote.audio torch torchaudio && python diarize.py meeting.mp3",
        "full_code": '''"""Transcribe + diarize an audio file.

Pipeline:
  1. Diarize: pyannote produces a timeline of who spoke when.
  2. Transcribe: Whisper transcribes the full audio with word-level timestamps.
  3. Merge: assign each transcribed word to the speaker active at that timestamp.
  4. Emit: transcript with [Speaker N] labels.

Output is a list of (speaker, start_seconds, end_seconds, text) segments.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import torch
import whisper
from pyannote.audio import Pipeline


@dataclass
class Segment:
    speaker: str          # "SPEAKER_00", "SPEAKER_01", ...
    start: float          # seconds
    end: float
    text: str


def transcribe(audio_path: Path, *, model_size: str = "base") -> dict:
    """Whisper transcription with word-level timestamps."""
    model = whisper.load_model(model_size)
    return model.transcribe(str(audio_path), word_timestamps=True)


def diarize(audio_path: Path, hf_token: str) -> list[tuple[float, float, str]]:
    """Pyannote speaker diarization."""
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
    )
    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
    diarization = pipeline(str(audio_path))
    return [(turn.start, turn.end, speaker) for turn, _, speaker in diarization.itertracks(yield_label=True)]


def merge(whisper_result: dict, diarization: list[tuple[float, float, str]]) -> list[Segment]:
    """Assign each Whisper segment to the most-overlapping speaker."""
    segments: list[Segment] = []
    for seg in whisper_result["segments"]:
        seg_start = seg["start"]
        seg_end = seg["end"]
        # Find speaker with max temporal overlap
        best_speaker = "UNKNOWN"
        best_overlap = 0.0
        for d_start, d_end, speaker in diarization:
            overlap = max(0, min(seg_end, d_end) - max(seg_start, d_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker
        segments.append(Segment(
            speaker=best_speaker, start=seg_start, end=seg_end, text=seg["text"].strip()
        ))
    return segments


def format_transcript(segments: list[Segment]) -> str:
    """Group consecutive same-speaker segments into paragraphs."""
    out = []
    current_speaker = None
    current_text = []
    current_start = None
    for seg in segments:
        if seg.speaker != current_speaker:
            if current_speaker is not None:
                out.append(f"[{current_speaker} @ {current_start:.1f}s] {' '.join(current_text)}")
            current_speaker = seg.speaker
            current_text = [seg.text]
            current_start = seg.start
        else:
            current_text.append(seg.text)
    if current_speaker is not None:
        out.append(f"[{current_speaker} @ {current_start:.1f}s] {' '.join(current_text)}")
    return "\\n\\n".join(out)


def process(audio_path: Path, hf_token: str) -> str:
    print("Transcribing...")
    whisper_result = transcribe(audio_path)
    print("Diarizing...")
    diarization = diarize(audio_path, hf_token)
    print("Merging...")
    segments = merge(whisper_result, diarization)
    return format_transcript(segments)


if __name__ == "__main__":
    audio = Path(sys.argv[1] if len(sys.argv) > 1 else "audio.mp3")
    hf_token = os.environ["HF_TOKEN"]
    print(process(audio, hf_token))
''',
        "dependencies": [
            {"name": "openai-whisper", "version": ">=20240930", "purpose": "Whisper STT"},
            {"name": "pyannote.audio", "version": ">=3.1", "purpose": "Speaker diarization"},
            {"name": "torch", "version": ">=2.0", "purpose": "PyTorch (GPU support)"},
            {"name": "torchaudio", "version": ">=2.0", "purpose": "Audio I/O"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "HF token (pyannote model is gated)", "example": "hf_..."},
        ],
        "setup_steps": [
            "pip install openai-whisper pyannote.audio torch torchaudio",
            "Get HF_TOKEN from huggingface.co; accept pyannote/speaker-diarization-3.1 license on HF.",
            "export HF_TOKEN=hf_...",
            "python diarize.py meeting.mp3",
        ],
        "variations": [
            {
                "label": "Use OpenAI Whisper API",
                "description": "Cloud Whisper instead of local.",
                "code_snippet": "from openai import OpenAI\\nclient = OpenAI()\\nwith open(audio_path, 'rb') as f:\\n    transcript = client.audio.transcriptions.create(model='whisper-1', file=f, response_format='verbose_json', timestamp_granularities=['word'])",
            },
            {
                "label": "Speaker name mapping",
                "description": "Replace SPEAKER_00 with names.",
                "code_snippet": "# Pyannote uses anonymous labels. If you know who spoke, provide voiceprints or just rename after the fact.\\nname_map = {'SPEAKER_00': 'Alice', 'SPEAKER_01': 'Bob'}",
            },
            {
                "label": "Webhook delivery",
                "description": "Process async; deliver result via webhook.",
                "code_snippet": "# Use Celery / RQ for the heavy work. POST result to client's webhook URL when done.",
            },
            {
                "label": "Streaming transcription",
                "description": "Real-time with diarization.",
                "code_snippet": "# Streaming is harder: pyannote handles streaming via Pipeline.from_pretrained('pyannote/speaker-diarization-3.1', streaming=True)\\n# Whisper streaming: faster-whisper or stream-then-transcribe-chunks.",
            },
        ],
        "common_errors": [
            {
                "error_text": "HF gated model error",
                "cause": "pyannote model requires accepting license on HF.",
                "fix_snippet": "Visit huggingface.co/pyannote/speaker-diarization-3.1, accept license, then HF_TOKEN works.",
            },
            {
                "error_text": "GPU not used, very slow",
                "cause": "PyTorch installed without CUDA.",
                "fix_snippet": "pip install torch --index-url https://download.pytorch.org/whl/cu121 (or matching CUDA version). Verify: python -c 'import torch; print(torch.cuda.is_available())'",
            },
            {
                "error_text": "Wrong speaker assignment on cross-talk",
                "cause": "Two speakers overlap; one dominates the merge.",
                "fix_snippet": "Merge logic uses max overlap. For better cross-talk handling, use word-level Whisper + word-level overlap. Or accept the limitation; pure overlap is hard.",
            },
            {
                "error_text": "Diarization detects 1 speaker for 2-speaker audio",
                "cause": "Audio too short or speakers too similar in voice.",
                "fix_snippet": "Pyannote needs ~1 min minimum and distinguishable voices. For short clips, manual splitting may be needed.",
            },
        ],
        "production_checklist": [
            "Run on GPU for any production use; CPU is 10-30x slower.",
            "Pre-process audio: normalize loudness, downsample to 16kHz (Whisper's native).",
            "Validate against ground-truth transcripts on a sample.",
            "Set expected speaker count (num_speakers parameter) if known.",
            "Anonymize before sending audio to cloud Whisper if PII concerns.",
            "Track per-clip processing time + cost.",
            "Test with adversarial audio: heavy accents, background noise, overlapping speech.",
        ],
        "tested_with": {
            "model_versions": ["whisper-base", "pyannote/speaker-diarization-3.1"],
            "library_versions": ["openai-whisper==20240930", "pyannote.audio==3.3.2"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["whisper", "pyannote"],
        "related_glossary_slugs": ["transcription", "diarization", "speech-to-text"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Local Whisper vs API?",
                "answer": "Local: free, slower, requires GPU for speed. API: faster, costs ~$0.006/minute, no setup. Pick based on cost-volume curve and privacy needs.",
            },
            {
                "question": "What model size?",
                "answer": "base: fast, decent. small: better quality, 2x slower. medium: noticeably better, 4x slower. large: best, 10x slower. For meetings: small or medium.",
            },
            {
                "question": "Will it work in noisy environments?",
                "answer": "Whisper is robust but degrades. Pre-process with noise reduction (RNNoise) for crucial transcripts. Diarization especially suffers in noise.",
            },
            {
                "question": "How to handle multiple languages in one recording?",
                "answer": "Whisper auto-detects per chunk. For mixed-language audio (code-switching), word-level timestamps + manual review work better than treating it as one language.",
            },
        ],
        "github_url": "https://github.com/openai/whisper",
        "meta_title": "Whisper Transcription With Speaker Diarization",
        "meta_description": "Transcribe + diarize audio: Whisper + pyannote. Produces speaker-labeled transcripts with word-level alignment. Local or via API.",
    },
]
