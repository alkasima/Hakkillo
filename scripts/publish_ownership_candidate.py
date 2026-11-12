"""Publish the completed ownership experiment with its measured limitations."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
from huggingface_hub.errors import RepositoryNotFoundError

ROOT = Path(__file__).resolve().parents[1]
REPO = "alkasima/Hakkillo-135M-v0.2-ownership-candidate2"
ADAPTER = ROOT / "artifacts/hakkillo-135m-v0.2-ownership-candidate2"
REPORTS = ROOT / "reports/ownership-v1"
EXPECTED_SHA = "78f34236ea8b49fe05a9b2d1ebdd14f15225f467324047a2e2ce4b8f9e183113"


def main():
    record = REPORTS / "publication.json"
    if record.exists():
        raise SystemExit("Publication already recorded; preserve the existing release.")
    digest = hashlib.sha256((ADAPTER / "adapter_model.safetensors").read_bytes()).hexdigest()
    if digest != EXPECTED_SHA:
        raise SystemExit("Adapter differs from the evaluated candidate.")
    comparison = json.loads((REPORTS / "comparison.json").read_text(encoding="utf-8"))
    if not comparison["completed"] or comparison["candidate2_adapter_sha256"] != digest:
        raise SystemExit("Completed comparison does not match the adapter.")
    review = json.loads((REPORTS / "review.json").read_text(encoding="utf-8"))
    if review["raw_outputs_sha256"] != hashlib.sha256((REPORTS / "comparison.json").read_bytes()).hexdigest():
        raise SystemExit("Review does not refer to these raw outputs.")
    metrics = json.loads((ADAPTER / "training_metrics.json").read_text(encoding="utf-8"))
    if metrics != json.loads((REPORTS / "candidate2-training.json").read_text(encoding="utf-8")):
        raise SystemExit("Training metrics differ from the recorded run.")
    operations = []
    for name in ("adapter_model.safetensors", "adapter_config.json", "tokenizer.json", "tokenizer_config.json",
                 "special_tokens_map.json", "chat_template.jinja", "training_metrics.json"):
        if (ADAPTER / name).is_file():
            operations.append(CommitOperationAdd(path_in_repo=name, path_or_fileobj=ADAPTER / name))
    operations += [CommitOperationAdd(path_in_repo=name, path_or_fileobj=ROOT / name) for name in ("LICENSE", "NOTICE")]
    operations.append(CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=ROOT / "model_cards/ownership-candidate2.md"))
    for name in ("comparison.json", "review.json", "candidate2-training.json", "plan.json"):
        operations.append(CommitOperationAdd(path_in_repo="evidence/" + name, path_or_fileobj=REPORTS / name))
    markdown = (REPORTS / "RESULTS.md").read_text(encoding="utf-8")
    def source_link(match):
        target = match.group(1)
        if target.startswith("https://"):
            return match.group(0)
        relative = (REPORTS / target).resolve().relative_to(ROOT).as_posix()
        return "](https://github.com/alkasima/Hakkillo/blob/main/" + relative + ")"
    markdown = re.sub(r"\]\(([^)]+)\)", source_link, markdown)
    operations.append(CommitOperationAdd(path_in_repo="evidence/RESULTS.md", path_or_fileobj=markdown.encode("utf-8")))
    for name in ("reference-errata.json", "manifest.json"):
        operations.append(CommitOperationAdd(path_in_repo="evidence/" + name, path_or_fileobj=ROOT / "data/ownership-v1" / name))
    api = HfApi()
    if api.whoami()["name"] != "alkasima":
        raise SystemExit("Sign in as the intended owner before publishing.")
    try:
        info = api.model_info(REPO)
    except RepositoryNotFoundError:
        info = None
    if info and any(f.rfilename == "adapter_model.safetensors" for f in info.siblings):
        raise SystemExit("Weights already published; inspect that release before retrying.")
    api.create_repo(REPO, repo_type="model", private=False, exist_ok=True)
    commit = api.create_commit(repo_id=REPO, operations=operations,
                              commit_message="Publish experimental ownership candidate with gains and regressions")
    remote = Path(hf_hub_download(REPO, "adapter_model.safetensors", revision=commit.oid))
    if hashlib.sha256(remote.read_bytes()).hexdigest() != EXPECTED_SHA:
        raise SystemExit("Published weights failed checksum verification.")
    result = {"published_at_utc": datetime.now(timezone.utc).isoformat(), "model_id": REPO,
              "model_url": "https://huggingface.co/" + REPO, "revision": commit.oid,
              "adapter_sha256": EXPECTED_SHA, "downloaded_weight_checksum_verified": True,
              "status": "Experimental ownership checkpoint with broader writing regressions; not promoted to browser",
              "reserved_evaluation": "24 cases generated once per model after the fixed run; now inspected evidence",
              "candidate_onnx_or_browser_evaluation_completed": False,
              "browser_model": json.loads((ROOT / "web/model.json").read_text(encoding="utf-8"))}
    record.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
