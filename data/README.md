# Starter data

`train.jsonl` contains 32 synthetic prompt/response examples authored for this project with AI assistance on 2026-11-07. `eval.jsonl` contains 8 separate development examples. These are released under the repository's Apache-2.0 license. They contain no scraped conversations or user chat logs.

The examples cover identity, short explanations, writing, simple arithmetic, and model limitations. They were inspected for basic correctness. They are too small, narrow, and stylistically similar to establish general capability or safety. Evaluation prompts are visible, so this is a development set, not a secret final test set. Do not repeatedly tune against it and call the result an unbiased benchmark.

Each line must contain nonempty `prompt` and `response` strings. The trainer inserts the same system prompt used by the demo, masks all prompt tokens, and trains only on the assistant response and end token. It rejects duplicate prompts, overlaps between training and evaluation prompts, and examples that exceed the configured length.

Before adding data: record its source, license, collection method, and consent where needed; remove private information; deduplicate; review answers; separate training and evaluation by source or topic. Keep a versioned manifest with counts and hashes. Do not train directly on feedback without review and permission.
