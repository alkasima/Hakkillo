import { pipeline, env, TextStreamer } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1';

env.allowLocalModels = false;
env.backends.onnx.wasm.numThreads = 1;
let generator;
const system = 'You are Hakkillo, a small English AI assistant. Give clear, brief and helpful answers. If you do not know, say so. You cannot browse the web or take actions.';

self.addEventListener('message', async ({ data }) => {
  try {
    if (data.type === 'load') {
      const response = await fetch('./model.json');
      if (!response.ok) throw new Error('Model configuration is unavailable');
      const config = await response.json();
      generator = await pipeline('text-generation', config.model_id, {
        revision: config.revision,
        device: 'wasm', dtype: 'q8',
        progress_callback: (event) => {
          if (event.status === 'progress') {
            self.postMessage({ type: 'progress', percent: event.progress, message: `Downloading ${event.file}: ${Math.round(event.progress || 0)}%` });
          } else if (event.status === 'done') {
            self.postMessage({ type: 'progress', message: 'Preparing the model for your CPU…' });
          }
        },
      });
      self.postMessage({ type: 'ready' });
    } else if (data.type === 'generate') {
      if (!generator) throw new Error('Load the model first');
      const started = performance.now();
      const messages = [{ role: 'system', content: system }, ...data.messages];
      const streamer = new TextStreamer(generator.tokenizer, {
        skip_prompt: true, skip_special_tokens: true,
        callback_function: (text) => self.postMessage({ type: 'token', text }),
      });
      const output = await generator(messages, {
        max_new_tokens: 64, do_sample: false, repetition_penalty: 1.08, streamer,
      });
      const generated = output[0].generated_text;
      const text = Array.isArray(generated) ? generated.at(-1).content : generated;
      self.postMessage({ type: 'answer', text: text.trim(), seconds: ((performance.now() - started) / 1000).toFixed(1) });
    }
  } catch (error) {
    self.postMessage({ type: 'error', message: error.message || String(error) });
  }
});
