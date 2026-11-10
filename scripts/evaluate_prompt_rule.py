"""Compare a fixed rewrite instruction on the same pinned candidate and inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huggingface_hub import hf_hub_download
from peft import PeftModel
from hakkillo.model import load_base, generate_reply
from hakkillo.settings import ROOT, BASE_MODEL, BASE_REVISION, SYSTEM_PROMPT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/community/2026-11-10-prompt-rule.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output filename to preserve earlier evidence.")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    if len({row["id"] for row in data["cases"]}) != len(data["cases"]):
        parser.error("Duplicate case IDs.")
    publication = json.loads((ROOT / "reports/v0.2/publication.json").read_text(encoding="utf-8"))
    weights = Path(hf_hub_download(publication["model_id"], "adapter_model.safetensors", revision=publication["revision"]))
    checksum = hashlib.sha256(weights.read_bytes()).hexdigest()
    if checksum != publication["adapter_sha256"]:
        parser.error("Published candidate checksum does not match the recorded release.")
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": data, "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "base_model": BASE_MODEL, "base_revision": BASE_REVISION,
        "model_id": publication["model_id"], "revision": publication["revision"],
        "adapter_sha256": checksum, "system_prompt": SYSTEM_PROMPT,
        "generation": {"runtime": "Python float32 CPU", "max_new_tokens": 64,
                       "repetition_penalty": 1.08, "do_sample": False, "history": []},
        "training_performed": False, "reserved_holdout_used": False,
        "quality_scoring": "Separate qualitative AI review; no automatic semantic score.",
        "variants": {},
    }
    model, tokenizer = load_base()
    model = PeftModel.from_pretrained(model, publication["model_id"], revision=publication["revision"]).eval()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for label, template in data["variants"].items():
        results = []
        for case in data["cases"]:
            prompt = template.format(sentence=case["sentence"])
            start = time.perf_counter()
            response = generate_reply(model, tokenizer, prompt, max_new_tokens=64, repetition_penalty=1.08)
            row = {"case_id": case["id"], "prompt": prompt, "response": response,
                   "seconds": round(time.perf_counter() - start, 3)}
            results.append(row)
            print(json.dumps({"variant": label, **row}, ensure_ascii=True), flush=True)
        report["variants"][label] = results
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
