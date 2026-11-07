"""Save base/adapter outputs for human review; do not invent a quality score."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from peft import PeftModel

from hakkillo.model import generate_reply, load_base
from hakkillo.settings import DEFAULT_ADAPTER, ROOT

PROMPTS = [
    "Introduce yourself in one short sentence.",
    "What is 7 plus 5? Reply with just the number.",
    "Explain evaporation to a ten-year-old in two sentences.",
    "Rewrite politely: Send me the file now.",
    "Give me three things to check when my laptop will not charge.",
    "What is the weather in Lagos right now?",
    "What is the capital city of Nigeria?",
    "Summarize in one sentence: Amina planted beans on Monday. She watered them daily. One week later, green shoots appeared.",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
    parser.add_argument("--max-new-tokens", type=int, default=80)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/generation_review.json")
    args = parser.parse_args()
    model, tokenizer = load_base()
    model.eval()
    records = [{"prompt": p} for p in PROMPTS]
    for label in ("base", "hakkillo"):
        if label == "hakkillo":
            model = PeftModel.from_pretrained(model, args.adapter).eval()
        for row in records:
            started = time.perf_counter()
            row[label] = generate_reply(model, tokenizer, row["prompt"], max_new_tokens=args.max_new_tokens)
            row[label + "_seconds"] = round(time.perf_counter() - started, 3)
            print(f"{label}: {row['prompt']} -> {row[label]}", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "note": "Development prompts, greedy decoding, shared Hakkillo system prompt. Human review required; not a standardized benchmark.",
        "max_new_tokens": args.max_new_tokens, "results": records,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
