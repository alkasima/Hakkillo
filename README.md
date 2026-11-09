# Hakkillo

**A small English AI assistant, growing through measured improvements.**

[Try Hakkillo](https://huggingface.co/spaces/alkasima/Hakkillo) · [Adapter weights](https://huggingface.co/alkasima/Hakkillo-135M-v0.1) · [Browser weights](https://huggingface.co/alkasima/Hakkillo-135M-v0.1-ONNX) · [Roadmap](VISION.md)

Hakkillo starts with [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct), an Apache-2.0 model that can run on a CPU. The first experiment adds a small LoRA adapter: a separate set of trained weights that changes the base model's behavior without retraining all its parameters.

This is an early learning and development release. It is not pretrained from scratch and is not competitive with large assistants. Its starter dataset is deliberately tiny; lower loss on that dataset does not establish general improvement.

## Quick start on Windows

Use Python 3.10 or 3.11 and Git. From this project directory:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:7860**. The first reply downloads the base model (about 270 MB of weights); subsequent runs use the local cache. Allow a few GB of free disk space for Python dependencies and model files. Model execution uses CPU float32, so memory usage is larger than the download size. The local app binds to your computer only and does not write chat transcripts.

The hosted Space uses a separate browser runtime: a static website downloads about 141 MB of model/tokenizer files and runs the merged, quantized Hakkillo model on the visitor's CPU. It needs no API key. Responses may differ from the Python adapter because of quantization and runtime differences. See [browser export instructions](BROWSER_EXPORT.md).

The demo has three starter prompts, including a labelled rewriting challenge that v0.1 struggles with. Each starter opens a fresh conversation. After a reply, **Copy last exchange** prepares the prompt, response, earlier turns used, and exact model revision for a reproducible report. Review the copied text before posting it to GitHub; the app does not submit feedback automatically.

Until an adapter is available, the app explicitly shows **base-model preview**. To download the published Hakkillo adapter, once it is available:

```powershell
$env:HAKKILLO_ADAPTER = 'alkasima/Hakkillo-135M-v0.1'
.\.venv\Scripts\python.exe app.py
```

## Train a first adaptation

```powershell
.\.venv\Scripts\python.exe scripts/train.py
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe app.py
```

The default run uses 32 synthetic examples, 8 separate development examples, 48 steps, batch size 1, and four CPU threads. Only the attention query/value LoRA weights train; base weights stay frozen. The trainer masks system/user tokens, checks for prompt overlap, and saves the actual before/after loss and data hashes. It refuses to overwrite an existing run.

Outputs:

- `artifacts/hakkillo-135m-v0.1/`: local adapter weights and tokenizer; excluded from Git.
- `reports/training_metrics.json`: run settings, hashes, and measured development losses.
- `reports/generation_review.json`: base and Hakkillo answers to the same prompts, with latency.

When the default local adapter exists, the app loads it automatically. For a new experiment, preserve the first run:

```powershell
.\.venv\Scripts\python.exe scripts/train.py --output artifacts/experiment-002 --steps 96
.\.venv\Scripts\python.exe scripts/evaluate.py --adapter artifacts/experiment-002 --output reports/experiment-002-review.json
$env:HAKKILLO_ADAPTER = (Resolve-Path artifacts/experiment-002).Path
.\.venv\Scripts\python.exe app.py
```

Each training command starts from the same pinned base model. It does not resume an earlier adapter. More steps can cause overfitting; compare outputs before choosing a release.

## Publish to Hugging Face

GitHub stores the code, data, and reports. One Hugging Face **model repository** stores the adapter; another stores merged quantized ONNX weights. A free **static Space** hosts the browser demo.

Sign in locally using a token with write access. Never place tokens in source files or chat messages:

```powershell
.\.venv\Scripts\hf.exe auth login
.\.venv\Scripts\python.exe scripts/publish_hf.py --owner alkasima
```

This publishes the adapter to `alkasima/Hakkillo-135M-v0.1` and generates the model card from measured results. After completing [browser export](BROWSER_EXPORT.md), publish the free browser demo:

```powershell
.\.venv\Scripts\python.exe scripts/publish_browser.py --owner alkasima
```

The browser publisher creates `alkasima/Hakkillo-135M-v0.1-ONNX` and the static Space `alkasima/Hakkillo`, pinning its model download to an exact commit. During this setup, Hugging Face required a PRO subscription for Gradio/Docker CPU hosting on this account; static Spaces were available without that subscription. The project requests no paid hardware. The Python Gradio app remains available locally. An optional `--gradio --space-name Hakkillo-server` flag on the adapter publisher is available for accounts eligible for server hosting.

Model weights are never committed to GitHub. `reports/publishing.json` records successful Hugging Face uploads; hosted runtime verification is recorded separately.

## Project map

| Location | Purpose |
|---|---|
| `app.py` | Local and hosted chat demo |
| `hakkillo/` | Model loading, inference, training-data checks |
| `data/` | Licensed synthetic starter data and provenance |
| `scripts/train.py` | CPU LoRA training and held-out loss |
| `scripts/evaluate.py` | Side-by-side output review |
| `scripts/publish_hf.py` | Adapter publishing |
| `web/` | Static browser chat demo |
| `scripts/publish_browser.py` | ONNX model and static Space publishing |
| `VISION.md` | Product direction and release gates |
| `reports/` | Recorded evidence, not estimated scores |

## Limits and attribution

Short English prompts are the initial focus. The model can produce incorrect facts, arithmetic errors, repetitions, and poor instruction following. It has no tools, browsing, or durable memory. Do not treat it as a source of verified medical, legal, or financial decisions. The static demo processes chat in the visitor's browser and does not transmit messages to an inference service. It downloads model files from Hugging Face and JavaScript/runtime assets from jsDelivr. The local Python app does not save chat transcripts.

Hugging Face's SmolLM team created the underlying model. Hakkillo adds the project, examples, and experimental adaptation. Code and adaptation are Apache-2.0; see [LICENSE](LICENSE), [NOTICE](NOTICE), and the [upstream model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct).
