"""Run in the optional export environment after optimum-cli export onnx."""
import argparse
import json
from pathlib import Path

import onnx
from onnxruntime.quantization import QuantType, quantize_dynamic

parser = argparse.ArgumentParser()
parser.add_argument("--folder", type=Path, default=Path("artifacts/hakkillo-browser"))
args = parser.parse_args()
folder = args.folder
destination = folder / "onnx"
destination.mkdir(exist_ok=True)
output = destination / "model_quantized.onnx"
quantize_dynamic(
    str(folder / "model.onnx"), str(output), weight_type=QuantType.QInt8,
    per_channel=False, reduce_range=False, op_types_to_quantize=["MatMul", "Gather"],
)
onnx.checker.check_model(str(output))
config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
config["transformers.js_config"] = {"kv_cache_dtype": {"q8": "float32"}}
(folder / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print(f"Validated quantized model: {output.stat().st_size / 1e6:.1f} MB")
