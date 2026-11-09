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

# Hakkillo-135M v0.2 writing candidate 1

**Experimental LoRA adapter for English grammar correction and polite rewriting.** Published on 2026-11-09 for inspection and local testing. This is a development candidate, not a stable v0.2 release. The [public browser demo](https://huggingface.co/spaces/alkasima/Hakkillo) still runs v0.1.

[Source, training data and roadmap](https://github.com/alkasima/Hakkillo) · [Experiment report](https://github.com/alkasima/Hakkillo/blob/main/EXPERIMENTS.md) · [Report a reproducible problem](https://github.com/alkasima/Hakkillo/issues/new)

Hakkillo adapts Hugging Face's Apache-2.0 [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct). It was not pretrained from scratch. This repository contains the approximately 1.9 MB adapter, tokenizer, license, and measured evidence; it requires the base model to generate text.

## What changed

For `Rewrite politely: Send me the file now.`, v0.1 responded as if asked to access a file. This candidate produced `Could you please send me the file now?` in the Python CPU smoke check.

All three models were compared on the same 50 synthetic development prompts using float32 CPU inference, greedy decoding, a 64-token answer limit, and repetition penalty 1.08:

| Development diagnostic | Base model | Hakkillo v0.1 | This candidate |
|---|---:|---:|---:|
| Reference matches / 50 | 12 | 13 | 43 |
| Grammar references / 20 | 8 | 8 | 17 |
| Polite-rewrite references / 20 | 0 | 0 | 16 |
| Content-preservation references / 10 | 4 | 5 | 10 |
| Selected literal checks / 16 | 11 | 9 | 16 |

These are reference matches after whitespace normalization, **not semantic accuracy or a general benchmark**. Case and punctuation still matter, and valid alternative wording may fail a reference match. The literal checks miss some subject and ownership errors. The data and review were produced by an AI assistant, not independent human evaluators. Development prompts were used to measure progress. The separate 20-prompt reserved holdout has not been generated, scored, or used for model selection.

Raw outputs and training metrics are included under `evidence/`. The metrics file's historical `held_out_loss_*` keys refer to the **50-prompt development set**, not the reserved holdout.

## Known limitations

- Failed to fix `a honest worker` to `an honest worker`; v0.1 got this example right.
- Changed `Does she likes oranges?` to `Does Hakkillo like oranges?`, changing the subject.
- Changed `your umbrella` to `my umbrella` in a polite rewrite, changing ownership.
- Still fabricated current Lagos weather, gave poor laptop troubleshooting advice, and ignored some requested output formats in a small general smoke check.

Use short English writing requests and check that names, pronouns, numbers, and meaning are preserved. It has no live web access and is not a reliable general assistant. Independent human review, reserved-holdout evaluation, and ONNX/browser validation remain outstanding. No improvement in browser inference or general assistant reliability is claimed.

## Training and provenance

- Base: `HuggingFaceTB/SmolLM2-135M-Instruct`, pinned at `12fd25f77366fa6b3b4b768ec3050bf629380bac` (134,515,008 parameters).
- LoRA: query/value projections, rank 8, alpha 16, dropout 0.05; 460,800 trainable parameters.
- Data: 100 synthetic source sentence pairs, two prompt variants each, plus 32 v0.1 replay examples: **232 training requests**. No user conversations were used. Training data is Apache-2.0; see the source repository's `data/v0.2/README.md` and manifest.
- Training: CPU float32, four threads, 464 steps, batch size 1, learning rate 0.0003, seed 42, maximum sequence length 256.
- Training plus development-loss passes: 612 seconds after model loading. Development assistant-token loss: 0.6494 before, 0.0643 after. This does not establish performance on independent tasks.
- Environment: Python 3.10, PyTorch 2.10.0+cpu, Transformers 5.8.1, PEFT 0.21.2.
- Adapter SHA-256: `6772cf97cde238a51aecd7eb8419aca100d4b43a6ce017800b3d20da08f49a84`.

## Try it on a CPU

Clone [the project](https://github.com/alkasima/Hakkillo), then run these commands from its directory in PowerShell (Python 3.10 or 3.11):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
$env:HAKKILLO_ADAPTER = 'alkasima/Hakkillo-135M-v0.2-writing-candidate1'
$env:HAKKILLO_MODEL_LABEL = 'Hakkillo writing candidate 1 - experimental'
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:7860`. The first model load downloads the base weights, about 270 MB, plus this adapter. Float32 inference and Python dependencies need more RAM and disk space than those downloads. The local app does not save chat transcripts.

For reproducible work, use the model commit recorded in the project's `reports/v0.2/publication.json` as the `revision` argument to `PeftModel.from_pretrained`. The project's loader already pins the base model. Its system prompt is:

> You are Hakkillo, a small English AI assistant. Give clear, brief and helpful answers. If you do not know, say so. You cannot browse the web or take actions.

## Next release checks

Review meaning and tone with independently written examples, address article and pronoun failures, then evaluate a selected candidate on the reserved holdout. Compare Python and quantized ONNX results before promoting any candidate to the public browser chat.
