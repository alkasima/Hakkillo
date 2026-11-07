"""Validate examples and mask the prompt so only assistant tokens are trained."""
import json
from pathlib import Path

import torch

from hakkillo.settings import SYSTEM_PROMPT


def read_examples(path):
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in ("prompt", "response")):
            raise ValueError(f"{path}:{number}: prompt and response must be nonempty strings")
        rows.append(row)
    if not rows:
        raise ValueError(f"No examples in {path}")
    if len({r["prompt"].strip().casefold() for r in rows}) != len(rows):
        raise ValueError(f"Duplicate prompts in {path}")
    return rows


def encode_example(tokenizer, row, max_length=256):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": row["prompt"]},
    ]
    prefix = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
    full = tokenizer.apply_chat_template(
        messages + [{"role": "assistant", "content": row["response"]}], tokenize=True, return_dict=False
    )
    if full[:len(prefix)] != prefix:
        raise ValueError("Chat template prefix mismatch; cannot safely mask the assistant target")
    if len(full) > max_length:
        raise ValueError(f"Example has {len(full)} tokens, over limit {max_length}; shorten it or raise the limit")
    if len(full) <= len(prefix):
        raise ValueError("Example has no assistant tokens")
    return {
        "input_ids": torch.tensor([full], dtype=torch.long),
        "attention_mask": torch.ones((1, len(full)), dtype=torch.long),
        "labels": torch.tensor([[-100] * len(prefix) + full[len(prefix):]], dtype=torch.long),
    }


def ensure_disjoint(train, evaluation):
    overlap = {r["prompt"].strip().casefold() for r in train} & {
        r["prompt"].strip().casefold() for r in evaluation
    }
    if overlap:
        raise ValueError(f"Training and evaluation prompts overlap: {sorted(overlap)}")
