// Plain text only. Never include the rest of the page or unrelated chat history.
export function feedbackText(exchange, metadata) {
  if (!exchange || !metadata) throw new Error('No completed exchange is available.');
  const context = exchange.context.length
    ? exchange.context.map((turn) => `${turn.role}: ${turn.content}`).join('\n\n')
    : '(Fresh conversation; no earlier turns.)';
  return [
    'Hakkillo model feedback',
    `Model: ${metadata.model_id}`,
    `Revision: ${metadata.revision}`,
    `Runtime: Transformers.js ${metadata.library_version}; ${metadata.device}; ${metadata.dtype}`,
    `Generation: greedy; max_new_tokens=${metadata.max_new_tokens}; repetition_penalty=${metadata.repetition_penalty}`,
    `Starter case: ${exchange.case_id || 'custom prompt'}`,
    '', 'Earlier turns used for this reply:', context,
    '', 'Prompt:', exchange.prompt,
    '', 'Actual reply:', exchange.response,
    '', 'What I expected / what went wrong:', '(Please add your explanation.)',
  ].join('\n');
}
