# Prompt-rule experiment: posts for the project owner

Attach `assets/prompt-rule-2026-11-10.png`. These are drafts; no posts or replies have been sent.

## X

I gave Hakkillo a stricter rewrite rule: preserve ownership and meaning.

On 12 examples, it fixed none of 4 ownership errors and introduced a fifth.

Next: targeted training, then rerun these tests.

What would you try next?

#BuildInPublic #AI

## LinkedIn

I tried to fix an AI rewriting mistake with a clearer instruction. A passing test started failing.

I'm building Hakkillo, a tiny English assistant based on SmolLM2-135M-Instruct, on my CPU.

After community feedback about ownership and negation, I tested a stricter prompt that explicitly asked it to preserve names, pronouns, ownership, negation, numbers, and deadlines.

Same model. Same 12 sentences. Same generation settings.

The four existing ownership errors remained, and a fifth appeared.

Input: “Don't lend me your umbrella.”

Current prompt: “Please do not lend me your umbrella.”

Stricter prompt: “Please do not lend me my umbrella.”

It kept the negation but changed the owner. The answer still sounded polite.

This is one prompt experiment on a small set of selected examples, not a general benchmark or proof that prompt rules never work. I reviewed ownership and negation separately so the fluent wording wouldn't hide the mistake.

I haven't deployed this rule or changed the model weights. Next, I plan to test targeted training examples and rerun these checks.

When a clearer prompt fails, what do you investigate first: the training examples, the task framing, or how you evaluate the answer?

Full prompts and results:
https://github.com/alkasima/Hakkillo/blob/main/reports/community/2026-11-10-prompt-rule.md

#BuildInPublic #OpenSourceAI #MachineLearning
