"""Record pinned model outputs for community regression cases; no automatic quality score."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huggingface_hub import hf_hub_download
from peft import PeftModel
from hakkillo.model import generate_reply, load_base
from hakkillo.settings import ROOT, BASE_MODEL, BASE_REVISION, SYSTEM_PROMPT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/community/2026-11-10-umbrella.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path to preserve previous results.")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    if len({row["id"] for row in data["cases"]}) != len(data["cases"]):
        parser.error("Case IDs must be unique.")
    v01 = json.loads((ROOT / "reports/publishing.json").read_text(encoding="utf-8"))
    candidate = json.loads((ROOT / "reports/v0.2/publication.json").read_text(encoding="utf-8"))
    sources = [
        ("v0.1", "alkasima/Hakkillo-135M-v0.1", v01["model_commit"]),
        ("writing-candidate1", candidate["model_id"], candidate["revision"]),
    ]
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": data,
        "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "base_model": BASE_MODEL, "base_revision": BASE_REVISION,
        "system_prompt": SYSTEM_PROMPT,
        "generation": {"runtime": "Python float32 CPU; not quantized browser inference",
                       "max_new_tokens": 64, "do_sample": False,
                       "repetition_penalty": 1.08, "history": []},
        "reserved_holdout_used": False,
        "quality_scoring": "Separate qualitative review required. No semantic accuracy score is generated.",
        "models": {},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for label, model_id, revision in sources:
        weights = Path(hf_hub_download(model_id, "adapter_model.safetensors", revision=revision))
        model, tokenizer = load_base()
        model = PeftModel.from_pretrained(model, model_id, revision=revision).eval()
        results = []
        for case in data["cases"]:
            prompt = "Rewrite politely: " + case["sentence"]
            started = time.perf_counter()
            reply = generate_reply(model, tokenizer, prompt, max_new_tokens=64, repetition_penalty=1.08)
            results.append({"case_id": case["id"], "prompt": prompt, "response": reply,
                            "seconds": round(time.perf_counter() - started, 3)})
            print(json.dumps({"model": label, **results[-1]}, ensure_ascii=True), flush=True)
        report["models"][label] = {
            "model_id": model_id, "revision": revision,
            "adapter_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(), "results": results,
        }
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        del model, tokenizer
        gc.collect()


if __name__ == "__main__":
    main()
