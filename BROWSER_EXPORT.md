# Browser model and free static Space

The static demo runs the actual Hakkillo adaptation, merged into the base model and quantized to int8 ONNX. It is not a wrapper around an unrelated hosted model. The ONNX weight file is about 136.6 MB; the page quotes about 141 MB including tokenizer files. Runtime JavaScript and WebAssembly add a separate download. Modern desktop browsers are the first target; mobile memory/performance varies.

The browser uses Transformers.js 3.8.1, WebAssembly CPU inference, one worker, one WASM thread, at most two previous conversation turns, and at most 64 new tokens per reply. The page does not send chat messages to an inference server. It obtains app code/runtime files from jsDelivr and model files from Hugging Face. Browser caching and offline availability depend on the browser; permanent offline support is not guaranteed.

## Export a new release

Train the adapter first. Keep export tooling separate because Optimum ONNX 0.1.0 uses Transformers 4 while the app uses Transformers 5. A fresh export environment needs additional disk space; allow several GB for dependencies and temporary float32 checkpoints.

```powershell
.\.venv\Scripts\python.exe scripts/merge_for_export.py
python -m venv .venv-export
.\.venv-export\Scripts\python.exe -m pip install --upgrade pip
.\.venv-export\Scripts\python.exe -m pip install --no-cache-dir -r requirements-export.txt
.\.venv-export\Scripts\optimum-cli.exe export onnx --model .export-source --task text-generation-with-past --opset 17 --device cpu artifacts/hakkillo-browser
.\.venv-export\Scripts\python.exe scripts/quantize_browser.py
.\.venv-export\Scripts\python.exe -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('HuggingFaceTB/SmolLM2-135M-Instruct', revision='12fd25f77366fa6b3b4b768ec3050bf629380bac').save_pretrained('artifacts/hakkillo-browser')"
.\.venv-export\Scripts\python.exe scripts/check_onnx.py
.\.venv\Scripts\python.exe scripts/publish_browser.py --owner alkasima
```

On this laptop the export environment shares the existing app environment's packages through a local `.pth` file to avoid duplicating PyTorch. Transformers, PEFT, and Hugging Face Hub are overridden inside the export environment. Use `.venv` for the app and `.venv-export` only for export/check commands. A normal separate environment as above is simpler on a machine with more disk space.

`scripts/check_onnx.py` tests initial empty caches and subsequent cached decoding with ONNX Runtime CPU. The original export reported a small numerical discrepancy from its PyTorch reference (maximum logit difference about 0.00193, above the default 1e-5 tolerance). Structural checking and successful replies establish that the exported pipeline runs, not that it is quality-equivalent. Quantization changes outputs; compare a new export against the original on an independent evaluation set before claiming preserved quality.

## Deploy and verify

The publisher uploads only quantized weights/configuration/tokenizer files, never the large temporary float32 checkpoint. It records the model commit in `web/model.json`, creates a static Space, and uploads `web/`.

Check the Space runtime, open the page, click **Load Hakkillo**, wait for the model to load, and submit a short question. Test a follow-up and **New chat**. A successful upload alone does not verify browser inference. For local website changes, serve `web/` with `python -m http.server 8080 --directory web --bind 127.0.0.1` and reload the page after edits.

The public model and demo source remain Apache-2.0 with upstream attribution. Preserve the old model revisions and publish new versioned repositories when promoting a new trained model.
