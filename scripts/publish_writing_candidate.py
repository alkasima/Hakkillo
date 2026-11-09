"""Publish the measured writing candidate as an explicitly experimental adapter."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
from huggingface_hub.errors import RepositoryNotFoundError

ROOT = Path(__file__).resolve().parents[1]
REPO = "alkasima/Hakkillo-135M-v0.2-writing-candidate1"
ADAPTER = ROOT / "artifacts/hakkillo-135m-v0.2-writing-candidate1"
REPORT = ROOT / "reports/v0.2/publication.json"
EXPECTED_SHA = "6772cf97cde238a51aecd7eb8419aca100d4b43a6ce017800b3d20da08f49a84"
FILES = (
    "adapter_model.safetensors", "adapter_config.json", "tokenizer.json",
    "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja",
    "training_metrics.json",
)
EVIDENCE = (
    "candidate1-training.json", "writing-baseline.json", "writing-candidate1.json",
    "writing-no-repetition-penalty.json", "general-candidate1.json",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if REPORT.exists():
        raise SystemExit("Publication record already exists; preserve it and use a new release.")
    weights = ADAPTER / "adapter_model.safetensors"
    if sha256(weights) != EXPECTED_SHA:
        raise SystemExit("Adapter checksum differs from the evaluated candidate.")
    metrics = json.loads((ADAPTER / "training_metrics.json").read_text(encoding="utf-8"))
    recorded = json.loads((ROOT / "reports/v0.2/candidate1-training.json").read_text(encoding="utf-8"))
    if metrics != recorded or metrics["release"] != "0.2.0-writing-candidate1":
        raise SystemExit("Training evidence does not match this candidate.")
    operations = [CommitOperationAdd(path_in_repo=name, path_or_fileobj=ADAPTER / name)
                  for name in FILES if (ADAPTER / name).is_file()]
    operations += [CommitOperationAdd(path_in_repo=name, path_or_fileobj=ROOT / name)
                   for name in ("LICENSE", "NOTICE")]
    operations.append(CommitOperationAdd(path_in_repo="README.md",
                      path_or_fileobj=ROOT / "model_cards/writing-candidate1.md"))
    operations += [CommitOperationAdd(path_in_repo="evidence/" + name,
                   path_or_fileobj=ROOT / "reports/v0.2" / name) for name in EVIDENCE]
    operations += [CommitOperationAdd(path_in_repo="evidence/data-" + name,
                   path_or_fileobj=ROOT / "data/v0.2" / name) for name in ("README.md", "manifest.json")]
    api = HfApi()
    if api.whoami()["name"] != REPO.split("/")[0]:
        raise SystemExit("Sign in as the intended model owner before publishing.")
    try:
        info = api.model_info(REPO)
    except RepositoryNotFoundError:
        info = None
    if info and any(f.rfilename == "adapter_model.safetensors" for f in info.siblings):
        raise SystemExit("Candidate weights already published; inspect the existing release before retrying.")
    api.create_repo(REPO, repo_type="model", private=False, exist_ok=True)
    commit = api.create_commit(repo_id=REPO, operations=operations,
                              commit_message="Publish experimental v0.2 writing candidate with measured evidence")
    remote = Path(hf_hub_download(REPO, "adapter_model.safetensors", revision=commit.oid))
    if sha256(remote) != EXPECTED_SHA:
        raise SystemExit("Published weights failed checksum verification.")
    result = {
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_status": "experimental prerelease; not promoted to browser chat",
        "model_id": REPO, "model_url": "https://huggingface.co/" + REPO,
        "revision": commit.oid, "adapter_sha256": EXPECTED_SHA,
        "downloaded_weight_checksum_verified": True,
        "reserved_holdout_generated_or_scored": False,
        "independent_human_review_completed": False,
        "candidate_onnx_or_browser_evaluation_completed": False,
        "browser_model": json.loads((ROOT / "web/model.json").read_text(encoding="utf-8")),
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
