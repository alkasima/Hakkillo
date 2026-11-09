import { feedbackText } from './feedback.mjs';

const $ = (id) => document.getElementById(id);
const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
let busy = false;
let loaded = false;
let history = [];
let responseNode;
let pendingExchange;
let lastExchange;
let modelMetadata;

function setBusy(value) {
  busy = value;
  $('prompt').disabled = value || !loaded;
  $('send').disabled = value || !loaded;
  $('clear').disabled = value || !loaded;
  $('load').disabled = value;
  $('copy-feedback').disabled = value || !lastExchange;
  document.querySelectorAll('.suggestion').forEach((button) => { button.disabled = value || !loaded; });
}

function message(role, text) {
  const element = document.createElement('div');
  element.className = `message ${role}`;
  const speaker = document.createElement('span');
  speaker.className = 'speaker';
  speaker.textContent = role === 'user' ? 'You' : 'Hakkillo';
  const content = document.createElement('span');
  content.textContent = text;
  element.append(speaker, content);
  $('messages').append(element);
  element.scrollIntoView({ block: 'nearest' });
  return content;
}

function fail(error) {
  $('status').textContent = error;
  $('progress').hidden = true;
  if (history.at(-1)?.role === 'user') history.pop();
  if (responseNode && !responseNode.textContent) responseNode.textContent = 'The model could not finish this reply.';
  pendingExchange = null;
  setBusy(false);
}

$('load').addEventListener('click', () => {
  setBusy(true);
  $('status').textContent = 'Preparing your model download…';
  $('progress').hidden = false;
  worker.postMessage({ type: 'load' });
});

worker.addEventListener('message', ({ data }) => {
  if (data.type === 'progress') {
    $('status').textContent = data.message;
    if (data.percent != null) $('progress').value = data.percent;
  } else if (data.type === 'ready') {
    loaded = true;
    modelMetadata = data.metadata;
    $('welcome').hidden = true;
    $('progress').hidden = true;
    $('status').textContent = 'Model ready · messages stay in this browser';
    $('prompt').placeholder = 'Ask a short question in English…';
    setBusy(false);
    $('prompt').focus();
  } else if (data.type === 'token') {
    responseNode.textContent += data.text;
    $('messages').scrollTop = $('messages').scrollHeight;
  } else if (data.type === 'answer') {
    responseNode.textContent = data.text || 'I could not produce an answer. Try a shorter question.';
    history.push({ role: 'assistant', content: data.text });
    history = history.slice(-4);
    lastExchange = { ...pendingExchange, response: data.text };
    pendingExchange = null;
    $('feedback-panel').hidden = false;
    $('status').textContent = `Answered in ${data.seconds}s · experimental model`;
    setBusy(false);
    $('prompt').focus();
  } else if (data.type === 'error') {
    fail(`Could not complete this request: ${data.message}. If loading failed, reload the page to retry.`);
  }
});
worker.addEventListener('error', () => fail('The model worker could not start. Check your connection and reload this page.'));

$('chat-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const text = $('prompt').value.trim();
  if (!loaded || busy || !text) return;
  setBusy(true);
  $('feedback-panel').hidden = true;
  $('feedback-status').textContent = '';
  $('feedback-fallback').hidden = true;
  $('status').textContent = 'Thinking on your CPU…';
  message('user', text);
  responseNode = message('assistant', '');
  const starter = [...document.querySelectorAll('.suggestion')].find((button) => button.dataset.prompt === text);
  pendingExchange = { prompt: text, context: history.map((turn) => ({ ...turn })), case_id: starter?.dataset.case || null };
  history.push({ role: 'user', content: text });
  $('prompt').value = '';
  worker.postMessage({ type: 'generate', messages: history });
});
$('prompt').addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    $('chat-form').requestSubmit();
  }
});
function clearConversation() {
  history = [];
  responseNode = null;
  pendingExchange = null;
  lastExchange = null;
  $('messages').replaceChildren();
  $('prompt').value = '';
  $('feedback-panel').hidden = true;
  $('feedback-fallback').hidden = true;
  $('feedback-fallback').value = '';
  $('feedback-status').textContent = '';
  $('status').textContent = 'New conversation · model stays loaded';
}
$('clear').addEventListener('click', clearConversation);
document.querySelectorAll('.suggestion').forEach((button) => button.addEventListener('click', () => {
  if (busy || !loaded) return;
  clearConversation();
  $('prompt').value = button.dataset.prompt;
  $('chat-form').requestSubmit();
}));
$('copy-feedback').addEventListener('click', async () => {
  if (!lastExchange || !modelMetadata || busy) return;
  const text = feedbackText(lastExchange, modelMetadata);
  try {
    await navigator.clipboard.writeText(text);
    $('feedback-status').textContent = 'Copied. Review the text before posting it.';
  } catch {
    $('feedback-fallback').hidden = false;
    $('feedback-fallback').value = text;
    $('feedback-fallback').focus();
    $('feedback-fallback').select();
    $('feedback-status').textContent = 'Copy the selected text manually, then review it before posting.';
  }
});
fetch('./model.json').then((response) => response.json()).then((config) => {
  if (config.download_mb) $('download-size').textContent = `${config.download_mb} MB`;
}).catch(() => {});
