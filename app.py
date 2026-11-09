"""Local and Hugging Face Spaces entry point. No paid APIs or GPU required."""
import os

import gradio as gr

from hakkillo.model import Assistant, adapter_source

assistant = Assistant()


def respond(message, history, max_new_tokens, temperature):
    # Gradio 6 may represent text messages as typed content blocks.
    normalized = []
    for item in history:
        content = item.get("content", "")
        if isinstance(content, list):
            content = "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
        normalized.append({"role": item["role"], "content": content})
    try:
        return assistant.reply(message, normalized, max_new_tokens, temperature)
    except ValueError as error:
        raise gr.Error(str(error)) from error


mode = os.environ.get("HAKKILLO_MODEL_LABEL", "Experimental Hakkillo adaptation") if adapter_source() else "Base-model preview: Hakkillo adapter is not loaded"
demo = gr.ChatInterface(
    fn=respond,
    title="Hakkillo",
    description=(
        f"**A small assistant, growing one release at a time.**\n\n{mode}. "
        "Built on SmolLM2-135M-Instruct. Best for short English answers. "
        "This early model can make mistakes and has no live web access. "
        "The first reply may take longer while the model loads."
    ),
    examples=[
        ["Explain what a language model is in two sentences.", 96, 0],
        ["Help me plan a 20-minute study session.", 96, 0],
        ["What can you help me with?", 96, 0],
    ],
    additional_inputs=[
        gr.Slider(16, 256, value=96, step=16, label="Maximum reply tokens"),
        gr.Slider(0, 1, value=0, step=0.1, label="Creativity (0 = consistent replies)"),
    ],
    cache_examples=False,
    concurrency_limit=1,
    analytics_enabled=False,
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.queue(max_size=12).launch(
        server_name=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.environ.get("PORT", "7860")),
        share=False,
    )
