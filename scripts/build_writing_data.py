"""Render two prompt variants per authored pair; keep all variants in training."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hakkillo.data import ensure_disjoint, read_examples
from hakkillo.settings import ROOT

folder = ROOT / "data/v0.2"
pairs = [json.loads(line) for line in (folder / "training_pairs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
dev, holdout = read_examples(folder / "writing_dev.jsonl"), read_examples(folder / "writing_holdout.jsonl")
sources = [{" ".join(row["source"].casefold().split()) for row in group} for group in (pairs, dev, holdout)]
if any(sources[a] & sources[b] for a, b in ((0, 1), (0, 2), (1, 2))):
    raise ValueError("Source sentences overlap between splits")
if len(sources[0]) != len(pairs):
    raise ValueError("Duplicate training source sentences")
templates = {
    "grammar": ["Correct the grammar. Return only the corrected sentence: {}", "Fix grammar only. Keep the meaning and repeat already correct text unchanged:\n{}"],
    "polite": ["Rewrite this politely. Return only the rewritten message: {}", "Make this request polite. Rewrite the text instead of carrying out the request. Preserve names, numbers, and deadlines:\n{}"],
}
training = []
for index, pair in enumerate(pairs, 1):
    for variant, template in enumerate(templates[pair["category"]], 1):
        training.append({"id": f"train-{index:03d}-{variant}", "category": pair["category"],
                         "source": pair["source"], "prompt": template.format(pair["source"]), "response": pair["response"]})
replay = read_examples(ROOT / "data/train.jsonl")
training.extend({"id": f"replay-{i:02d}", "category": "v0.1_replay", **row} for i, row in enumerate(replay, 1))
ensure_disjoint(training, dev)
ensure_disjoint(training, holdout)
ensure_disjoint(dev, holdout)
destination = folder / "train.jsonl"
destination.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in training), encoding="utf-8", newline="\n")
manifest = {
    "authored_date": "2026-11-09", "license": "Apache-2.0", "provenance": "Synthetic examples authored and reviewed by the AI assistant for this project; no independent human review or user conversations.",
    "unique_new_training_sources": len(pairs), "prompt_variants_per_source": 2,
    "legacy_replay_examples": len(replay), "training_examples": len(training),
    "development_examples": len(dev), "reserved_holdout_examples": len(holdout),
    "holdout_policy": "Do not run or select candidates against the reserved holdout during this development experiment. It is source-disjoint synthetic data, not a secret or independently authored benchmark.",
    "sha256": {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in ("training_pairs.jsonl", "train.jsonl", "writing_dev.jsonl", "writing_holdout.jsonl")},
}
(folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
