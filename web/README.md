---
title: Hakkillo
emoji: 🌱
colorFrom: green
colorTo: gray
sdk: static
app_file: index.html
pinned: false
license: apache-2.0
models:
- alkasima/Hakkillo-135M-v0.1-ONNX
short_description: A tiny English assistant running in your browser
---

# Hakkillo

An experimental 135M English assistant. **This browser chat runs v0.1.** Click Load Hakkillo to download about 141 MB of quantized model and tokenizer files, then chat on this device. Messages are not sent to an inference server. Model files are served by Hugging Face and runtime libraries by jsDelivr.

Try a starter prompt, including the labelled writing challenge. Each starter begins a fresh conversation. After a reply, use **Copy last exchange** to prepare feedback with the prompt, reply, earlier turns used, and exact model revision. Review the text before posting; nothing is submitted automatically.

## Latest update: 12 November 2026

The [experimental ownership candidate2](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-ownership-candidate2) is published for local CPU testing. Targeted training reduced ownership errors from 4 to 1 in 12 known cases. On 24 cases using constructions reserved before training, reference matches improved from 21 to 22. The earlier 50-case writing set fell from 43 to 42 reference matches, including grammar and email-preservation regressions. These small synthetic checks are not general accuracy or an independent benchmark.

Read the [results, frozen plan, and regressions](https://github.com/alkasima/Hakkillo/blob/main/reports/ownership-v1/RESULTS.md). The reserved cases are now inspected evidence; future tuning needs a new evaluation design. Independent human review and candidate ONNX/browser validation remain pending. The ownership candidate is not used by this browser chat.

[Code and roadmap](https://github.com/alkasima/Hakkillo) · [v0.1 model card](https://huggingface.co/alkasima/Hakkillo-135M-v0.1) · [Ownership candidate model card](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-ownership-candidate2)
