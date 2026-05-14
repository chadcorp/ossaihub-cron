"""Fine-tuning starters — OpenAI FT, LoRA with PEFT."""

RECORDS = [
    {
        "slug": "openai-fine-tune-pipeline",
        "title": "OpenAI Fine-Tune End-to-End Pipeline",
        "tldr": "Complete OpenAI fine-tune workflow: prepare JSONL training data, validate format, upload, kick off job, poll completion, evaluate the resulting model. With cost estimate before commit.",
        "category": "fine-tuning",
        "language": "python",
        "framework": "OpenAI SDK",
        "tags": ["fine-tuning", "openai", "training", "evaluation"],
        "best_for_tags": ["domain-specialization", "format-compliance", "tone-matching"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When prompt engineering hits a ceiling on a narrow task — formatting compliance, brand voice, specialized classification. Fine-tuning works best where you have 50-500 high-quality examples of the desired behavior.",
        "when_not_to_use": "Skip when RAG would solve it (you need the model to know facts, not behave differently). Skip when you have <50 examples; tune the prompt instead. Skip if cost matters more than 5-10% quality improvement.",
        "quick_start": "pip install openai && OPENAI_API_KEY=sk-... python tune.py prepare data.csv && python tune.py train",
        "full_code": '''"""OpenAI fine-tuning end-to-end.

Steps:
  1. prepare: convert CSV/JSONL to OpenAI training format.
  2. validate: check format, warn on issues, estimate cost.
  3. upload: upload training (and optional validation) file.
  4. train: kick off fine-tune job.
  5. poll: wait for completion; show progress.
  6. evaluate: run held-out test cases through both base and fine-tuned model.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import tiktoken
from openai import OpenAI

client = OpenAI()
enc = tiktoken.encoding_for_model("gpt-4o-mini")

BASE_MODEL = "gpt-4o-mini-2024-07-18"  # currently supports fine-tuning
COST_PER_M_TRAINING_TOKEN = 3.00       # USD (approximate; check OpenAI's pricing page)


# ----------------- 1. PREPARE -----------------

def prepare_from_csv(csv_path: Path, jsonl_path: Path) -> None:
    """CSV columns: system, user, assistant.

    Outputs JSONL with one {messages: [...]} per row.
    """
    import csv

    with csv_path.open() as fin, jsonl_path.open("w") as fout:
        reader = csv.DictReader(fin)
        for row in reader:
            example = {
                "messages": [
                    {"role": "system", "content": row["system"]},
                    {"role": "user", "content": row["user"]},
                    {"role": "assistant", "content": row["assistant"]},
                ]
            }
            fout.write(json.dumps(example) + "\\n")


# ----------------- 2. VALIDATE -----------------

def validate(jsonl_path: Path) -> dict:
    """Check format, count tokens, estimate cost."""
    issues = []
    total_tokens = 0
    n_examples = 0

    with jsonl_path.open() as f:
        for i, line in enumerate(f, 1):
            try:
                ex = json.loads(line)
            except json.JSONDecodeError as e:
                issues.append(f"line {i}: invalid JSON ({e})")
                continue

            if "messages" not in ex:
                issues.append(f"line {i}: missing 'messages' field")
                continue

            for msg in ex["messages"]:
                if msg.get("role") not in {"system", "user", "assistant"}:
                    issues.append(f"line {i}: invalid role {msg.get('role')}")
                total_tokens += len(enc.encode(msg.get("content", "")))

            n_examples += 1

    return {
        "n_examples": n_examples,
        "total_tokens": total_tokens,
        "issues": issues,
        "estimated_cost_usd_per_epoch": (total_tokens / 1_000_000) * COST_PER_M_TRAINING_TOKEN,
    }


# ----------------- 3. UPLOAD -----------------

def upload(jsonl_path: Path) -> str:
    """Upload training file. Returns file ID."""
    with jsonl_path.open("rb") as f:
        resp = client.files.create(file=f, purpose="fine-tune")
    return resp.id


# ----------------- 4. TRAIN -----------------

def train(
    training_file_id: str,
    *,
    validation_file_id: str | None = None,
    suffix: str = "ossaihub-custom",
    n_epochs: int = 3,
) -> str:
    """Create fine-tune job. Returns job ID."""
    job = client.fine_tuning.jobs.create(
        training_file=training_file_id,
        validation_file=validation_file_id,
        model=BASE_MODEL,
        hyperparameters={"n_epochs": n_epochs},
        suffix=suffix,
    )
    return job.id


# ----------------- 5. POLL -----------------

def poll(job_id: str, *, interval_seconds: int = 30) -> str | None:
    """Block until job completes. Returns fine-tuned model name or None."""
    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)
        print(f"  status: {job.status}", end="")
        if job.estimated_finish:
            print(f" (eta: {job.estimated_finish})")
        else:
            print()

        if job.status in ("succeeded", "failed", "cancelled"):
            if job.status == "succeeded":
                return job.fine_tuned_model
            print(f"Job ended with status: {job.status}")
            if job.error:
                print(f"Error: {job.error}")
            return None

        time.sleep(interval_seconds)


# ----------------- 6. EVALUATE -----------------

def evaluate(fine_tuned_model: str, test_cases: list[dict]) -> None:
    """Run test cases through base and fine-tuned model; compare side by side."""
    for tc in test_cases:
        print(f"\\n--- {tc.get('name', 'case')} ---")
        for model in [BASE_MODEL, fine_tuned_model]:
            resp = client.chat.completions.create(
                model=model,
                messages=tc["messages"],
                temperature=0,
            )
            print(f"\\n[{model}]\\n{resp.choices[0].message.content}")


# ----------------- MAIN -----------------

def main():
    if len(sys.argv) < 2:
        print("usage: python tune.py prepare data.csv | validate | upload | train | poll <job_id> | evaluate <model>")
        return

    cmd = sys.argv[1]

    if cmd == "prepare":
        prepare_from_csv(Path(sys.argv[2]), Path("training.jsonl"))
        print("Wrote training.jsonl")

    elif cmd == "validate":
        stats = validate(Path("training.jsonl"))
        print(json.dumps(stats, indent=2))

    elif cmd == "upload":
        file_id = upload(Path("training.jsonl"))
        print(f"Uploaded: {file_id}")
        Path(".file_id").write_text(file_id)

    elif cmd == "train":
        file_id = Path(".file_id").read_text().strip()
        job_id = train(file_id)
        print(f"Started job: {job_id}")
        Path(".job_id").write_text(job_id)

    elif cmd == "poll":
        job_id = sys.argv[2] if len(sys.argv) > 2 else Path(".job_id").read_text().strip()
        model = poll(job_id)
        if model:
            print(f"Fine-tuned model: {model}")
            Path(".model").write_text(model)

    elif cmd == "evaluate":
        model = sys.argv[2] if len(sys.argv) > 2 else Path(".model").read_text().strip()
        test_cases = [
            {"name": "case1", "messages": [{"role": "user", "content": "test prompt"}]},
        ]
        evaluate(model, test_cases)


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Fine-tune API"},
            {"name": "tiktoken", "version": ">=0.7", "purpose": "Token counting"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai tiktoken",
            "Prepare CSV with columns: system, user, assistant",
            "python tune.py prepare data.csv  # → training.jsonl",
            "python tune.py validate  # check format + estimate cost",
            "python tune.py upload  # → file ID",
            "python tune.py train  # → job ID",
            "python tune.py poll  # wait for completion",
            "python tune.py evaluate  # compare base vs fine-tuned",
        ],
        "variations": [
            {
                "label": "With validation file",
                "description": "Track loss on held-out set.",
                "code_snippet": "# Upload a separate validation.jsonl; pass validation_file_id to train()\\n# OpenAI reports validation loss in job events",
            },
            {
                "label": "Hyperparameter sweep",
                "description": "Try multiple epochs.",
                "code_snippet": "for n_epochs in [1, 2, 3, 4]:\\n    job_id = train(file_id, n_epochs=n_epochs, suffix=f'epochs-{n_epochs}')\\n    # poll each, then evaluate all on held-out test set",
            },
            {
                "label": "Synthetic data augmentation",
                "description": "Generate more training examples from existing.",
                "code_snippet": "# Use the base model to generate variants of each example.\\n# Validate carefully — synthetic noise can hurt.",
            },
            {
                "label": "Function calling tune",
                "description": "Tune for consistent tool use.",
                "code_snippet": "# Include tool_calls in assistant messages.\\n# Format per OpenAI docs: messages with 'tool_calls' array.",
            },
        ],
        "common_errors": [
            {
                "error_text": "BadRequestError: invalid file format",
                "cause": "JSONL doesn't follow OpenAI's expected schema.",
                "fix_snippet": "Validate first. Each line: {\"messages\": [{\"role\": ..., \"content\": ...}, ...]}. No extra fields at top level.",
            },
            {
                "error_text": "Cost shock",
                "cause": "Didn't estimate before running.",
                "fix_snippet": "Always run validate() first; multiply total_tokens by n_epochs to get full cost estimate.",
            },
            {
                "error_text": "Fine-tuned model performs worse than base",
                "cause": "Insufficient or poor-quality training data.",
                "fix_snippet": "Need at least 50-100 high-quality examples. Re-evaluate examples — diverse, cover edge cases, no contradictions. If unsolved, fine-tuning isn't the right tool.",
            },
            {
                "error_text": "Training takes hours",
                "cause": "Normal for first job; depends on dataset size.",
                "fix_snippet": "Smaller datasets train in 10-30 min; larger in hours. Use the poll script with notification.",
            },
        ],
        "production_checklist": [
            "Hold out 20% of data for evaluation BEFORE training.",
            "Compare base vs fine-tuned on held-out cases; don't just trust training loss.",
            "Pin the fine-tuned model name in your code; don't auto-upgrade.",
            "Monitor production performance; retrain on new data quarterly.",
            "Cost: training is one-time; inference cost on FT models is higher than base. Calculate ROI.",
            "Document the fine-tune: data version, base model version, hyperparameters, eval results.",
            "Keep training data in version control; reproducibility matters.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini-2024-07-18"],
            "library_versions": ["openai==1.51.0", "tiktoken==0.8.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["fine-tuning", "supervised-finetuning"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "When does fine-tuning beat prompting?",
                "answer": "Narrow tasks with specific format / style requirements. Brand voice. Domain-specific classification with subtle nuances. Function-call format compliance. NOT for: knowledge updates (use RAG), reasoning capability boosts (use larger model).",
            },
            {
                "question": "How much training data do I need?",
                "answer": "OpenAI says minimum 10; realistically 50-100 to see improvement, 200-500 for solid gains. Quality matters more than quantity beyond that.",
            },
            {
                "question": "What's the cost?",
                "answer": "Training: ~$3 per million tokens (gpt-4o-mini) × n_epochs. Inference on FT model: ~2-3x base model cost. Estimate carefully before training.",
            },
            {
                "question": "Can I download the fine-tuned model?",
                "answer": "No — OpenAI fine-tuned models are hosted only. For full ownership, fine-tune a local model with LoRA (see PEFT starter).",
            },
        ],
        "github_url": "https://github.com/openai/openai-python",
        "meta_title": "OpenAI Fine-Tune Pipeline — Starter",
        "meta_description": "End-to-end OpenAI fine-tuning: prepare data, validate, upload, train, poll, evaluate base vs fine-tuned. Cost estimate before commit.",
    },
    {
        "slug": "lora-finetune-with-peft",
        "title": "LoRA Fine-Tune With Hugging Face PEFT",
        "tldr": "Parameter-efficient fine-tuning (LoRA) on a Llama 3.1 8B model using PEFT. Trains on a single A100 in hours; saves 100MB adapter instead of 16GB full weights.",
        "category": "fine-tuning",
        "language": "python",
        "framework": "PEFT + transformers",
        "tags": ["lora", "peft", "fine-tuning", "open-source-llm"],
        "best_for_tags": ["local-fine-tune", "domain-llm", "low-budget-tuning"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When you want to fine-tune an open-source model (Llama, Mistral) without renting an 8x A100. LoRA trains only 0.1-1% of parameters; you get a small adapter file that swaps in at inference time.",
        "when_not_to_use": "Skip when you can use OpenAI fine-tuning (easier, no infra). Skip when you need full weights (research). Skip if you don't have any GPU — LoRA still needs one A100 for 8B+ models.",
        "quick_start": "pip install peft transformers accelerate bitsandbytes && python lora_train.py",
        "full_code": '''"""LoRA fine-tune of Llama 3.1 8B using PEFT.

Trains on consumer-friendly hardware:
  - 1x A100 40GB (recommended) or A100 80GB
  - QLoRA (4-bit base model) enables training on smaller GPUs

Output is a ~100MB adapter file that loads on top of the base model.
"""
from __future__ import annotations

from datasets import load_dataset
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
import torch

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"

# 4-bit quantization for QLoRA — fits 8B in ~6GB instead of ~16GB
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
)
model = prepare_model_for_kbit_training(model)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# LoRA config — what layers to adapt
lora_config = LoraConfig(
    r=16,                                  # rank: higher = more capacity, more params
    lora_alpha=32,                         # scaling
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # attention layers
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Output like: "trainable params: 6,815,744 || all params: 8,036,067,328 || trainable%: 0.085"


# Load and format dataset
def format_example(example):
    """Format as Llama instruction template."""
    return {
        "text": (
            "<|start_header_id|>system<|end_header_id|>\\n\\n"
            f"{example.get('system', 'You are a helpful assistant.')}<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\\n\\n"
            f"{example['instruction']}<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\\n\\n"
            f"{example['response']}<|eot_id|>"
        )
    }


dataset = load_dataset("json", data_files="training.jsonl", split="train")
dataset = dataset.map(format_example)
dataset = dataset.map(lambda x: tokenizer(x["text"], truncation=True, max_length=2048), batched=True)

# Training args
training_args = TrainingArguments(
    output_dir="./lora-output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,         # effective batch = 16
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=False,
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    report_to="none",                      # or "wandb" for logging
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
)
trainer.train()

# Save adapter only (100MB) — not the full model
model.save_pretrained("./final-adapter")
tokenizer.save_pretrained("./final-adapter")

# ----------------- LOADING FOR INFERENCE -----------------
# Later, to load:
#   from peft import PeftModel
#   base = AutoModelForCausalLM.from_pretrained(MODEL_NAME, quantization_config=bnb_config)
#   model = PeftModel.from_pretrained(base, "./final-adapter")
''',
        "dependencies": [
            {"name": "peft", "version": ">=0.13", "purpose": "Parameter-efficient fine-tuning"},
            {"name": "transformers", "version": ">=4.45", "purpose": "Model + Trainer"},
            {"name": "accelerate", "version": ">=1.0", "purpose": "Multi-GPU / device management"},
            {"name": "bitsandbytes", "version": ">=0.44", "purpose": "4-bit quantization"},
            {"name": "datasets", "version": ">=3.0", "purpose": "Data loading"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "HF token (Llama is gated)", "example": "hf_..."},
        ],
        "setup_steps": [
            "Accept Llama 3.1 license on huggingface.co",
            "export HF_TOKEN=hf_...",
            "pip install peft transformers accelerate bitsandbytes datasets torch",
            "Prepare training.jsonl: {\"instruction\": \"...\", \"response\": \"...\"} per line",
            "python lora_train.py  # needs GPU",
            "Adapter saved to ./final-adapter (~100MB)",
        ],
        "variations": [
            {
                "label": "DPO (preference tuning)",
                "description": "Train on preference pairs instead of completions.",
                "code_snippet": "from trl import DPOTrainer\\n# Dataset has {prompt, chosen, rejected}\\ntrainer = DPOTrainer(model, args=training_args, train_dataset=dataset, tokenizer=tokenizer)",
            },
            {
                "label": "Without 4-bit (full precision)",
                "description": "If you have an 80GB A100.",
                "code_snippet": "# Skip bnb_config; load model directly:\\nmodel = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.bfloat16, device_map='auto')",
            },
            {
                "label": "Multi-GPU",
                "description": "Distribute across 2-8 GPUs.",
                "code_snippet": "# accelerate launch lora_train.py\\n# Auto-distributes via accelerate config (run `accelerate config` first)",
            },
            {
                "label": "Inference server",
                "description": "Serve the adapter with vLLM.",
                "code_snippet": "# vLLM supports LoRA adapters:\\n# vllm serve meta-llama/Llama-3.1-8B-Instruct --lora-modules my-adapter=./final-adapter",
            },
        ],
        "common_errors": [
            {
                "error_text": "OutOfMemoryError",
                "cause": "Batch size too high or model not quantized.",
                "fix_snippet": "Reduce per_device_train_batch_size to 1; increase gradient_accumulation_steps to maintain effective batch. Or use smaller model (Llama 3.1 1B).",
            },
            {
                "error_text": "Training converges immediately (loss → 0)",
                "cause": "Likely overfitting on small dataset, or data leakage.",
                "fix_snippet": "Hold out validation set; track val loss. If val loss diverges, reduce learning rate or epochs. Check for duplicate examples in training data.",
            },
            {
                "error_text": "Adapter doesn't change model output",
                "cause": "Forgot to load adapter at inference time, or LoRA target_modules wrong.",
                "fix_snippet": "Verify adapter loading: model = PeftModel.from_pretrained(base, './final-adapter'). For Llama 3.1, q_proj/k_proj/v_proj/o_proj are correct; verify with model.print_trainable_parameters() > 0%.",
            },
            {
                "error_text": "Slow training on consumer GPU",
                "cause": "QLoRA still needs a strong GPU.",
                "fix_snippet": "Llama 3.1 8B QLoRA needs at least A10G or 3090 for reasonable speed. 4090 also works. For weaker hardware, use a smaller base model (3B or 1B).",
            },
        ],
        "production_checklist": [
            "Hold out 10-20% of data as eval set; track val loss.",
            "Save adapter + base model version + LoRA config — reproducibility.",
            "Test on held-out cases AND production-shape inputs before deploying.",
            "For inference, vLLM with LoRA adapter is fastest. Or transformers with PeftModel.",
            "Monitor base model upgrades; LoRA adapters are tied to a specific base version.",
            "Backup adapters; they're small but irreplaceable without retraining.",
            "Document hyperparameters in adapter folder — future-you will thank you.",
        ],
        "tested_with": {
            "model_versions": ["meta-llama/Llama-3.1-8B-Instruct"],
            "library_versions": ["peft==0.13.2", "transformers==4.45.2", "bitsandbytes==0.44.1"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["peft", "transformers"],
        "related_glossary_slugs": ["lora", "qlora", "peft", "fine-tuning"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "LoRA vs full fine-tune?",
                "answer": "LoRA: 0.1-1% of parameters, tiny memory footprint, slightly worse quality. Full FT: all parameters, much bigger memory, slightly better quality. For most tasks, LoRA is the right call. Full FT only for research or extreme quality.",
            },
            {
                "question": "What r value (rank) to use?",
                "answer": "r=8-16 for most tasks. r=32-64 if you have lots of data and want more capacity. r=4 if data is small. Higher r = more params but bigger adapter.",
            },
            {
                "question": "Can I run inference on CPU?",
                "answer": "Slow but possible. Better: use the adapter with an Ollama-compatible quantization (GGUF) for CPU inference. Or just use the base model.",
            },
            {
                "question": "How does this compare to OpenAI fine-tuning?",
                "answer": "OpenAI: easier, hosted, no infra, no model ownership. LoRA: full control, own the adapter, can run on your hardware, cheaper at scale. Pick based on operational concerns.",
            },
        ],
        "github_url": "https://github.com/huggingface/peft",
        "meta_title": "LoRA Fine-Tune With Hugging Face PEFT",
        "meta_description": "Parameter-efficient fine-tune of Llama 3.1 8B with PEFT + QLoRA. ~100MB adapter trains on a single A100 in hours.",
    },
]
