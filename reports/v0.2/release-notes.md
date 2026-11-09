Hakkillo's first writing candidate is available for local CPU testing. The adapter targets grammar correction and polite rewriting: for example, it changes “Send me the file now” into “Could you please send me the file now?” where v0.1 treated the request as file access.

- [Download the experimental adapter and read its model card](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-writing-candidate1).
- [Read the experiment, raw results, and known failures](https://github.com/alkasima/Hakkillo/blob/main/EXPERIMENTS.md).
- [Visit the public demo](https://huggingface.co/spaces/alkasima/Hakkillo), with starter prompts, a labelled challenge, and copyable feedback. **Its chat still runs v0.1.** The candidate has not been exported or validated for the browser.

On the same 50 synthetic development prompts, reference matches were 12/50 for the base, 13/50 for v0.1, and 43/50 for this candidate. These are whitespace-normalized reference matches, **not general accuracy or an independent benchmark**. Training used 232 requests (100 source pairs with two prompt variants, plus 32 replay examples), 464 CPU steps, and about 10 minutes after loading.

This is an experimental prerelease, not stable v0.2. Article, subject, and ownership mistakes remain. The candidate still fabricates current weather and gives poor troubleshooting advice. Independent human review, the reserved holdout, and candidate ONNX/browser validation remain pending.

The exact Hugging Face revision and adapter checksum are recorded in `reports/v0.2/publication.json`. Code, data, model cards, and measured evidence are available under Apache-2.0. Hakkillo adapts Hugging Face's SmolLM2-135M-Instruct; it is not pretrained from scratch.
