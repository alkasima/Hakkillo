import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { JSDOM } from 'jsdom';
import { feedbackText } from '../web/feedback.mjs';

const html = await readFile(new URL('../web/index.html', import.meta.url), 'utf8');
const source = (await readFile(new URL('../web/app.js', import.meta.url), 'utf8'))
  .replace("import { feedbackText } from './feedback.mjs';", '')
  .replace('import.meta.url', "'https://demo.test/app.js'");
const metadata = { model_id: 'owner/model', revision: 'loaded-model-revision', library_version: '3.8.1', device: 'wasm CPU', dtype: 'q8', max_new_tokens: 64, repetition_penalty: 1.08 };
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

function setup() {
  const dom = new JSDOM(html, { url: 'https://demo.test/', runScripts: 'outside-only' });
  const window = dom.window;
  let worker;
  let copied;
  window.HTMLElement.prototype.scrollIntoView = () => {};
  window.feedbackText = feedbackText;
  window.fetch = async () => ({ json: async () => ({ download_mb: 141 }) });
  Object.defineProperty(window.navigator, 'clipboard', { configurable: true, value: { writeText: async (text) => { copied = text; } } });
  window.Worker = class {
    constructor() { worker = this; this.handlers = {}; this.sent = []; }
    addEventListener(name, handler) { this.handlers[name] = handler; }
    postMessage(message) { this.sent.push(JSON.parse(JSON.stringify(message))); }
    emit(data) { this.handlers.message({ data }); }
  };
  window.eval(source);
  const get = (id) => window.document.getElementById(id);
  function submit(text) {
    get('prompt').value = text;
    get('chat-form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
  }
  function ready() { get('load').click(); worker.emit({ type: 'ready', metadata }); }
  return { dom, window, get, worker, ready, submit, get copied() { return copied; } };
}

test('all starters are visible before loading, but cannot submit yet', (t) => {
  const app = setup(); t.after(() => app.dom.window.close());
  const buttons = [...app.window.document.querySelectorAll('.suggestion')];
  assert.equal(buttons.length, 3);
  assert.equal(app.get('suggestions').hidden, false);
  assert.ok(buttons.every((button) => button.disabled));
  assert.match(buttons[2].textContent, /Known challenge/);
  buttons[2].click();
  assert.equal(app.worker.sent.length, 0);
});

test('challenge submits the exact prompt in a fresh conversation and copies the version', async (t) => {
  const app = setup(); t.after(() => app.dom.window.close()); app.ready();
  app.submit('An earlier question');
  app.worker.emit({ type: 'answer', text: 'Earlier answer', seconds: '1.0' });
  app.window.document.querySelector('[data-case="rewrite-challenge"]').click();
  assert.deepEqual(app.worker.sent.at(-1).messages, [{ role: 'user', content: 'Rewrite politely: Send me the file now.' }]);
  app.worker.emit({ type: 'answer', text: 'An unhelpful reply', seconds: '1.2' });
  assert.equal(app.get('feedback-panel').hidden, false);
  app.get('copy-feedback').click(); await tick();
  assert.ok(app.copied.includes('Revision: loaded-model-revision'));
  assert.ok(app.copied.includes('Starter case: rewrite-challenge'));
  assert.ok(app.copied.includes('An unhelpful reply'));
  assert.ok(!app.copied.includes('Earlier answer'));
  assert.equal(app.worker.sent.filter((message) => message.type === 'generate').length, 2);
});

test('follow-up feedback copies exactly the context passed to the model', async (t) => {
  const app = setup(); t.after(() => app.dom.window.close()); app.ready();
  for (let i = 0; i < 3; i++) {
    app.submit(`Question ${i}`);
    app.worker.emit({ type: 'answer', text: `Answer ${i}`, seconds: '1.0' });
  }
  app.submit('Please explain that.');
  assert.equal(app.worker.sent.at(-1).messages.length, 5);
  app.worker.emit({ type: 'answer', text: 'Follow-up reply', seconds: '1.0' });
  app.get('copy-feedback').click(); await tick();
  assert.ok(!app.copied.includes('Question 0'));
  assert.ok(app.copied.includes('Question 1'));
  assert.ok(app.copied.includes('Answer 2'));
  assert.ok(app.copied.includes('Please explain that.'));
});

test('clipboard failure exposes a manual copy, and new chat clears it', async (t) => {
  const app = setup(); t.after(() => app.dom.window.close()); app.ready();
  app.window.navigator.clipboard.writeText = async () => { throw new Error('Permission denied'); };
  app.submit('<img src=x onerror=alert(1)>');
  app.worker.emit({ type: 'answer', text: '<script>example</script>', seconds: '1.0' });
  assert.equal(app.get('messages').querySelector('img,script'), null);
  app.get('copy-feedback').click(); await tick();
  assert.equal(app.get('feedback-fallback').hidden, false);
  assert.ok(app.get('feedback-fallback').value.includes('<script>example</script>'));
  app.get('prompt').value = 'Unsent text'; app.get('clear').click();
  assert.equal(app.get('messages').textContent, '');
  assert.equal(app.get('prompt').value, '');
  assert.equal(app.get('feedback-panel').hidden, true);
  assert.equal(app.get('feedback-fallback').value, '');
  assert.equal(app.get('prompt').disabled, false);
});

test('busy state prevents overlapping starter runs; failed prompts leave model context', (t) => {
  const app = setup(); t.after(() => app.dom.window.close()); app.ready();
  app.submit('Fail this request');
  app.window.document.querySelector('[data-case="cpu"]').click();
  assert.equal(app.worker.sent.filter((message) => message.type === 'generate').length, 1);
  app.worker.emit({ type: 'error', message: 'Test failure' });
  app.submit('Next request');
  assert.deepEqual(app.worker.sent.at(-1).messages, [{ role: 'user', content: 'Next request' }]);
});
