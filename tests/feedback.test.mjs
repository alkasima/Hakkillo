import test from 'node:test';
import assert from 'node:assert/strict';
import { feedbackText } from '../web/feedback.mjs';

const metadata = { model_id: 'owner/model', revision: 'fixed-revision', library_version: '3.8.1', device: 'wasm CPU', dtype: 'q8', max_new_tokens: 64, repetition_penalty: 1.08 };

test('feedback records the actual model revision, settings, and exchange', () => {
  const text = feedbackText({ prompt: 'Rewrite this.', response: 'A reply.', context: [], case_id: 'rewrite-challenge' }, metadata);
  assert.ok(text.includes('Revision: fixed-revision'));
  assert.ok(text.includes('repetition_penalty=1.08'));
  assert.ok(text.includes('Starter case: rewrite-challenge'));
  assert.ok(text.includes('Prompt:\nRewrite this.\n\nActual reply:\nA reply.'));
  assert.ok(text.includes('Fresh conversation; no earlier turns.'));
});

test('a follow-up includes the context needed to reproduce it', () => {
  const text = feedbackText({ prompt: 'Make it shorter.', response: 'Short.', context: [{ role: 'user', content: 'Explain a CPU.' }, { role: 'assistant', content: 'A long explanation.' }] }, metadata);
  assert.ok(text.includes('user: Explain a CPU.'));
  assert.ok(text.includes('assistant: A long explanation.'));
  assert.ok(text.includes('Starter case: custom prompt'));
});

test('unrelated page data is excluded and text stays literal', () => {
  const text = feedbackText({ prompt: '<script>example</script>', response: 'Text', context: [], unrelated_history: 'DO_NOT_INCLUDE' }, { ...metadata, private_value: 'ALSO_DO_NOT_INCLUDE' });
  assert.ok(text.includes('<script>example</script>'));
  assert.ok(!text.includes('DO_NOT_INCLUDE'));
});

test('copying before a completed response is rejected', () => {
  assert.throws(() => feedbackText(null, metadata));
  assert.throws(() => feedbackText({}, null));
});
