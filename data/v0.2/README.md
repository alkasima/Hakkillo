# Writing experiment — 2026-11-09

The target is short English grammar correction and polite rewriting. These examples were authored and inspected by the AI assistant for this project and are released under Apache-2.0. They are synthetic, with no independent human review and no collected user conversations. The email addresses use reserved example domains.

- `training_pairs.jsonl`: 100 distinct source sentences (50 grammar, 50 politeness), with desired rewrites.
- `train.jsonl`: 200 rendered request variants plus 32 v0.1 examples for replay. The variants are not 200 independent source examples.
- `writing_dev.jsonl`: 50 separate writing prompts used during development (20 grammar, 20 politeness, 10 content-preservation checks).
- `writing_holdout.jsonl`: 20 reserved, source-disjoint examples. Do not run them during this development session or use them to pick hyperparameters. They are visible synthetic data, not a secret or independently authored benchmark.
- `manifest.json`: counts, provenance, and byte-level hashes.

All variants of a source stay in training; splitting after paraphrasing a source would leak it across splits. The builder rejects duplicate source sentences and exact prompt/source overlap across the three splits. This is not semantic deduplication: all sets share task types and grammatical constructions. A final release needs independently written cases and human review.

References are illustrative. A different polite sentence may be equally good. The evaluator reports normalized reference matches and exact preservation of selected names, codes, numbers, and deadlines. These are diagnostics, not semantic accuracy or a human preference score. Even a preserved keyword can appear in a sentence with the wrong meaning; check negation and meaning manually.

Regenerate the training requests with `python scripts/build_writing_data.py`. Do not add development or holdout examples to training. User feedback examples should be separated, stripped of private content where appropriate, and used for training only with suitable permission.
