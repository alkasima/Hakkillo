This experimental checkpoint targets ownership mistakes in polite rewrites. It continues writing candidate1 using 128 new synthetic sentences plus 64 replay requests, trained for 384 CPU steps. For example, “Lend me your umbrella” now preserves “your” in the rewrite.

- Known ownership errors: **4 → 1** across 12 regression cases.
- Cases using sentence constructions reserved before training: **21/24 → 22/24** reference matches.
- Earlier writing development: **43/50 → 42/50** reference matches, including new grammar and email-preservation regressions.

These are small synthetic tests with AI-assisted review, not general accuracy or an independent benchmark. The reserved constructions were excluded from the supervised data and evaluated after the fixed run; they are now inspected evidence. One malformed regression reference was corrected transparently for both models, with frozen files and raw outputs retained.

[Download the experimental adapter](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-ownership-candidate2) · [Full procedure, outputs, and failures](https://github.com/alkasima/Hakkillo/blob/main/reports/ownership-v1/RESULTS.md) · [Plan committed before training](https://github.com/alkasima/Hakkillo/commit/9a54501ff34ac51cfe829efa22e919358190521f)

The candidate still changes ownership in “Send her his draft” and two coordinated-owner cases. It also retains unreliable general answers. **This is not a stable release. The browser chat still runs v0.1.** The Space announcement links to this experiment without changing its model pin.

Validation: 14 Python and 9 JavaScript tests passed locally. Published weights matched the evaluated checksum, and a pinned remote-adapter smoke check reproduced the corrected umbrella rewrite. The Space is RUNNING, its served assets match local files, and the browser model configuration is unchanged. Candidate ONNX/browser evaluation and independent human review remain outstanding.
