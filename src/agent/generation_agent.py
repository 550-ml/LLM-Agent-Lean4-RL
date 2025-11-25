from .base import BaseAgent, AgentState
from typing import Dict, Any
from ..llm.base import BaseLLM
import logging

logger = logging.getLogger(__name__)


class GenerationAgent(BaseAgent):
    """答案生成智能体
    负责：
    1. 生成答案
    2. 输出格式化代码和证明
    """

    def __init__(self, llm: BaseLLM):
        super().__init__(llm, "GenerationAgent")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        generation_prompt = f"""
        You are an expert Lean4 theorem-proving agent working on the PutnamBench Lean4 dataset.
Your ONLY task is to fill the placeholder {{proof}} in the Lean theorem template with a valid Lean4 proof script.
The problem already provides:
- all necessary imports
- the theorem name and statement
- the exact location of {{proof}}

==================== Problem ====================
{state.problem_description}

==================== High-Level Plan ====================
The following is the high-level proof plan produced in the earlier planning phase:
{state.planning_result}

==================== Lean4 Theorem Template ====================
The template below shows the theorem EXACTLY as it should appear, with a single placeholder {{proof}}.
DO NOT modify anything outside {{proof}}.
DO NOT repeat the theorem header, imports, or structure.

```lean
{state.task_template}
==================== Your Task ====================
	•	Generate ONLY the Lean4 proof code that replaces {{proof}}.
	•	The output must be ONLY the proof (a valid Lean4 proof script).
	•	NO import, NO theorem, NO headers, NO comments, NO extra explanations.
	•	DO NOT wrap your output in markdown or code fences.
	•	DO NOT output CODEPART or PROOFPART markers.
	•	DO NOT output natural-language text.
	•	DO NOT output sorry or admit.
	•	You may begin the proof using:
	•	by followed by tactic lines, OR
	•	directly the tactics if the template already contains := by.

=========== OUTPUT FORMAT ===========
OUTPUT ONLY this:

[Lean4 proof script that replaces {{proof}}]

(There must be no other text.)

Begin your answer with the first Lean tactic or by.
“””
        """
        if state.error_history:
            error_info = "\n".join(
                [f"- {err}" for err in state.error_history[-3:]])  # 只显示最近3个错误
            generation_prompt += f"""
            Previous error information:
    {error_info}
Please correct your implementation based on these errors."""

        # * 2. call llm
        messages = [
            {"role": "system", "content": "You are a Lean4 code generation expert."},
            {"role": "user", "content": generation_prompt}
        ]
        response = self.llm.get_response(messages)
        logger.debug(f"GenerationAgent response: {response}")
        # * 3. update state
        proof = self._clean_proof(response)
        state.current_proof = proof
        return {
            "proof": proof,
            "raw_response": response,
            "success": True
        }

    def _clean_proof(self, response: str) -> str:
        """
        清理 LLM 输出，拿到纯 Lean 证明代码：
        - 去掉 ``` / ```lean 代码块包裹
        - 去掉首尾空白
        """
        text = response.strip()

        # 去掉可能的代码块围栏
        if "```" in text:
            text = text.replace("```lean", "")
            text = text.replace("```", "")

        return text.strip()
