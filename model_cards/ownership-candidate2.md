---
language:
- en
license: apache-2.0
library_name: peft
pipeline_tag: text-generation
base_model: HuggingFaceTB/SmolLM2-135M-Instruct
base_model_relation: adapter
tags:
- lora
- cpu
- experimental
- text-generation
---

# Hakkillo-135M v0.2 ownership candidate 2

**Experimental ownership-focused adapter with known regressions.** This continues [writing candidate1](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-writing-candidate1) and improves several ownership rewrites, while worsening some grammar and detail-preservation tasks. It is not a stable release or a reliable general assistant. The [public browser chat](https://huggingface.co/spaces/alkasima/Hakkillo) still runs v0.1.

[Full results and procedure](https://github.com/alkasima/Hakkillo/blob/main/reports/ownership-v1/RESULTS.md) · [Source and data](https://github.com/alkasima/Hakkillo) · [Prerecorded plan](https://github.com/alkasima/Hakkillo/commit/9a54501ff34ac51cfe829efa22e919358190521f)

## What improved

`Lend me your umbrella.` now produces `Could you please lend me your umbrella?` instead of changing `your` to `my` under the original `Rewrite politely:` prompt.

| Separate evaluation group | Previous candidate | This candidate |
|---|---:|---:|
| Known regression cases preserving requirements | 8/12 | 11/12 |
| Familiar-construction development cases | 13/16 | 16/16 |
| Reserved-construction cases | 21/24 | 22/24 |

These are qualitative judgments by the AI coding assistant and coincide with corrected exact reference matches. They are **not general accuracy or independent human evaluation**. The input sets are small and synthetic. See the reference erratum in `evidence/`: one ungrammatical regression reference was corrected for both models without altering frozen inputs, training, or raw outputs.

The reserved patterns were excluded from the new training/development examples and the previous adapter's supervised data. Relative-owner clauses stayed 8/8, owner contrasts improved 7/8 to 8/8, and coordinated owners stayed 6/8. This is limited evidence of transfer, not proof of general ownership reasoning. The base model's pretraining exposure is unknown. After this one fixed run, these reserved cases are now inspected evidence and cannot be called a fresh holdout for later tuning.

## Regressions and remaining failures

The earlier 50-case writing-development set fell from **43/50 to 42/50 reference matches**. The candidate now misses corrections of `I has three pencils` and `can sings`, and changes `coordinator@example.org` into `coordinator at example.org`. It also changes a request to know room availability into a request to indicate availability. These are material failures despite the ownership gains.

Remaining ownership errors include:

- `Send her his draft.` → `Could you please send her her draft?`
- `Return his pencil and her coat.` → `Could you please return his pencil and his coat?`
- `Return our parcel and their badge.` → `Could you please return our parcel and its badge?`

It still invents current Lagos weather, gives poor laptop advice, and ignores some output-format instructions. It has no live web access. All outputs, the per-case review, and prior-task checks are included in `evidence/`. No candidate ONNX/browser validation was performed.

## Training

- Base: Hugging Face's Apache-2.0 `HuggingFaceTB/SmolLM2-135M-Instruct`, revision `12fd25f77366fa6b3b4b768ec3050bf629380bac`, 134,515,008 parameters. Hakkillo was not pretrained from scratch.
- Initial adapter: writing candidate1 at `829fc0b86824c276b8fe9b8a566c7bcd63ab41fb`.
- Data: 128 new synthetic ownership sentences plus 64 replay requests; no community feedback examples or private conversations used for training. A separate 16-case development set supplied the loss check.
- LoRA: q_proj/v_proj, rank 8, alpha 16, dropout 0.05, 460,800 trainable parameters. Fresh AdamW optimizer, continuing adapter weights.
- Fixed run: 384 steps, two passes over 192 requests, learning rate 0.0001, batch size 1, seed 42, four threads, CPU float32, maximum length 256.
- Training and development-loss passes: 473.6 seconds after loading. Development loss: 0.0808 → 0.0009. Historical `held_out_loss_*` metric keys refer to this development set, not the 24 reserved cases.
- PyTorch 2.10.0+cpu, Transformers 5.8.1, PEFT 0.21.2, Python 3.10.
- Adapter SHA-256: `78f34236ea8b49fe05a9b2d1ebdd14f15225f467324047a2e2ce4b8f9e183113`.

No changes to the run followed reserved-output inspection. The older v0.2 reserved holdout was not generated or scored.

## Try locally

This repository contains a roughly 1.9 MB LoRA adapter, not the base model. Clone [Hakkillo](https://github.com/alkasima/Hakkillo), install its dependencies, and run from the project folder in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
$env:HAKKILLO_ADAPTER = 'alkasima/Hakkillo-135M-v0.2-ownership-candidate2'
$env:HAKKILLO_ADAPTER_REVISION = 'dc84ca9bd32a62497988a27e298b12dcd1388291'
$env:HAKKILLO_MODEL_LABEL = 'Hakkillo ownership candidate 2 - experimental'
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:7860`. The first run needs the base weights, about 270 MB, plus the adapter. RAM and dependency storage requirements exceed the download size. For reproducibility set `HAKKILLO_ADAPTER_REVISION` to the publication commit recorded in the project's `reports/ownership-v1/publication.json`.

Check every rewrite for ownership, names, negation, actions, and exact details. Share reproducible failures through the source repository's issue tracker after reviewing the text for private information.
