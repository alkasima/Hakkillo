"""Update an existing static demo without changing its model or uploading weights."""
import argparse
import json
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--space", default="alkasima/Hakkillo")
parser.add_argument("--report", type=Path, required=True)
args = parser.parse_args()
if args.report.exists():
    parser.error("Use a new report filename to preserve previous deployment records")
api = HfApi()
info = api.space_info(args.space)
if info.sdk != "static":
    parser.error("This publisher only supports an existing static Space")
remote_path = hf_hub_download(args.space, "model.json", repo_type="space", revision=info.sha)
remote = json.loads(Path(remote_path).read_text(encoding="utf-8"))
local = json.loads((root / "web/model.json").read_text(encoding="utf-8"))
if remote != local:
    parser.error("UI-only publishing must preserve the deployed model configuration")
commit = api.upload_folder(
    repo_id=args.space, repo_type="space", folder_path=root / "web",
    allow_patterns=["*.html", "*.css", "*.js", "*.mjs", "model.json"],
    parent_commit=info.sha, commit_message="Add reproducible starter prompts and copyable model feedback",
)
result = {"space": args.space, "previous_space_revision": info.sha, "space_revision": commit.oid,
          "model_configuration_unchanged": True, "model": local,
          "verification": "Upload succeeded; verify runtime and UI separately."}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
