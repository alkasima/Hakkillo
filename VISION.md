# Hakkillo: direction and release plan

## Vision

Build a small, accessible English assistant that helps people understand concepts, rewrite short text, and learn basic computing. Start with a model that works on the existing CPU laptop. Grow quality through better data and honest evaluation before increasing model size.

The first audience is people who want short, simple explanations and writing help. The initial promise is an approachable experimental assistant, not expert knowledge or reliable autonomous action. Confirm the most useful audience and tasks from real feedback before widening scope.

## Starting decisions

| Decision | Starting choice | Reason |
|---|---|---|
| Foundation | SmolLM2-135M-Instruct, pinned revision | Small, English instruction model; Apache-2.0 |
| Adaptation | LoRA, rank 8, attention query/value projections | Train a small number of weights on CPU |
| Runtime | CPU, float32, bounded context and replies | Works with the current hardware |
| Release artifact | Separate adapter with attribution | Small uploads; no duplicate base weights |
| Interface | Local Gradio chat; static browser Space with quantized ONNX | Accessible CPU demo without a paid inference server |
| Source | Public GitHub repository | Versioned code, data provenance, and evidence |
| First target | Short English explanations and rewriting | A narrower task is easier to evaluate |

The laptop was detected with about 16 GB RAM and an Intel i5-1145G7 CPU. This supports small experiments, but pretraining a useful general model from scratch would require vastly more data and compute. The base model already supplies the expensive pretraining. CPU adaptation is slower than GPU training and should remain small and measured.

## Releases

| Phase | Deliverable | Release gate |
|---|---|---|
| v0.1: working foundation | CPU app, starter adapter, model card, source repository, demo | Training runs; weights reload; before/after outputs recorded; limitations visible; hosted build and reply verified when login is available |
| v0.2: useful narrow task | Choose explanations or rewriting; collect 200–500 reviewed examples | Document source rights; deduplicate; keep a separate final test set; beat the base on the chosen task without material regressions |
| v0.3: better data and usability | Expand only where failures show a need; improve prompting or data; assess quantization | Blind human comparison plus factuality/instruction checks; acceptable latency and memory on the target laptop |
| v0.4: wider evaluation | Independently authored challenge set and feedback process | Report successes and failures by task; avoid tuning on the final test set; review privacy and data permissions |
| Later: larger model if justified | Trial a 360M–1B base or rented/borrowed GPU training | Evidence that the 135M model is the bottleneck; affordable compute; better quality after accounting for latency and RAM |

These phases are decision gates, not promised dates. Avoid scaling merely to produce a larger version number. Additional languages should be chosen with the user, supported by licensed data and native-speaker review, and evaluated separately.

## What “better” means

For a real v0.2 evaluation, build at least 50 independently authored prompts spread across the chosen task and common failure cases. Use a development split for iteration and an untouched final test split for the release decision. Label answers without revealing which model produced them.

Track instruction following, correctness, clarity, unsupported claims, and preference against the unmodified base with the same system prompt and generation settings. Suggested initial release gate: win at least 60% of non-tied human comparisons on the target task, report the sample size and ties, and show no important regression in basic factual questions or handling unknown/live information. This is a project target, not a measured current score.

Track latency, time to first response where measured, RAM, model/adapter size, and startup behavior. Set a latency target after measuring the current laptop; avoid promising real-time responses in advance. Log base revision, code commit, dataset hashes, package versions, seed, and hyperparameters for every candidate.

The v0.1 eight-example development loss is only a pipeline sanity check. Its answers are similar in style to the training data. It must not be advertised as a broad benchmark.

## Improvement loop

1. Record a concrete failure on a target task.
2. Determine whether the cause is unclear prompting, missing context, poor data, or model capacity.
3. Add or fix licensed, reviewed training examples without contaminating evaluation.
4. Run a small experiment from the pinned base and preserve its outputs.
5. Compare against the current release and base model with identical inference settings.
6. Publish only a clearly identified release with evidence and limitations; preserve the previous adapter for rollback.

Training is intentional and versioned. The demo does not silently learn from chats. Collecting user feedback or conversations for training needs a clear consent and retention policy before implementation.

## First backlog after v0.1

- Choose the single most valuable task with a few prospective users.
- Review the recorded base/adapter generations and list specific failures.
- Create an independent evaluation set before expanding the training set.
- Record CPU latency and peak memory; try a quantized inference format only if it improves the actual user experience.
- Add 200–500 reviewed task examples with provenance and split discipline.
- Train several small candidates, choose by evaluation, and publish a new version instead of overwriting v0.1.
