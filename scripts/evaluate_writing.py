"""Reproducible writing development check; reference matches are not quality scores."""
import argparse
from collections import defaultdict
import gc
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from peft import PeftModel
from hakkillo.data import ensure_disjoint, read_examples
from hakkillo.model import generate_reply, load_base
from hakkillo.settings import BASE_MODEL, BASE_REVISION, DEFAULT_ADAPTER, ROOT


def normalize(text):
    return " ".join(text.split())


def display_source(source):
    if source and Path(source).is_absolute() and Path(source).is_relative_to(ROOT):
        return Path(source).relative_to(ROOT).as_posix()
    return source


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["category"]].append(row)
    output = {}
    for category, cases in {"all": rows, **groups}.items():
        preservation = [r for r in cases if r["preserve"]]
        output[category] = {
            "cases": len(cases),
            "reference_matches": sum(r["reference_match"] for r in cases),
            "preservation_checks_passed": sum(not r["missing_literals"] for r in preservation),
            "preservation_cases": len(preservation),
            "median_seconds": round(statistics.median(r["seconds"] for r in cases), 3),
        }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / "data/v0.2/writing_dev.jsonl")
    parser.add_argument("--model", action="append", help="base, or label=adapter-path; repeat for comparisons")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetition-penalty", type=float, default=1.08)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--training-data", type=Path, action="append", default=[])
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; use a new filename to preserve the previous result")
    if args.repetition_penalty <= 0:
        parser.error("Repetition penalty must be positive")
    rows = read_examples(args.data)
    if len({r["id"] for r in rows}) != len(rows):
        parser.error("Case IDs must be unique")
    for source in [ROOT / "data/train.jsonl", *args.training_data]:
        ensure_disjoint(read_examples(source), rows)
    report = {
        "dataset": str(args.data.relative_to(ROOT)) if args.data.is_relative_to(ROOT) else args.data.name,
        "reserved_holdout_used": args.data.resolve() == (ROOT / "data/v0.2/writing_holdout.jsonl").resolve(),
        "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "base_model": BASE_MODEL, "base_revision": BASE_REVISION,
        "repetition_penalty": args.repetition_penalty, "max_new_tokens": args.max_new_tokens,
        "decoding": "greedy, float32 CPU, existing Hakkillo system prompt",
        "caveat": "Synthetic prompts. Normalized reference matches and literal-preservation checks are diagnostics, not semantic accuracy. Alternative good rewrites require human review.",
        "models": {},
    }
    selections = args.model or ["base", f"v0.1={DEFAULT_ADAPTER}"]
    for selection in selections:
        label, source = ("base", None) if selection == "base" else selection.split("=", 1)
        if label in report["models"]:
            parser.error("Model labels must be unique")
        model, tokenizer = load_base()
        if source:
            model = PeftModel.from_pretrained(model, source)
        model.eval()
        outputs = []
        for i, row in enumerate(rows, 1):
            started = time.perf_counter()
            reply = generate_reply(model, tokenizer, row["prompt"], max_new_tokens=args.max_new_tokens,
                                   repetition_penalty=args.repetition_penalty)
            preserve = row.get("preserve", [])
            outputs.append({
                "id": row["id"], "category": row["category"], "prompt": row["prompt"],
                "reference": row["response"], "response": reply,
                "reference_match": normalize(reply) in [normalize(r) for r in [row["response"], *row.get("alternatives", [])]],
                "preserve": preserve, "missing_literals": [p for p in preserve if p not in reply],
                "rubric": row.get("rubric", "Preserve meaning, follow the instruction, and add no unsupported details."),
                "seconds": round(time.perf_counter() - started, 3),
            })
            if i % 10 == 0:
                print(f"{label}: {i}/{len(rows)} prompts", flush=True)
        report["models"][label] = {"adapter": display_source(source), "summary": summarize(outputs), "results": outputs}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({label: report["models"][label]["summary"]}), flush=True)
        del model, tokenizer
        gc.collect()
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
