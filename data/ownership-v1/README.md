# Ownership experiment — 12 November 2026

Synthetic data authored and inspected by the AI assistant, Apache-2.0. No private conversations or feedback examples are added to training. The examples have no independent human review.

- **Train:** 128 new sentence pairs across four constructions, plus 64 replay requests: all 32 starter examples and 16 old grammar sources in their two existing prompt variants. Each new source has one prompt variant.
- **Development:** 16 different sources from the same four training constructions. Only this set supplies the training loss check.
- **Reserved:** 24 cases across three whole constructions excluded from this supervised training: ownership relative clauses (`that belongs to`), contrast with an independent possessive (`not yours`), and two coordinated objects with separate possessors. These are evaluated only after the fixed candidate has finished training.
- **Regression:** the original 12 community/prompt-experiment cases, unchanged as input sentences. Their illustrative reference rewrites were authored for this experiment. They are already familiar development evidence, not a new benchmark.

The audit checks all previous candidate1 training examples as well as the new train/dev data. Regex checks and source/prompt disjointness catch the declared construction families, but do not establish complete semantic separation. We cannot claim these constructions were absent from the base model's pretraining. The reserved cases are visible synthetic data; they are not an independent or secret test.

Data, run settings, and evaluation policy are frozen before training in `reports/ownership-v1/plan.json`. All 24 reserved outputs must be reported, with construction-level results separate from the 12 regressions and 16 familiar-construction development cases. Once evaluated, these reserved cases become inspected evidence and must not be reused as a fresh holdout for later tuning.

The older `data/v0.2/writing_holdout.jsonl` is not used for this experiment. No examples from these new regression or reserved files are copied into training.

The builder refuses to overwrite this directory. Tests verify hashes, split checks, forbidden constructions in training/history, and complete assistant-only targets. See `scripts/build_ownership_data.py` for the reproducible construction logic.
