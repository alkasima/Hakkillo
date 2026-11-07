"""Check the quantized graph on CPU, including empty and growing KV caches."""
import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

folder = Path("artifacts/hakkillo-browser")
options = ort.SessionOptions()
options.intra_op_num_threads = 4
session = ort.InferenceSession(str(folder / "onnx/model_quantized.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
tokenizer = AutoTokenizer.from_pretrained(folder)
records = []
system = "You are Hakkillo, a small English AI assistant. Give clear, brief and helpful answers. If you do not know, say so. You cannot browse the web or take actions."
for prompt in ["What is a CPU?", "What is the capital city of Nigeria?", "What is 7 plus 5? Reply with just the number."]:
    ids = tokenizer.apply_chat_template([{"role":"system","content":system},{"role":"user","content":prompt}], add_generation_prompt=True, return_tensors="np")
    inputs = {"input_ids": ids, "attention_mask": np.ones_like(ids), "position_ids": np.arange(ids.shape[1],dtype=np.int64)[None,:]}
    for entry in session.get_inputs():
        if entry.name.startswith("past_key_values"):
            inputs[entry.name] = np.zeros((1,3,0,64),dtype=np.float32)
    generated=[]
    started=time.perf_counter()
    length=ids.shape[1]
    for _ in range(64):
        result=dict(zip([o.name for o in session.get_outputs()],session.run(None,inputs)))
        logits=result['logits'][0,-1,:].copy()
        if not np.isfinite(logits).all():
            raise RuntimeError('Non-finite logits')
        # Same repetition penalty as the interactive demos, applied to prompt + generated tokens.
        for token in set(ids[0].tolist()+generated):
            logits[token] = logits[token] * 1.08 if logits[token] < 0 else logits[token] / 1.08
        token=int(logits.argmax())
        if token==tokenizer.eos_token_id: break
        generated.append(token)
        inputs={"input_ids":np.array([[token]],dtype=np.int64),"attention_mask":np.ones((1,length+1),dtype=np.int64),"position_ids":np.array([[length]],dtype=np.int64)}
        for key,value in result.items():
            if key.startswith('present.'):
                inputs[key.replace('present.','past_key_values.',1)]=value
        length+=1
    text=tokenizer.decode(generated,skip_special_tokens=True).strip()
    if not text: raise RuntimeError('Empty generated reply')
    record={"prompt":prompt,"response":text,"seconds":round(time.perf_counter()-started,3),"generated_tokens":len(generated)}
    records.append(record)
    print(json.dumps(record),flush=True)
Path('reports/browser_runtime_check.json').write_text(json.dumps({"runtime":"ONNX Runtime CPU; browser checked separately","quantization":"dynamic int8 MatMul and Gather","results":records},indent=2)+'\n',encoding='utf-8')
