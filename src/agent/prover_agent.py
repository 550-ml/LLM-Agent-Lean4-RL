import logging
import re
import time
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


class ProverAgent:
    """使用本地 Goedel-LM 模型进行证明的智能体"""

    def __init__(
        self,
        model_path: str = "./Goedel-LM/Goedel-Prover-V2-32B",
        device_map: Optional[dict] = None,
        max_new_tokens: int = 1024,
    ):
        self.model_path = model_path
        self.device_map = device_map or {"": 0}
        self.max_new_tokens = max_new_tokens

        # 初始化时直接加载模型
        self._model = None
        self._tokenizer = None
        self._load_model()

    def _load_model(self):
        """加载模型"""
        if self._model is not None:
            return

        logger.info(f"Loading Goedel-LM model from {self.model_path}")
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)

            # 设置 pad_token（如果不存在）
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=self.device_map,
                dtype=torch.bfloat16,
                trust_remote_code=True,
            )
            logger.info("Goedel-LM model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Goedel-LM model: {e}")
            raise

    def prove_subgoal(self, subgoal: str, header: str = "") -> str:
        """
        使用 Goedel-LM 证明子目标

        Args:
            subgoal: 需要证明的子目标（Lean 4 代码）
            header: 可选的头部代码（imports 等）

        Returns:
            生成的证明代码
        """
        # 构建完整的代码
        full_code = header + "\n" + subgoal if header else subgoal

        # 构建 prompt
        prompt = f"""Complete the following Lean 4 code:

```lean4
{full_code}```

Before producing the Lean 4 code to formally prove the given theorem, provide a detailed proof plan outlining the main proof steps and strategies.
The plan should highlight key ideas, intermediate lemmas, and proof structures that will guide the construction of the final formal proof.
""".strip()

        chat = [{"role": "user", "content": prompt}]

        try:
            # 编码输入
            encoded = self._tokenizer.apply_chat_template(
                chat,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
            )

            # 生成证明
            start_time = time.time()
            outputs = self._model.generate(
                encoded.to(self._model.device),
                max_new_tokens=self.max_new_tokens,
                pad_token_id=self._tokenizer.pad_token_id,
            )

            # 解码输出
            generated_text = self._tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

            logger.debug(f"Prover generation time: {time.time() - start_time:.2f}s")

            # 提取 Lean 代码块（如果有）
            pattern = re.compile(r"```(?:lean4?)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
            matches = pattern.findall(generated_text)
            if matches:
                return matches[0]

            # 如果没有代码块，返回整个响应（可能需要进一步处理）
            return generated_text

        except Exception as e:
            logger.error(f"Error in prove_subgoal: {e}")
            return ""
