# Hakkillo v0.1: experimental release

Date: 2026-11-07. Foundation: SmolLM2-135M-Instruct, 134,515,008 parameters. Adaptation: 460,800 LoRA parameters; saved adapter weights: 1,858,776 bytes.

The first local CPU experiment completed 48 steps on 32 synthetic examples. Training plus the two development-loss passes took 41.85 seconds after model loading. Loss on 8 separate development examples decreased from 2.8116 to 2.5544. These are narrow development results, not a general benchmark. Package versions and data hashes are in `training_metrics.json`.

## Qualitative review

Eight additional prompts were run through the base model and Hakkillo with the same Hakkillo system prompt, greedy decoding, repetition penalty 1.08, and an 80-token reply limit. All outputs and measured response times are preserved in `generation_review.json`. This is an informal, non-blind review, not a scored benchmark.

| Case | Observation |
|---|---|
| 7 + 5 | Hakkillo answered 12; the base began with 12 then continued with incorrect operations. Hakkillo still ignored “just the number.” |
| Nigerian capital | Both answered Abuja correctly. |
| Short summary | Both produced a reasonable but incomplete summary, omitting the shoots. |
| Evaporation | Both used an incorrect hot-stove analogy. |
| Polite rewriting | Both misunderstood the task as a request to access a file. |
| Laptop charging | Both gave unreliable troubleshooting suggestions. |
| Current weather | Both invented live conditions despite the system prompt saying there is no browsing. |
| Introduction | Neither included the Hakkillo name in this particular phrasing. |

The lower development loss and one improved arithmetic answer are encouraging pipeline signals. They do not establish a useful general assistant. v0.1 is a working foundation for training, hosting, and learning.

## Next experiment

Prioritize a single task, such as short rewriting. Build independent evaluation prompts before expanding the training data. Include varied rewriting instructions and negative examples of confusing rewriting with taking an action. Separately evaluate unsupported claims about live information. Use reviewed, varied examples instead of repeating these eight review prompts in training.

Keep this release available for comparison. Publish a new version only after measuring the intended improvement and checking regressions.

## Browser edition

The free static Space uses the merged Hakkillo weights converted to ONNX and dynamically quantized (int8 MatMul and Gather). The weight file is about 136.6 MB, plus tokenizer and browser runtime downloads. It runs on the visitor's CPU.

The float32 export's maximum logit difference from its PyTorch reference was about 0.00193, above the exporter's strict default tolerance. ONNX structural validation and cached CPU generation completed successfully. In the quantized three-prompt runtime check, the model explained a CPU and answered Abuja, but produced an incomplete arithmetic response. The original float32 adapter answered that arithmetic prompt correctly, so this is an observed quantization/runtime regression. The browser model should not inherit the adapter's development loss as its own score.

See `browser_runtime_check.json` for the raw CPU outputs. Browser UI verification is recorded separately after deployment.
