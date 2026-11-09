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

## Latest update: 9 November 2026

The [experimental v0.2 writing candidate](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-writing-candidate1) is now published for local CPU testing. On 50 synthetic development prompts it matched 43 references, compared with 13 for v0.1. This is not general accuracy or an independent benchmark. It still makes article, subject, and ownership mistakes.

Read the [results and known failures](https://github.com/alkasima/Hakkillo/blob/main/EXPERIMENTS.md). Independent human review, the reserved holdout, and candidate ONNX/browser evaluation remain pending. The candidate is not used by this browser chat.

[Code and roadmap](https://github.com/alkasima/Hakkillo) · [v0.1 model card](https://huggingface.co/alkasima/Hakkillo-135M-v0.1) · [Writing candidate model card](https://huggingface.co/alkasima/Hakkillo-135M-v0.2-writing-candidate1)
