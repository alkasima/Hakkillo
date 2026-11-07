from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_MODEL = "HuggingFaceTB/SmolLM2-135M-Instruct"
BASE_REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
DEFAULT_ADAPTER = ROOT / "artifacts" / "hakkillo-135m-v0.1"
SYSTEM_PROMPT = (
    "You are Hakkillo, a small English AI assistant. "
    "Give clear, brief and helpful answers. "
    "If you do not know, say so. You cannot browse the web or take actions."
)
