# Writing candidate — 2026-11-09

For the later ownership training run, see [12 November results](reports/ownership-v1/RESULTS.md), including reserved sentence constructions and broader regressions. This page preserves the first writing candidate's results.

Today’s experiment targets grammar correction and polite rewriting. Its adapter is now published as [Hakkillo-135M-v0.2-writing-candidate1](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-writing-candidate1), an **experimental prerelease for inspection and local testing**. It is not a stable v0.2 release. The public Space still uses the pinned v0.1 ONNX model and links to this candidate. Its starter prompts and feedback-copy controls have been updated in response to the X feedback relayed by the project owner.

## Result

| Development diagnostic | Base model | Hakkillo v0.1 | Writing candidate 1 |
|---|---:|---:|---:|
| Reference matches, all 50 | 12 | 13 | 43 |
| Grammar references, 20 | 8 | 8 | 17 |
| Polite-rewrite references, 20 | 0 | 0 | 16 |
| Content-preservation references, 10 | 4 | 5 | 10 |
| Selected literal checks passed, 16 | 11 | 9 | 16 |

These are whitespace-normalized reference matches and selected literal checks, **not a general accuracy score**. The prompts and training pairs are synthetic and were authored/reviewed by the AI assistant. An equally good alternative rewrite may not match a reference. Some subject/pronoun errors are not captured by the literal checks. The 20-example reserved holdout has not been used for generation, loss measurement, or model selection.

Turning off the repetition penalty on v0.1 yielded 11/50 reference matches and still no polite-reference matches. Its preservation diagnostic improved to 12/16, but that did not establish an overall gain; the existing 1.08 penalty was retained for the candidate comparison. All compared runs use the existing system prompt, greedy decoding, float32 CPU, and a 64-token answer limit.

The candidate trained from the pinned base for 464 steps with LoRA rank 8, learning rate 0.0003, seed 42, batch size 1, and four CPU threads. There are 100 new source sentences, two request variants per source, and 32 v0.1 replay examples: 232 training requests, not 232 independent sources. Training plus two development-loss passes took about 612 seconds after loading. Development loss fell from 0.6494 to 0.0643. This is development evidence, not a release benchmark.

## An improvement and remaining failures

For **“Rewrite politely: Send me the file now.”**, v0.1 refused the request as though asked to access a file. The candidate answered **“Could you please send me the file now?”**

Three clear writing failures remain:

- `g10`: failed to change “a honest worker” to “an honest worker”; v0.1 got this case right.
- `g16`: changed “Does she likes oranges?” into “Does Hakkillo like oranges?” instead of preserving the subject.
- `p07`: changed “your umbrella” to “my umbrella,” altering ownership.

The other four reference mismatches are different wording and need human judgment: “completed” versus “finished,” “stop interrupting me” versus “let me finish speaking,” “fix the spelling” versus “correct the spelling,” and “Could I please know…” versus “Could you please let me know…”. No blind human preference score is claimed.

The original eight-prompt smoke check also ran. The candidate rewrote the file request successfully, gave a correct short definition of evaporation, and retained Abuja and the arithmetic result. It still ignored some output-format instructions, invented live Lagos weather, and gave poor laptop-charging advice. It does not qualify as a reliable general assistant.

## Try the candidate locally

Run from the project folder in PowerShell:

```powershell
$env:HAKKILLO_ADAPTER = 'alkasima/Hakkillo-135M-v0.2-writing-candidate1'
$env:HAKKILLO_ADAPTER_REVISION = '829fc0b86824c276b8fe9b8a566c7bcd63ab41fb'
$env:HAKKILLO_MODEL_LABEL = 'Hakkillo writing candidate 1 — experimental'
.\.venv\Scripts\python.exe app.py
```

First install the dependencies using the README's setup command. Open `http://127.0.0.1:7860` and try short writing requests. These environment variables apply to that terminal session. In a fresh terminal, the app defaults to the original local v0.1 adapter if present, or the base-model preview otherwise. The original local candidate remains at `artifacts/hakkillo-135m-v0.2-writing-candidate1`.

## Reproduce without overwriting earlier runs

```powershell
.\.venv\Scripts\python.exe scripts/build_writing_data.py
.\.venv\Scripts\python.exe scripts/train.py --train data/v0.2/train.jsonl --eval data/v0.2/writing_dev.jsonl --output artifacts/writing-next --steps 464 --learning-rate 0.0003 --release writing-next --report reports/v0.2/writing-next-training.json
.\.venv\Scripts\python.exe scripts/evaluate_writing.py --model writing-next=artifacts/writing-next --training-data data/v0.2/train.jsonl --output reports/v0.2/writing-next-evaluation.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm ci --ignore-scripts --no-audit --no-fund
npm test
```

Choose fresh output paths for each new run. The evaluator refuses to overwrite an existing result, and the trainer keeps metrics inside the run directory. Use `--report` only with a new path. Source sentences and request variants are checked for overlap between train/development/holdout splits.

## Before promoting a stable release or the browser chat

The experimental adapter is public so others can inspect it and reproduce the results. These checks remain outstanding for promotion:

1. Review the actual outputs and the anonymous comparison sheet in `reports/v0.2/`.
2. Add independently written pronoun/ownership and article examples without copying development prompts into training.
3. Once a candidate is selected, evaluate it on the reserved holdout and independently authored user tasks; use human review for meaning and tone.
4. Export that candidate to ONNX and compare its browser results with Python results. Quantization hurt v0.1 on an arithmetic example, so do not assume parity.
5. Publish a stable version with evidence and update the browser model pin only if it passes these checks.

## Files and verification

Raw outputs: `reports/v0.2/writing-baseline.json`, `writing-no-repetition-penalty.json`, `writing-candidate1.json`, and `general-candidate1.json`. Training settings and hashes: `candidate1-training.json`. Data provenance: `data/v0.2/README.md` and `manifest.json`. The training metrics' historical `held_out_loss_*` keys refer to the development set, not the reserved holdout.

`reports/v0.2/publication.json` records the exact Hugging Face model revision and the checksum verification of downloaded weights. The candidate model card and raw measured outputs are also included in the Hugging Face model repository.

The [GitHub prerelease](https://github.com/alkasima/Hakkillo/releases/tag/v0.2.0-writing-candidate1) records the published source. All nine Python and nine JavaScript tests passed locally and in GitHub Actions for that source. A smoke check loading the pinned published adapter reproduced the expected file-request rewrite. See `reports/v0.2/release-verification.json`, `published-smoke.json`, and `space-publication.json` for release and deployment evidence.

The new UI passed nine automated JavaScript tests, including DOM interactions with a mocked model worker. The Space reported `RUNNING`; deployed files matched local files and the feedback module was served as JavaScript. The browser automation tool failed to initialize, so this update has **not** had a fresh visual/interactive browser check. Its deployed model and generation settings were preserved. No feedback is automatically submitted or used for training.
