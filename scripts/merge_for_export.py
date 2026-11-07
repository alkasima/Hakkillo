"""Merge a trained adapter into a temporary Transformers export checkpoint."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from peft import PeftModel
from hakkillo.model import load_base
from hakkillo.settings import DEFAULT_ADAPTER

parser = argparse.ArgumentParser()
parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
parser.add_argument("--output", type=Path, default=Path(".export-source"))
args = parser.parse_args()
if args.output.exists() and any(args.output.iterdir()):
    parser.error("Choose an empty output directory")
model, tokenizer = load_base()
model = PeftModel.from_pretrained(model, args.adapter).merge_and_unload().eval()
args.output.mkdir(parents=True, exist_ok=True)
model.save_pretrained(args.output, safe_serialization=True)
tokenizer.save_pretrained(args.output)
print(f"Saved temporary merged model to {args.output}")
