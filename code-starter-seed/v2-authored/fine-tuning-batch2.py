"""Fine-tuning starters — batch 2: Unsloth QLoRA, Axolotl, dataset prep, eval."""

RECORDS = [
    {
        "slug": "unsloth-qlora-llama-finetune",
        "title": "Unsloth QLoRA Fine-Tune (4x Faster, 70% Less VRAM)",
        "tldr": "Unsloth: drop-in fine-tuning that's 4x faster + uses 70% less VRAM than HF Trainer. Fine-tune Llama-3.1-8B on a single 24GB GPU in <2 hours.",
        "category": "fine-tuning",
        "language": "python",
        "framework": "Unsloth",
        "tags": ["unsloth", "qlora", "fine-tuning", "llama"],
        "best_for_tags": ["single-gpu", "fast-iteration", "cost-sensitive"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Fine-tuning Llama / Mistral / Phi / Qwen on a single GPU (24GB+) and want to iterate fast. Unsloth's custom kernels make this practical without H100 clusters.",
        "when_not_to_use": "Skip for full-parameter fine-tuning of 70B+ models (still need multi-GPU + DeepSpeed). Skip if you need broad model support — Unsloth supports a curated list.",
        "quick_start": "pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git' && python unsloth_qlora.py",
        "full_code": '''"""Unsloth QLoRA fine-tune on a single 24GB GPU."""
from __future__ import annotations

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments


# ----------------- LOAD MODEL (4-bit QLoRA) -----------------

MAX_SEQ_LEN = 4096

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    max_seq_length=MAX_SEQ_LEN,
    dtype=None,  # auto: bfloat16 on Ampere+, float16 on older
    load_in_4bit=True,
)


# ----------------- ADD LORA ADAPTERS -----------------

model = FastLanguageModel.get_peft_model(
    model,
    r=16,                            # LoRA rank; 16 is balanced
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,                   # 2x rank is a good default
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",  # ~30% less VRAM
    random_state=42,
    use_rslora=False,                # try True for harder tasks
)


# ----------------- DATASET (Alpaca-style) -----------------

ALPACA_TEMPLATE = """Below is an instruction. Write a response that fulfills it.

### Instruction:
{instruction}

### Response:
{output}"""


def format_alpaca(example):
    return {"text": ALPACA_TEMPLATE.format(
        instruction=example["instruction"],
        output=example["output"],
    )}


dataset = load_dataset("yahma/alpaca-cleaned", split="train")
dataset = dataset.map(format_alpaca)


# ----------------- TRAINER -----------------

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LEN,
    packing=True,                # 5x faster on short sequences
    args=TrainingArguments(
        output_dir="./unsloth-llama-finetune",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,   # effective batch = 8
        warmup_steps=20,
        max_steps=200,                   # short run for demo; remove for full epoch
        learning_rate=2e-4,
        bf16=True,                       # bfloat16 if available
        logging_steps=10,
        optim="adamw_8bit",              # 8-bit Adam for memory
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="wandb",               # or "none"
    ),
)


# ----------------- TRAIN -----------------

if __name__ == "__main__":
    trainer.train()

    # Save LoRA adapter
    model.save_pretrained("./unsloth-llama-lora")
    tokenizer.save_pretrained("./unsloth-llama-lora")

    # OR merge to base + save as full model (4-bit or 16-bit)
    # model.save_pretrained_merged("./merged-16bit", tokenizer, save_method="merged_16bit")
    # model.save_pretrained_gguf("./gguf-q4", tokenizer, quantization_method="q4_k_m")
''',
        "dependencies": [
            {"name": "unsloth", "version": ">=2024.10", "purpose": "Optimized fine-tuning"},
            {"name": "trl", "version": ">=0.11", "purpose": "SFTTrainer"},
            {"name": "datasets", "version": ">=2.18", "purpose": "Dataset loading"},
            {"name": "wandb", "version": ">=0.17", "purpose": "Experiment tracking (optional)"},
        ],
        "env_vars": [
            {"name": "WANDB_API_KEY", "required": False, "description": "If using wandb", "example": "..."},
            {"name": "HF_TOKEN", "required": True, "description": "For gated model downloads", "example": "hf_..."},
        ],
        "setup_steps": [
            "Install: pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'",
            "Verify GPU: nvidia-smi (need 24GB+ for 8B; 16GB for 7B)",
            "export HF_TOKEN=hf_...",
            "python unsloth_qlora.py",
            "Monitor: tensorboard or wandb dashboard",
        ],
        "variations": [
            {"label": "Larger model (70B)", "description": "QLoRA on 70B with 1×H100 80GB or 2×A6000.", "code_snippet": "model_name='unsloth/Meta-Llama-3.1-70B-Instruct-bnb-4bit'; per_device_train_batch_size=1; gradient_accumulation_steps=8"},
            {"label": "DPO / preference tuning", "description": "Train on chosen/rejected pairs.", "code_snippet": "from trl import DPOTrainer; DPOTrainer(model=model, beta=0.1, train_dataset=dpo_dataset, ...)"},
            {"label": "Export to GGUF for Ollama", "description": "Run fine-tuned model in Ollama.", "code_snippet": "model.save_pretrained_gguf('./gguf', tokenizer, quantization_method='q4_k_m'); # then 'ollama create my-model -f Modelfile'"},
        ],
        "common_errors": [
            {"error_text": "CUDA OOM mid-training", "cause": "Sequence length / batch too aggressive.", "fix_snippet": "Reduce max_seq_length (4096 → 2048). Reduce per_device_train_batch_size. Increase gradient_accumulation_steps to keep effective batch size."},
            {"error_text": "Loss diverges (NaN)", "cause": "Learning rate too high.", "fix_snippet": "Lower learning_rate (2e-4 → 1e-4). Increase warmup_steps. Add gradient_clipping (max_grad_norm=1.0 in TrainingArguments)."},
            {"error_text": "Model outputs garbage after merging", "cause": "Wrong save method or tokenizer mismatch.", "fix_snippet": "Use save_pretrained_merged with 'merged_16bit' (not 4bit). Verify tokenizer pad/eos tokens match base model."},
            {"error_text": "RuntimeError: unsloth not supported on this GPU", "cause": "Unsloth requires Ampere+ (RTX 30/40, A100, H100).", "fix_snippet": "Use vanilla HF Trainer + bitsandbytes for older GPUs. Or rent a colab/runpod with Ampere+."},
        ],
        "production_checklist": [
            "Hold out an eval set; track loss + custom metrics during training.",
            "Track experiments (wandb / mlflow) — fine-tuning has many knobs.",
            "Run inference test on fine-tuned model before merging.",
            "Quantize for deployment (4-bit or 8-bit) to cut serving cost.",
            "Document training data + config (model card).",
            "Test for catastrophic forgetting on general benchmarks.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct", "Mistral-7B-v0.3"],
            "library_versions": ["unsloth==2024.10", "trl==0.11"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["unsloth", "trl"],
        "related_glossary_slugs": ["qlora", "fine-tuning"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "QLoRA vs full fine-tuning?", "answer": "QLoRA: trains a small adapter (~50MB) on top of frozen 4-bit base. 5-10% less performance than full FT. 50x cheaper VRAM. Use QLoRA unless you need full FT for quality reasons."},
            {"question": "Unsloth vs HF Trainer?", "answer": "Unsloth: 4x faster, 70% less VRAM, custom kernels. HF Trainer: broader model support, more features. Unsloth for compatible models; HF for everything else."},
            {"question": "How much data?", "answer": "1k-10k high-quality examples beats 100k mediocre. Quality > quantity. Aim for >2k examples for a 7B model."},
            {"question": "Cost?", "answer": "Single 8B fine-tune on RTX 4090 ($0.50/hr cloud): ~$1-3. On A100: faster, similar cost. Compare to OpenAI fine-tuning (~$25 for 1M tokens) — way cheaper if you self-host."},
        ],
        "github_url": "https://github.com/unslothai/unsloth",
        "meta_title": "Unsloth QLoRA Fine-Tune Starter",
        "meta_description": "Fine-tune Llama / Mistral with Unsloth QLoRA: 4x faster, 70% less VRAM. Single 24GB GPU, 2-hour iterations, GGUF export.",
    },
    {
        "slug": "axolotl-config-driven-finetune",
        "title": "Axolotl Config-Driven Fine-Tune",
        "tldr": "Axolotl: YAML-config-driven fine-tuning supporting QLoRA, LoRA, full-FT, DPO. Reproducible, distributed-training friendly, integrates with DeepSpeed / FSDP.",
        "category": "fine-tuning",
        "language": "yaml",
        "framework": "Axolotl",
        "tags": ["axolotl", "fine-tuning", "yaml-config", "distributed"],
        "best_for_tags": ["reproducibility", "multi-gpu", "team-workflows"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Team-environment fine-tuning where reproducibility + config-as-code matter. Axolotl YAML configs are easier to version + share than Python scripts. Multi-GPU FT is first-class.",
        "when_not_to_use": "Skip for one-off experiments (Python script is faster). Skip for unsupported models (Axolotl supports a curated list).",
        "quick_start": "pip install 'axolotl[flash-attn,deepspeed]' && accelerate launch -m axolotl.cli.train config.yml",
        "full_code": '''# axolotl config — fine-tune Llama-3.1-8B with QLoRA on Alpaca dataset
# Save as: config.yml
# Run:     accelerate launch -m axolotl.cli.train config.yml

# ----------------- MODEL -----------------
base_model: meta-llama/Llama-3.1-8B-Instruct
model_type: LlamaForCausalLM
tokenizer_type: AutoTokenizer

load_in_4bit: true                    # QLoRA
strict: false


# ----------------- DATASET -----------------
datasets:
  - path: yahma/alpaca-cleaned
    type: alpaca                       # built-in format; or: completion, sharegpt, custom

  # Multi-dataset mix
  # - path: tatsu-lab/alpaca
  #   type: alpaca
  # - path: ./custom_data.jsonl
  #   type: chat_template
  #   chat_template: chatml

dataset_prepared_path: ./prepared
val_set_size: 0.05
output_dir: ./axolotl-llama-out

sequence_len: 4096
sample_packing: true                  # pack short sequences; ~5x faster
pad_to_sequence_len: true


# ----------------- LORA -----------------
adapter: qlora                        # qlora | lora | (omit for full FT)
lora_r: 32
lora_alpha: 64
lora_dropout: 0.05
lora_target_linear: true
lora_modules_to_save: []


# ----------------- TRAINING -----------------
gradient_accumulation_steps: 4
micro_batch_size: 2
num_epochs: 3

optimizer: adamw_bnb_8bit             # 8-bit Adam
lr_scheduler: cosine
learning_rate: 2.0e-4
warmup_steps: 50

train_on_inputs: false                # mask user turns; only train on assistant
group_by_length: false

bf16: auto
tf32: true
flash_attention: true
gradient_checkpointing: true


# ----------------- DEEPSPEED (multi-GPU) -----------------
# deepspeed: deepspeed_configs/zero2.json   # uncomment for multi-GPU


# ----------------- LOGGING + EVAL -----------------
logging_steps: 10
eval_steps: 100
save_steps: 200
save_total_limit: 2

# WandB
# wandb_project: my-finetune
# wandb_entity: my-team


# ----------------- TOKENS + ROPE -----------------
special_tokens:
  pad_token: "<|end_of_text|>"

# rope_scaling:
#   type: linear
#   factor: 2.0


# ----------------- POST-TRAINING MERGE -----------------
# After training, merge LoRA → base:
# python -m axolotl.cli.merge_lora ./axolotl-llama-out
''',
        "dependencies": [
            {"name": "axolotl", "version": ">=0.5", "purpose": "Config-driven fine-tuning framework"},
            {"name": "flash-attn", "version": ">=2.6", "purpose": "Flash attention (optional, faster)"},
            {"name": "deepspeed", "version": ">=0.15", "purpose": "Multi-GPU support"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "Gated model access", "example": "hf_..."},
            {"name": "WANDB_API_KEY", "required": False, "description": "Optional logging", "example": "..."},
        ],
        "setup_steps": [
            "Install Axolotl: pip install 'axolotl[flash-attn,deepspeed]'",
            "Save config.yml",
            "huggingface-cli login",
            "accelerate config  # one-time setup, pick GPU/multi-GPU",
            "accelerate launch -m axolotl.cli.train config.yml",
            "Merge: python -m axolotl.cli.merge_lora ./axolotl-llama-out",
        ],
        "variations": [
            {"label": "DPO preference tuning", "description": "Train on chosen/rejected pairs.", "code_snippet": "# Add to config:\\nrl: dpo\\ndatasets:\\n  - path: argilla/distilabel-intel-orca-dpo-pairs\\n    type:\\n      field_system: system\\n      field_chosen: chosen\\n      field_rejected: rejected"},
            {"label": "Multi-GPU with DeepSpeed", "description": "Scale across N GPUs.", "code_snippet": "# Uncomment deepspeed: deepspeed_configs/zero2.json in config\\n# Run: deepspeed --num_gpus 4 -m axolotl.cli.train config.yml"},
            {"label": "Full fine-tuning (no LoRA)", "description": "Maximum quality, max cost.", "code_snippet": "# Remove 'adapter: qlora' and lora_* fields. Need 80GB+ VRAM for 7B; multi-GPU for 13B+"},
        ],
        "common_errors": [
            {"error_text": "FlashAttention not available", "cause": "Wrong CUDA version or older GPU.", "fix_snippet": "Pin: pip install flash-attn==2.6.3 --no-build-isolation. Set flash_attention: false in config if hardware doesn't support."},
            {"error_text": "Sample packing breaks loss", "cause": "Some dataset formats incompatible.", "fix_snippet": "Set sample_packing: false. ~5x slower but works with all formats. Re-enable after debugging."},
            {"error_text": "Inconsistent results across runs", "cause": "No seed set.", "fix_snippet": "Add seed: 42 to config. Note: distributed training has inherent non-determinism even with seed."},
            {"error_text": "Validation loss stops decreasing early", "cause": "Underfit or LR too low.", "fix_snippet": "Increase num_epochs. Check learning_rate (2e-4 typical for LoRA). Consider mixing in more diverse data."},
        ],
        "production_checklist": [
            "Pin all dependency versions in requirements.txt.",
            "Version-control the YAML config alongside model card.",
            "Set seed for reproducibility (still non-deterministic in distributed).",
            "Track all runs in wandb/mlflow for comparison.",
            "Hold out a TEST set (never seen during training/eval).",
            "Document data sources + processing in config comments.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct"],
            "library_versions": ["axolotl==0.5"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["axolotl"],
        "related_glossary_slugs": ["lora", "qlora"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Axolotl vs Unsloth?", "answer": "Axolotl: config-first, multi-GPU friendly, reproducible. Unsloth: fastest single-GPU, custom kernels. Axolotl for production / teams; Unsloth for fast iteration."},
            {"question": "How long does training take?", "answer": "8B + QLoRA + Alpaca-cleaned (~50k examples) + 3 epochs: ~6-8 hours on A100. Single 4090: ~12-18 hours. Use micro_batch_size + gradient_accumulation_steps to fit memory."},
            {"question": "Sample packing — always on?", "answer": "Yes for performance unless you hit an error. Packs short sequences into one batch element. ~5x speedup typical. Some dataset types break with packing (chat with system prompts handled specially)."},
            {"question": "What about TPUs?", "answer": "Axolotl has partial TPU support via accelerate. Most heavily tested on NVIDIA. For TPU, consider EasyDeL or native JAX libs."},
        ],
        "github_url": "https://github.com/OpenAccess-AI-Collective/axolotl",
        "meta_title": "Axolotl Config-Driven Fine-Tune Starter",
        "meta_description": "Axolotl YAML config for QLoRA / LoRA / DPO / full FT. Multi-GPU friendly, reproducible, integrates with DeepSpeed.",
    },
    {
        "slug": "finetune-dataset-prep-pipeline",
        "title": "Fine-Tune Dataset Prep Pipeline (Quality > Quantity)",
        "tldr": "Dataset prep: dedupe, quality-filter, format conversion (chat template), token-count distribution check, train/val split. Bad data is the #1 cause of bad fine-tunes.",
        "category": "fine-tuning",
        "language": "python",
        "framework": "datasets + custom",
        "tags": ["dataset-prep", "fine-tuning", "quality-control", "tokenizer"],
        "best_for_tags": ["data-quality", "pre-training-pipeline", "ml-engineers"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Before fine-tuning: validate dataset quality. Catch issues that ruin training (duplicates, malformed examples, length outliers, missing fields). Do this BEFORE spending GPU hours.",
        "when_not_to_use": "Skip for tiny datasets (<200 examples; eyeball manually). Skip when you've already prepped a dataset for a previous fine-tune (rerun audit on changes).",
        "quick_start": "pip install datasets tqdm transformers && python prep_dataset.py",
        "full_code": '''"""Fine-tune dataset prep + audit pipeline."""
from __future__ import annotations

import hashlib
import json
import re
import statistics
from collections import Counter
from pathlib import Path

from datasets import Dataset, load_dataset
from transformers import AutoTokenizer
from tqdm import tqdm


TOKENIZER = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")


# ----------------- LOAD -----------------

def load_raw(source: str) -> Dataset:
    """Load from HuggingFace hub or local file."""
    if source.endswith(".jsonl"):
        return Dataset.from_json(source)
    return load_dataset(source, split="train")


# ----------------- AUDIT (run BEFORE filtering) -----------------

def audit(dataset: Dataset, instruction_field: str = "instruction",
          output_field: str = "output") -> dict:
    instruction_lens = []
    output_lens = []
    empty_count = 0
    has_lang_tags = 0
    seen_hashes: set[str] = set()
    duplicate_count = 0

    for ex in tqdm(dataset, desc="Auditing"):
        i = ex.get(instruction_field) or ""
        o = ex.get(output_field) or ""
        if not i.strip() or not o.strip():
            empty_count += 1
            continue
        if re.search(r"\\b(?:html|xml|css|javascript)\\b", o.lower()[:200]):
            has_lang_tags += 1
        i_tokens = len(TOKENIZER.encode(i))
        o_tokens = len(TOKENIZER.encode(o))
        instruction_lens.append(i_tokens)
        output_lens.append(o_tokens)
        # Dedup by hash
        h = hashlib.sha256((i + "|" + o).encode()).hexdigest()
        if h in seen_hashes:
            duplicate_count += 1
        else:
            seen_hashes.add(h)

    return {
        "total": len(dataset),
        "empty_examples": empty_count,
        "duplicates": duplicate_count,
        "unique_examples": len(dataset) - empty_count - duplicate_count,
        "instruction_tokens": {
            "median": statistics.median(instruction_lens) if instruction_lens else 0,
            "p95": sorted(instruction_lens)[int(0.95 * len(instruction_lens))] if instruction_lens else 0,
            "max": max(instruction_lens) if instruction_lens else 0,
        },
        "output_tokens": {
            "median": statistics.median(output_lens) if output_lens else 0,
            "p95": sorted(output_lens)[int(0.95 * len(output_lens))] if output_lens else 0,
            "max": max(output_lens) if output_lens else 0,
        },
        "with_html_tags": has_lang_tags,
    }


# ----------------- FILTERS -----------------

def filter_and_dedupe(dataset: Dataset, max_total_tokens: int = 4000,
                     instruction_field: str = "instruction",
                     output_field: str = "output") -> Dataset:
    """Apply quality filters."""
    seen: set[str] = set()
    kept = []

    for ex in tqdm(dataset, desc="Filtering"):
        i = (ex.get(instruction_field) or "").strip()
        o = (ex.get(output_field) or "").strip()
        if not i or not o:
            continue
        # Length filter (avoid OOM on training)
        total_tokens = len(TOKENIZER.encode(i + "\\n" + o))
        if total_tokens > max_total_tokens:
            continue
        # Deduplicate
        h = hashlib.sha256((i + "|" + o).encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        # Heuristic: reject very short outputs (likely low-quality)
        if len(o) < 20:
            continue
        kept.append({instruction_field: i, output_field: o})

    print(f"Kept {len(kept)} / {len(dataset)} ({100 * len(kept) / max(len(dataset), 1):.1f}%)")
    return Dataset.from_list(kept)


# ----------------- FORMAT TO CHAT TEMPLATE -----------------

def to_chat_template(example, instruction_field: str = "instruction",
                     output_field: str = "output"):
    """Convert to Llama-3 chat template."""
    messages = [
        {"role": "user", "content": example[instruction_field]},
        {"role": "assistant", "content": example[output_field]},
    ]
    return {"text": TOKENIZER.apply_chat_template(messages, tokenize=False)}


# ----------------- SPLIT -----------------

def train_val_test_split(dataset: Dataset, val_size: float = 0.05,
                         test_size: float = 0.02, seed: int = 42):
    splits = dataset.train_test_split(test_size=val_size + test_size, seed=seed)
    val_test = splits["test"].train_test_split(
        test_size=test_size / (val_size + test_size), seed=seed
    )
    return {
        "train": splits["train"],
        "validation": val_test["train"],
        "test": val_test["test"],
    }


# ----------------- SAVE -----------------

def save_splits(splits: dict, out_dir: str = "./prepared"):
    out = Path(out_dir)
    out.mkdir(exist_ok=True, parents=True)
    for name, ds in splits.items():
        path = out / f"{name}.jsonl"
        ds.to_json(str(path), orient="records", lines=True)
        print(f"Wrote {path}: {len(ds)} examples")


# ----------------- RUN -----------------

if __name__ == "__main__":
    raw = load_raw("yahma/alpaca-cleaned")
    print("\\n=== AUDIT ===")
    print(json.dumps(audit(raw), indent=2))

    print("\\n=== FILTER + DEDUPE ===")
    cleaned = filter_and_dedupe(raw)

    print("\\n=== FORMAT TO CHAT TEMPLATE ===")
    formatted = cleaned.map(to_chat_template)

    print("\\n=== SPLIT ===")
    splits = train_val_test_split(formatted)
    save_splits(splits)
''',
        "dependencies": [
            {"name": "datasets", "version": ">=2.18", "purpose": "HF datasets"},
            {"name": "transformers", "version": ">=4.45", "purpose": "Tokenizer"},
            {"name": "tqdm", "version": ">=4.66", "purpose": "Progress bars"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "Tokenizer downloads", "example": "hf_..."},
        ],
        "setup_steps": [
            "pip install datasets transformers tqdm",
            "export HF_TOKEN=hf_...",
            "Replace dataset source with your real data",
            "python prep_dataset.py",
            "Inspect ./prepared/train.jsonl + audit output",
        ],
        "variations": [
            {"label": "LLM-as-judge filter", "description": "Filter low-quality examples with another LLM.", "code_snippet": "# For each example, ask GPT-4o-mini: 'is this a high-quality training example? yes/no.' Filter no's."},
            {"label": "Synthetic data generation", "description": "Augment small datasets.", "code_snippet": "# Use Magpie / Self-Instruct: prompt a large model to generate (instruction, output) pairs from a seed instruction"},
            {"label": "Multi-source mix", "description": "Combine datasets with weights.", "code_snippet": "# Use datasets.interleave_datasets([ds1, ds2, ds3], probabilities=[0.5, 0.3, 0.2]) to control mix ratio"},
        ],
        "common_errors": [
            {"error_text": "Out-of-memory loading large dataset", "cause": "Trying to load all at once.", "fix_snippet": "Use streaming: load_dataset('...', streaming=True). Iterate without loading everything into RAM."},
            {"error_text": "Train/val leak (data in both)", "cause": "Splitting AFTER deduplication.", "fix_snippet": "Dedupe BEFORE split. Or split first, then dedupe within each split — but check val/test don't share hashes with train."},
            {"error_text": "Chat template not applying correctly", "cause": "Tokenizer missing template.", "fix_snippet": "Verify tokenizer.chat_template attribute exists. For older tokenizers, set tokenizer.chat_template manually."},
            {"error_text": "Length filter too aggressive — dataset shrinks 80%", "cause": "max_total_tokens too low.", "fix_snippet": "Set max_total_tokens to match your training max_seq_len. Don't filter too aggressively at prep time."},
        ],
        "production_checklist": [
            "Run audit BEFORE filtering — surfaces issues you'd miss in spot-checks.",
            "Deduplicate by exact hash + near-duplicate detection (MinHash for big datasets).",
            "Hold out a TEST split, never seen during training or eval-iteration.",
            "Version dataset prep code alongside model artifacts.",
            "Track: total examples, filter rate, token distribution per split.",
            "Document data sources + filters in the model card.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["datasets==2.18", "transformers==4.45"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["huggingface-datasets"],
        "related_glossary_slugs": ["dataset-curation", "fine-tuning"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How much data for fine-tuning?", "answer": "1k-10k high-quality > 100k mediocre. For instruction-tuning a 7B model: 5k diverse examples is a good baseline. More if your domain is broad."},
            {"question": "Near-duplicate detection?", "answer": "Exact-hash catches identical examples. For near-duplicates (paraphrases), use MinHash + LSH or embedding cosine similarity. Adds 5-10% filter on top of exact-hash."},
            {"question": "Should I balance categories?", "answer": "Depends on use case. If training a classifier, balance. If training an open-ended assistant, follow real-world distribution. Synthetic upsampling is a last resort."},
            {"question": "Validation vs test set?", "answer": "Validation: used for early stopping / HP tuning. Test: locked, single final evaluation. Treat test set as sacred — don't peek during iteration."},
        ],
        "github_url": "",
        "meta_title": "Fine-Tune Dataset Prep Pipeline Starter",
        "meta_description": "Dataset prep for fine-tuning: audit, dedupe, length-filter, chat-template format, train/val/test split. Bad data ruins fine-tunes — start clean.",
    },
    {
        "slug": "finetune-eval-vs-baseline",
        "title": "Fine-Tune Evaluation vs Baseline (Win-Rate)",
        "tldr": "After fine-tuning, prove it beat the baseline. Compare fine-tuned vs base on held-out set with LLM judge — win-rate, tie-rate, regression-rate. The metric that matters.",
        "category": "fine-tuning",
        "language": "python",
        "framework": "Custom + OpenAI judge",
        "tags": ["fine-tuning", "eval", "win-rate", "judge"],
        "best_for_tags": ["ml-engineers", "fine-tune-validation", "ab-testing"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Just finished fine-tuning. Need to PROVE it beat the base model before shipping. LLM-judge win-rate on a held-out set is the gold-standard practical metric.",
        "when_not_to_use": "Skip if you have a deterministic eval (BLEU, exact match) — use that. Skip for tiny test sets (<50 examples) — noise dominates win-rate signal.",
        "quick_start": "pip install openai datasets && python finetune_eval.py",
        "full_code": '''"""Fine-tune vs baseline win-rate eval."""
from __future__ import annotations

import json
import os
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI
from datasets import load_dataset


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- GENERATE RESPONSES -----------------

def generate(prompt: str, model: str) -> str:
    """Call BOTH the base model and fine-tuned model.

    Wire to your real endpoints — vLLM, Modal, etc. Below is illustrative.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=512,
    )
    return response.choices[0].message.content


# ----------------- LLM JUDGE -----------------

JUDGE_PROMPT = """You are evaluating two AI responses to a user prompt.

PROMPT:
{prompt}

RESPONSE A:
{a}

RESPONSE B:
{b}

Which response is better overall (correctness, completeness, helpfulness)?
Respond with EXACTLY one of: "A", "B", or "TIE".
Do not explain. Just the letter."""


def judge(prompt: str, response_a: str, response_b: str) -> str:
    """Single judgment from a stronger model (gpt-4o)."""
    j = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            prompt=prompt, a=response_a, b=response_b
        )}],
        temperature=0,
        max_tokens=10,
    )
    return j.choices[0].message.content.strip()


# ----------------- BIAS MITIGATION: SWAP A/B -----------------

def judge_with_position_swap(prompt: str, base_resp: str, ft_resp: str) -> str:
    """Run judge twice (A=base/B=ft AND A=ft/B=base); only count consistent verdict."""
    v1 = judge(prompt, base_resp, ft_resp)
    v2 = judge(prompt, ft_resp, base_resp)

    # Translate v2 (where A=ft) to base/ft language
    if v1 == "A" and v2 == "B":
        return "base"  # base won both
    elif v1 == "B" and v2 == "A":
        return "ft"  # ft won both
    else:
        return "tie"


# ----------------- RUN EVAL -----------------

def run_eval(eval_set_path: str, base_model: str, ft_model: str, n_samples: int = 100):
    examples = load_dataset("json", data_files=eval_set_path)["train"]
    if len(examples) > n_samples:
        examples = examples.shuffle(seed=42).select(range(n_samples))

    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for ex in examples:
            prompt = ex.get("instruction") or ex["prompt"]
            base_resp = generate(prompt, base_model)
            ft_resp = generate(prompt, ft_model)
            verdict = judge_with_position_swap(prompt, base_resp, ft_resp)
            results.append({"prompt": prompt[:100], "verdict": verdict})

    counts = Counter(r["verdict"] for r in results)
    total = len(results)
    print("\\n=== RESULTS ===")
    print(f"  ft wins:   {counts['ft']:>3} / {total} ({100 * counts['ft'] / total:.0f}%)")
    print(f"  base wins: {counts['base']:>3} / {total} ({100 * counts['base'] / total:.0f}%)")
    print(f"  ties:      {counts['tie']:>3} / {total} ({100 * counts['tie'] / total:.0f}%)")

    # Decision rule
    win_rate = (counts['ft'] + counts['tie'] * 0.5) / total
    if win_rate >= 0.55:
        print(f"\\n✅ Ship: fine-tune beats base (win-rate {win_rate:.2%})")
    elif win_rate <= 0.45:
        print(f"\\n❌ Don't ship: fine-tune LOSES (win-rate {win_rate:.2%})")
    else:
        print(f"\\n⚠️  Inconclusive (win-rate {win_rate:.2%}). Run more samples.")

    # Save detailed log
    with open("eval_results.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\\n")


if __name__ == "__main__":
    run_eval(
        eval_set_path="./prepared/test.jsonl",
        base_model="meta-llama/Llama-3.1-8B-Instruct",
        ft_model="my-ft-llama-3.1-8b",
        n_samples=100,
    )
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Judge LLM"},
            {"name": "datasets", "version": ">=2.18", "purpose": "Load test data"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "For gpt-4o judge", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai datasets",
            "Have a held-out test set (./prepared/test.jsonl)",
            "Configure base + ft model endpoints",
            "python finetune_eval.py",
            "Review eval_results.jsonl for per-example verdicts",
        ],
        "variations": [
            {"label": "Multi-judge consensus", "description": "Use 3 judges; majority wins.", "code_snippet": "# Run judge with gpt-4o, claude-3-5-sonnet, gemini-1.5-pro. Take majority verdict. More robust to single-judge bias."},
            {"label": "Per-category breakdown", "description": "Win-rate by query type.", "code_snippet": "# Tag eval examples by category. Compute win-rate per category. Surfaces where fine-tune wins vs loses."},
            {"label": "Statistical significance", "description": "Bootstrap confidence interval.", "code_snippet": "# Resample N times; compute win-rate distribution. Report 95% CI. Avoids over-interpreting small samples."},
        ],
        "common_errors": [
            {"error_text": "Judge favors the longer response", "cause": "Length bias.", "fix_snippet": "Position swap (already in code) helps. Also: tell judge to ignore length; or use rubric-based judge over preference judge."},
            {"error_text": "All responses tied", "cause": "Test set too easy or judge model too weak.", "fix_snippet": "Use harder test cases. Use a STRONGER judge (gpt-4o or claude-3-opus over gpt-4o-mini)."},
            {"error_text": "Win-rate jumps run-to-run", "cause": "Sample size too small or temperature non-zero.", "fix_snippet": "Use temperature=0 for generation AND judge. Run with at least 100 examples; 300 for stable signals."},
            {"error_text": "Judge says 'A' but the better answer is B", "cause": "Judge model has known biases.", "fix_snippet": "Position swap helps catch this. Multi-judge consensus better. Validate judge accuracy on a hand-labeled subset before trusting at scale."},
        ],
        "production_checklist": [
            "Hold-out test set never seen during fine-tuning.",
            "Position-swap to mitigate A/B bias.",
            "Use a STRONGER model as judge (gpt-4o beats gpt-4o-mini).",
            "Run with ≥100 examples for stable signals.",
            "Track win-rate over time — fine-tune drift detection.",
            "Pair with deterministic metrics (BLEU, exact-match) for full picture.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o", "Llama-3.1-8B-Instruct"],
            "library_versions": ["openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai", "datasets"],
        "related_glossary_slugs": ["llm-as-judge", "win-rate"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why win-rate vs loss / perplexity?", "answer": "Loss measures training fit, not user value. Two models with identical loss can produce different quality outputs. Win-rate measures what users actually care about: better answers."},
            {"question": "Cost of LLM judge?", "answer": "gpt-4o judge: ~$0.001 per comparison. 100 examples × 2 positions = 200 calls = ~$0.20 per eval run. Cheap relative to fine-tuning cost."},
            {"question": "Can the judge be the base model?", "answer": "No — judge must be STRONGER than both candidates. Otherwise the judge is biased toward responses that resemble its own outputs."},
            {"question": "What win-rate to ship?", "answer": "≥55% (after position swap) is the typical bar. 50% = same as base; below 45% = fine-tune is worse. Pair with category breakdown to spot regressions."},
        ],
        "github_url": "",
        "meta_title": "Fine-Tune Evaluation vs Baseline Starter",
        "meta_description": "Prove your fine-tune beat the base model: win-rate eval with LLM judge, position-swap bias mitigation, ship/don't-ship decision rule.",
    },
]
