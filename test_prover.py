import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

torch.manual_seed(30)

model_id = "./Goedel-LM/Goedel-Prover-V2-32B"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 设置 pad_token（如果不存在）
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map={"": 1},
    dtype=torch.bfloat16,
    trust_remote_code=True,
)

formal_statement = """
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem square_equation_solution {x y : ℝ} (h : x^2 + y^2 = 2*x - 4*y - 5) : x + y = -1 := by
  sorry
""".strip()

prompt = """
Complete the following Lean 4 code:

```lean4
{}```

Before producing the Lean 4 code to formally prove the given theorem, provide a detailed proof plan outlining the main proof steps and strategies.
The plan should highlight key ideas, intermediate lemmas, and proof structures that will guide the construction of the final formal proof.
""".strip()

chat = [
    {"role": "user", "content": prompt.format(formal_statement)},
]

# 1. 先用 tokenizer 得到 input_ids 和 attention_mask
encoded = tokenizer.apply_chat_template(
    chat,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt",
)


start = time.time()

# 3. 直接把 encoded 展开给 generate，用自带的 attention_mask
outputs = model.generate(
    encoded.to(model.device),
    max_new_tokens=1024,  # 建议你之后自己调小点，比如 1024/2048
    pad_token_id=tokenizer.pad_token_id,
)

print(outputs)
print("-" * 100)
print(tokenizer.batch_decode(outputs))
print("-" * 100)
print(time.time() - start)
