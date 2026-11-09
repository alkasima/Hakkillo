"""A small, reproducible LoRA run with assistant-only loss and a held-out check."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
from peft import LoraConfig, get_peft_model

from hakkillo.data import encode_example, ensure_disjoint, read_examples
from hakkillo.model import configure_cpu, load_base
from hakkillo.settings import BASE_MODEL, BASE_REVISION, DEFAULT_ADAPTER, ROOT


def mean_loss(model, examples):
    model.eval()
    total, tokens = 0.0, 0
    with torch.inference_mode():
        for batch in examples:
            count = int((batch["labels"][:, 1:] != -100).sum())
            total += float(model(**batch).loss) * count
            tokens += count
    return total / tokens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, default=ROOT / "data/train.jsonl")
    parser.add_argument("--eval", type=Path, default=ROOT / "data/eval.jsonl")
    parser.add_argument("--output", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--steps", type=int, default=48)
    parser.add_argument("--learning-rate", type=float, default=0.0001)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--release", default="development", help="Label for this experimental run")
    parser.add_argument("--report", type=Path, help="Optional new report path; the run always stores its own metrics")
    args = parser.parse_args()
    if args.steps < 1 or args.learning_rate <= 0:
        parser.error("steps and learning rate must be positive")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output directory is not empty; choose a new --output to preserve the previous run")
    if args.report and args.report.exists():
        parser.error("Report already exists; choose a new --report to preserve previous results")
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    train_rows, eval_rows = read_examples(args.train), read_examples(args.eval)
    ensure_disjoint(train_rows, eval_rows)
    model, tokenizer = load_base()
    configure_cpu(args.threads)
    train = [encode_example(tokenizer, r, args.max_length) for r in train_rows]
    evaluation = [encode_example(tokenizer, r, args.max_length) for r in eval_rows]
    started = time.perf_counter()
    before = mean_loss(model, evaluation)
    print(f"Held-out assistant token loss before training: {before:.4f}", flush=True)
    base_parameters = sum(p.numel() for p in model.parameters())
    model = get_peft_model(model, LoraConfig(
        task_type="CAUSAL_LM", r=8, lora_alpha=16, lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"], bias="none", revision=BASE_REVISION,
    ))
    model.config.use_cache = False
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.learning_rate)
    losses = []
    order = []
    model.train()
    for step in range(args.steps):
        if not order:
            order = list(range(len(train)))
            random.shuffle(order)
        batch = train[order.pop()]
        optimizer.zero_grad(set_to_none=True)
        loss = model(**batch).loss
        if not torch.isfinite(loss):
            raise RuntimeError("Non-finite training loss; no release was saved")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(float(loss.detach()))
        if (step + 1) % 8 == 0 or step == 0:
            print(f"Step {step+1}/{args.steps}: loss={losses[-1]:.4f}", flush=True)
    after = mean_loss(model, evaluation)
    elapsed = time.perf_counter() - started
    model.config.use_cache = True
    args.output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output, safe_serialization=True)
    tokenizer.save_pretrained(args.output)
    metrics = {
        "release": args.release, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_model": BASE_MODEL, "base_revision": BASE_REVISION,
        "base_parameters": base_parameters, "trainable_parameters": trainable,
        "training_examples": len(train), "evaluation_examples": len(evaluation),
        "steps": args.steps, "batch_size": 1, "learning_rate": args.learning_rate,
        "seed": args.seed, "threads": args.threads, "max_length": args.max_length,
        "device": "cpu", "dtype": "float32", "lora_rank": 8,
        "package_versions": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "huggingface-hub")},
        "lora_alpha": 16, "lora_dropout": 0.05,
        "train_sha256": hashlib.sha256(args.train.read_bytes()).hexdigest(),
        "eval_sha256": hashlib.sha256(args.eval.read_bytes()).hexdigest(),
        "held_out_loss_before": before, "held_out_loss_after": after,
        "held_out_perplexity_before": math.exp(before), "held_out_perplexity_after": math.exp(after),
        "elapsed_seconds": elapsed, "training_losses": losses,
        "interpretation": "Development loss on the supplied evaluation set; this alone is not evidence of general capability gains.",
    }
    (args.output / "training_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Held-out loss after training: {after:.4f}; saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
