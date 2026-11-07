const $ = (id) => document.getElementById(id);
const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
let busy = false;
let loaded = false;
let history = [];
let responseNode;

function setBusy(value) {
  busy = value;
  $('prompt').disabled = value || !loaded;
  $('send').disabled = value || !loaded;
  $('clear').disabled = value || !loaded;
  $('load').disabled = value;
  document.querySelectorAll('.suggestion').forEach((button) => { button.disabled = value; });
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
    $('welcome').hidden = true;
    $('progress').hidden = true;
    $('suggestions').hidden = false;
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
  $('suggestions').hidden = true;
  $('status').textContent = 'Thinking on your CPU…';
  message('user', text);
  responseNode = message('assistant', '');
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
$('clear').addEventListener('click', () => {
  history = [];
  responseNode = null;
  $('messages').replaceChildren();
  $('suggestions').hidden = false;
  $('status').textContent = 'New conversation · model stays loaded';
});
document.querySelectorAll('.suggestion').forEach((button) => button.addEventListener('click', () => {
  $('prompt').value = button.textContent;
  $('chat-form').requestSubmit();
}));
fetch('./model.json').then((response) => response.json()).then((config) => {
  if (config.download_mb) $('download-size').textContent = `${config.download_mb} MB`;
}).catch(() => {});
