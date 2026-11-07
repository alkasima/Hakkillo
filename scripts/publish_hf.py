"""Publish the adapter; optionally publish a server Space for an eligible account."""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huggingface_hub import HfApi, get_token

from hakkillo.settings import BASE_MODEL, BASE_REVISION, DEFAULT_ADAPTER, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--model-name", default="Hakkillo-135M-v0.1")
    parser.add_argument("--space-name", default="Hakkillo")
    parser.add_argument("--gradio", action="store_true", help="Also deploy a Gradio server Space; account eligibility is required")
    args = parser.parse_args()
    if not get_token():
        parser.error("Sign in first with: .venv\\Scripts\\hf.exe auth login (use a write-enabled token)")
    api = HfApi()
    identity = api.whoami()
    owners = {identity["name"]} | {org["name"] for org in identity.get("orgs", [])}
    if args.owner not in owners:
        parser.error(f"The signed-in account cannot publish as {args.owner}")
    for name in ("adapter_config.json", "adapter_model.safetensors", "training_metrics.json"):
        if not (args.adapter / name).is_file():
            parser.error(f"Missing {name}; run training first")
    metrics = json.loads((args.adapter / "training_metrics.json").read_text(encoding="utf-8"))
    model_id = f"{args.owner}/{args.model_name}"
    space_id = f"{args.owner}/{args.space_name}"
    model_card = f"""---
language:
- en
license: apache-2.0
library_name: peft
base_model: {BASE_MODEL}
base_model_relation: adapter
pipeline_tag: text-generation
tags:
- lora
- cpu
- experimental
---

# Hakkillo 135M v0.1

An experimental English assistant adaptation of [{BASE_MODEL}](https://huggingface.co/{BASE_MODEL}).
This repository contains **LoRA adapter weights**, not a standalone model or a model pretrained from scratch.
The original base weights and tokenizer are required and are downloaded automatically by the example below.

- Code and data: https://github.com/alkasima/Hakkillo
- Demo: https://huggingface.co/spaces/{space_id}
- Base revision: `{BASE_REVISION}`
- Base parameters: {metrics['base_parameters']:,}
- Trainable adapter parameters: {metrics['trainable_parameters']:,}
- Training: {metrics['steps']} CPU steps; batch size 1; float32; LoRA rank 8; learning rate {metrics['learning_rate']}
- Data: {metrics['training_examples']} project-authored synthetic training examples; {metrics['evaluation_examples']} separate development examples
- Seed: {metrics['seed']}

## Evaluation and limitations

Held-out assistant-token loss: **{metrics['held_out_loss_before']:.4f} before**, **{metrics['held_out_loss_after']:.4f} after**.
This tiny synthetic development set does not establish general improvement. No broad benchmark or safety validation is claimed.
The model can hallucinate, repeat itself, misunderstand instructions, and produce incorrect answers. It has no live information or tools.
Observed v0.1 failures include inventing current Lagos weather, an incorrect evaporation analogy, and mistaking a rewriting request for a request to access a file. The small development loss improvement does not resolve these failures.
Use it for experimentation and simple English tasks. It is not validated for high-stakes decisions or multilingual use.
See `training_metrics.json` for the run record and data hashes, and the code repository for qualitative comparisons.

## Run

Install the pinned `requirements.txt` from the code repository (Python 3.10 or 3.11), then:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

torch.set_num_threads(4)
base = "{BASE_MODEL}"
revision = "{BASE_REVISION}"
tokenizer = AutoTokenizer.from_pretrained(base, revision=revision)
model = AutoModelForCausalLM.from_pretrained(base, revision=revision, dtype=torch.float32, use_safetensors=True)
model = PeftModel.from_pretrained(model, "{model_id}").eval()
messages = [
    {{"role": "system", "content": "You are Hakkillo, a small English AI assistant. Give clear, brief and helpful answers. If you do not know, say so. You cannot browse the web or take actions."}},
    {{"role": "user", "content": "What is a language model?"}},
]
inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=False)
with torch.inference_mode():
    outputs = model.generate(inputs, attention_mask=torch.ones_like(inputs), max_new_tokens=96, do_sample=False, pad_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(outputs[0, inputs.shape[1]:], skip_special_tokens=True))
```

## Attribution and license

Apache-2.0. The base model was developed by Hugging Face's SmolLM team. Hakkillo adds a small project-specific adaptation.
Changes: LoRA adaptation of attention query/value projections using the included synthetic starter dataset.
Retain the original base model attribution and license when redistributing. See `LICENSE` and `NOTICE`.
"""
    (args.adapter / "README.md").write_text(model_card, encoding="utf-8")
    for name in ("LICENSE", "NOTICE"):
        shutil.copy2(ROOT / name, args.adapter / name)
    api.create_repo(model_id, repo_type="model", private=False, exist_ok=True)
    model_commit = api.upload_folder(
        repo_id=model_id, folder_path=args.adapter,
        allow_patterns=["*.json", "*.safetensors", "*.md", "*.jinja", "LICENSE", "NOTICE"],
        commit_message="Publish experimental Hakkillo v0.1 CPU LoRA adaptation",
    )
    report_path = ROOT / "reports/publishing.json"
    result = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    result.update({"model_url": f"https://huggingface.co/{model_id}", "model_commit": model_commit.oid})
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not args.gradio:
        print(f"Published adapter: https://huggingface.co/{model_id}")
        print("For the free static demo, export ONNX weights and run scripts/publish_browser.py.")
        return
    staging = ROOT / ".publish" / "space"
    staging.mkdir(parents=True, exist_ok=True)
    for name in ("app.py", "requirements.txt", "LICENSE", "NOTICE"):
        shutil.copy2(ROOT / name, staging / name)
    shutil.copytree(ROOT / "hakkillo", staging / "hakkillo", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    (staging / "README.md").write_text(f"""---
title: Hakkillo
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 6.31.0
python_version: '3.10'
app_file: app.py
pinned: false
license: apache-2.0
models:
- {model_id}
short_description: A tiny experimental English assistant running on CPU
---

# Hakkillo

An early 135M English assistant based on SmolLM2, with a small LoRA adaptation.
[Source and roadmap](https://github.com/alkasima/Hakkillo) · [Model card](https://huggingface.co/{model_id})

Runs on the default free CPU Space. The first reply downloads and loads the model.
The app does not write chat transcripts or send them to a paid model API. As a hosted service, messages are processed by this Space on Hugging Face infrastructure.
""", encoding="utf-8")
    api.create_repo(space_id, repo_type="space", space_sdk="gradio", private=False, exist_ok=True)
    api.add_space_variable(space_id, "HAKKILLO_ADAPTER", model_id)
    api.add_space_variable(space_id, "HAKKILLO_ADAPTER_REVISION", model_commit.oid)
    api.add_space_variable(space_id, "GRADIO_SERVER_NAME", "0.0.0.0")
    api.add_space_variable(space_id, "HAKKILLO_THREADS", "2")
    space_commit = api.upload_folder(
        repo_id=space_id, repo_type="space", folder_path=staging,
        allow_patterns=["*.py", "*.txt", "*.md", "LICENSE", "NOTICE", "hakkillo/*.py"],
        commit_message="Launch Hakkillo CPU demo with pinned adapter revision",
    )
    result = {"model_url": f"https://huggingface.co/{model_id}", "model_commit": model_commit.oid,
              "space_url": f"https://huggingface.co/spaces/{space_id}", "space_commit": space_commit.oid}
    (ROOT / "reports/publishing.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("Space uploaded. Verify its build/runtime and test a reply before announcing it as live.")


if __name__ == "__main__":
    main()
