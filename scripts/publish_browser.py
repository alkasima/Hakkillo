"""Publish merged ONNX weights and a free static Hugging Face Space."""
import argparse
import json
import math
import shutil
from pathlib import Path

from huggingface_hub import HfApi

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--owner', default='alkasima')
parser.add_argument('--model-name', default='Hakkillo-135M-v0.1-ONNX')
parser.add_argument('--space-name', default='Hakkillo')
parser.add_argument('--folder', type=Path, default=root/'artifacts/hakkillo-browser')
args=parser.parse_args()
api=HfApi()
account=api.whoami()
if args.owner not in {account['name']} | {org['name'] for org in account.get('orgs',[])}:
    parser.error('Sign in as the requested owner first')
folder=args.folder
if not (folder/'onnx/model_quantized.onnx').is_file():
    parser.error('Export and quantize the model first')
# Transformers.js 3 expects the chat template in tokenizer_config.json.
tokenizer_path = folder/'tokenizer_config.json'
tokenizer_config = json.loads(tokenizer_path.read_text(encoding='utf-8'))
tokenizer_config['chat_template'] = (folder/'chat_template.jinja').read_text(encoding='utf-8')
tokenizer_path.write_text(json.dumps(tokenizer_config,indent=2)+'\n',encoding='utf-8')
model_id=f'{args.owner}/{args.model_name}'
space_id=f'{args.owner}/{args.space_name}'
size_mb=math.ceil((folder/'onnx/model_quantized.onnx').stat().st_size/1e6)
for name in ('LICENSE','NOTICE'):
    shutil.copy2(root/name,folder/name)
(folder/'README.md').write_text(f'''---
language:
- en
license: apache-2.0
library_name: transformers.js
pipeline_tag: text-generation
base_model: {args.owner}/Hakkillo-135M-v0.1
base_model_relation: quantized
tags:
- onnx
- cpu
- experimental
---

# Hakkillo v0.1 — browser edition

Merged and dynamically int8-quantized ONNX weights for the experimental [Hakkillo adapter](https://huggingface.co/{args.owner}/Hakkillo-135M-v0.1), based on HuggingFaceTB/SmolLM2-135M-Instruct.

The model file is about {size_mb} MB. The [demo](https://huggingface.co/spaces/{space_id}) runs on the visitor's CPU using Transformers.js 3.8.1 and WebAssembly. No hosted inference API is used.

Code, training data, export commands, and reports: https://github.com/alkasima/Hakkillo

The adapter was trained for 48 CPU steps on 32 synthetic examples. This is an early prototype. It can invent facts, misunderstand instructions, and produce wrong explanations. See the adapter card and release report for observed failures. Quantization can change outputs; the adapter's development loss is not a measured score for this ONNX version.
In the three-prompt CPU check, it explained a CPU and identified Abuja, but failed to complete the answer to 7 + 5. This is an observed regression from the float32 adapter on that prompt.

Export: Optimum ONNX 0.1.0, Transformers 4.57.6, opset 17; dynamic int8 MatMul/Gather quantization in ONNX Runtime 1.23.2. The float export reported a maximum logit difference of 0.00193 against its PyTorch reference (above the default 1e-5 comparison tolerance). Structural checking and CPU generation tests are recorded in the source repository; no broad quantized quality claim is made.

```javascript
import {{ pipeline }} from '@huggingface/transformers';
const generator = await pipeline('text-generation', '{model_id}', {{ dtype: 'q8', device: 'wasm' }});
const result = await generator([
  {{ role: 'system', content: 'You are Hakkillo, a small English AI assistant.' }},
  {{ role: 'user', content: 'What is a CPU?' }}
], {{ max_new_tokens: 64, do_sample: false }});
console.log(result[0].generated_text.at(-1).content);
```

Apache-2.0. Hugging Face's SmolLM team created the base model. Hakkillo adds a small LoRA adaptation and this merged/quantized export. See LICENSE and NOTICE.
''',encoding='utf-8')
api.create_repo(model_id,repo_type='model',private=False,exist_ok=True)
commit=api.upload_folder(repo_id=model_id,folder_path=folder,allow_patterns=['*.json','*.txt','*.jinja','README.md','LICENSE','NOTICE','onnx/model_quantized.onnx'],commit_message='Publish quantized Hakkillo weights for browser CPU inference')
config={'model_id':model_id,'revision':commit.oid,'download_mb':size_mb+4}
(root/'web/model.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
stage=root/'.publish/static-space'
stage.mkdir(parents=True,exist_ok=True)
for source in (root/'web').iterdir():
    if source.is_file(): shutil.copy2(source,stage/source.name)
for name in ('LICENSE','NOTICE'): shutil.copy2(root/name,stage/name)
(stage/'README.md').write_text(f'''---
title: Hakkillo
emoji: 🌱
colorFrom: green
colorTo: gray
sdk: static
app_file: index.html
pinned: false
license: apache-2.0
models:
- {model_id}
short_description: A tiny English assistant running in your browser
---

# Hakkillo

An experimental 135M English assistant. Click Load Hakkillo to download the quantized model, then chat locally in your browser. Messages are not sent to an inference server. Model files are served by Hugging Face and runtime libraries by jsDelivr.

[Code and roadmap](https://github.com/alkasima/Hakkillo) · [Model card](https://huggingface.co/{args.owner}/Hakkillo-135M-v0.1)
''',encoding='utf-8')
api.create_repo(space_id,repo_type='space',space_sdk='static',private=False,exist_ok=True)
space_commit=api.upload_folder(repo_id=space_id,repo_type='space',folder_path=stage,allow_patterns=['*.html','*.css','*.js','*.json','*.md','LICENSE','NOTICE'],commit_message='Launch free Hakkillo browser CPU demo')
report_path=root/'reports/publishing.json'
result=json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
adapter=api.model_info(f'{args.owner}/Hakkillo-135M-v0.1')
result.update({'model_url':f'https://huggingface.co/{adapter.id}','model_commit':adapter.sha,'browser_model_url':f'https://huggingface.co/{model_id}','browser_model_commit':commit.oid,'space_url':f'https://huggingface.co/spaces/{space_id}','space_commit':space_commit.oid,'space_sdk':'static','download_mb':config['download_mb']})
report_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
