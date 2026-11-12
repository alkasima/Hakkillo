"""Evaluate one completed, preregistered ownership run against its frozen baseline."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from peft import PeftModel
from hakkillo.model import load_base, generate_reply
from hakkillo.settings import ROOT, BASE_MODEL, BASE_REVISION, SYSTEM_PROMPT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output filename; reserved results must never be silently overwritten.")
    folder = ROOT / "data/ownership-v1"
    plan = json.loads((ROOT / "reports/ownership-v1/plan.json").read_text(encoding="utf-8"))
    adapter = ROOT / plan["new_adapter"]
    if not (adapter / "training_metrics.json").is_file():
        parser.error("The fixed training run must finish before any reserved generations.")
    metrics = json.loads((adapter / "training_metrics.json").read_text(encoding="utf-8"))
    expected = plan["training"]
    for field in ("steps", "learning_rate", "batch_size", "threads", "seed", "max_length", "dtype", "device"):
        if metrics[field] != expected[field]:
            parser.error(f"Completed run differs from the fixed plan: {field}")
    if (metrics["initialization"]["sha256"] != plan["initial_adapter_sha256"]
            or metrics["train_sha256"] != plan["data_sha256"]["train.jsonl"]
            or metrics["eval_sha256"] != plan["data_sha256"]["dev.jsonl"]):
        parser.error("Training inputs do not match the frozen plan.")
    groups = {}
    for name, digest in plan["data_sha256"].items():
        data = (folder / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            parser.error(f"Frozen data changed: {name}")
        if name != "train.jsonl":
            groups[Path(name).stem] = [json.loads(line) for line in data.decode("utf-8").splitlines()]
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "preregistered_plan_commit": "9a54501ff34ac51cfe829efa22e919358190521f",
        "plan": plan, "training_run_completed_before_reserved_generation": True,
        "base_model": BASE_MODEL, "base_revision": BASE_REVISION, "system_prompt": SYSTEM_PROMPT,
        "decoding": "Python float32 CPU; greedy; max_new_tokens=64; repetition_penalty=1.08; empty history",
        "candidate2_adapter_sha256": hashlib.sha256((adapter / "adapter_model.safetensors").read_bytes()).hexdigest(),
        "caveat": "Exact reference matches are diagnostics only. Review complete outputs for ownership, roles, negation, actions and added content; report groups separately. Reserved cases are now inspected and are not a fresh holdout for later tuning.",
        "completed": False, "models": {},
    }
    selections = [
        ("candidate1", plan["initial_adapter"], plan["initial_adapter_revision"]),
        ("candidate2", str(adapter), None),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for label, source, revision in selections:
        model, tokenizer = load_base()
        model = PeftModel.from_pretrained(model, source, revision=revision).eval()
        output = {}
        for name in ("regression", "dev", "reserved"):
            rows = []
            for case in groups[name]:
                started = time.perf_counter()
                reply = generate_reply(model, tokenizer, case["prompt"], max_new_tokens=64, repetition_penalty=1.08)
                row = {**case, "reference": case["response"], "response": reply,
                       "reference_match": " ".join(reply.split()) == " ".join(case["response"].split()),
                       "seconds": round(time.perf_counter() - started, 3)}
                rows.append(row)
                print(json.dumps({"model": label, "group": name, "id": case["id"], "response": reply,
                                  "reference_match": row["reference_match"]}, ensure_ascii=True), flush=True)
            families = defaultdict(list)
            for row in rows:
                families[row["family"]].append(row)
            output[name] = {
                "cases": len(rows), "reference_matches": sum(r["reference_match"] for r in rows),
                "families": {family: {"cases": len(items), "reference_matches": sum(r["reference_match"] for r in items)}
                             for family, items in families.items()}, "results": rows,
            }
            report["models"][label] = output
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if label == "candidate2":
            legacy = [json.loads(line) for line in (ROOT / "data/v0.2/writing_dev.jsonl").read_text(encoding="utf-8").splitlines()]
            legacy_results = []
            for case in legacy:
                reply = generate_reply(model, tokenizer, case["prompt"], max_new_tokens=64, repetition_penalty=1.08)
                references = [case["response"], *case.get("alternatives", [])]
                legacy_results.append({**case, "reference": case["response"], "response": reply,
                    "reference_match": " ".join(reply.split()) in [" ".join(r.split()) for r in references]})
            output["legacy_writing_dev"] = {"cases": len(legacy_results),
                "reference_matches": sum(r["reference_match"] for r in legacy_results), "results": legacy_results,
                "candidate1_comparison": "reports/v0.2/writing-candidate1.json; same pinned base, system prompt and decoding"}
            print(json.dumps({"model": label, "legacy_writing_reference_matches": output["legacy_writing_dev"]["reference_matches"]}), flush=True)
            prior_smoke = json.loads((ROOT / "reports/v0.2/general-candidate1.json").read_text(encoding="utf-8"))
            smoke_results = []
            for case in prior_smoke["results"]:
                reply = generate_reply(model, tokenizer, case["prompt"], max_new_tokens=prior_smoke["max_new_tokens"], repetition_penalty=1.08)
                smoke_results.append({"prompt": case["prompt"], "candidate1": case["hakkillo"], "candidate2": reply})
                print(json.dumps({"model": label, "general_prompt": case["prompt"], "response": reply}, ensure_ascii=True), flush=True)
            output["general_smoke"] = {"max_new_tokens": prior_smoke["max_new_tokens"], "results": smoke_results,
                                      "candidate1_comparison": "Previous pinned candidate1 run; not an independent benchmark"}
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        del model, tokenizer
        gc.collect()
    report["completed"] = True
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
