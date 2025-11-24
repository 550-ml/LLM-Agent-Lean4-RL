"""
生成智能体：生成 Lean4 代码和证明
参考 Lean4-LLM-Ai-Agent-Mooc 的 main.py 中的 llm_agent 部分
"""

from typing import Dict, Any
from .base import BaseAgent, AgentState
from ..llm.base import BaseLLM


class GenerationAgent(BaseAgent):
    """
    生成智能体

    负责：
    1. 根据规划生成函数实现代码
    2. 生成对应的形式化证明
    3. 输出格式化的代码和证明
    """

    def __init__(self, llm: BaseLLM):
        """
        初始化生成智能体

        Args:
            llm: LLM 实例（通常使用代码生成能力强的模型，如 gpt-4o）
        """
        super().__init__(llm, "GenerationAgent")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        执行生成任务

        Args:
            state: 当前状态

        Returns:
            Dict[str, Any]: 包含 "code" 和 "proof" 键的字典
        """
        # 构建生成提示词
        generation_prompt = f"""你是一个 Lean4 代码生成专家。根据以下问题、规划和模板，生成代码和证明。

问题描述：
{state.problem_description}

规划分析：
{state.planning_result if state.planning_result else "无"}

Lean4 代码模板：
{state.task_template}

模板中有两个占位符需要填充：
1. {{code}} - 需要实现函数体
2. {{proof}} - 需要实现证明步骤

请严格按照以下格式输出，不要添加任何额外文本：

CODEPART:
[这里放函数实现代码]

PROOFPART:
[这里放证明步骤]

注意：
- 只输出代码和证明，不要包含 markdown 代码块标记
- 代码应该是可以直接替换 {{code}} 的完整实现
- 证明应该是可以直接替换 {{proof}} 的完整证明步骤"""

        # 如果有错误历史，添加错误信息
        if state.error_history:
            error_info = "\n".join(
                [f"- {err}" for err in state.error_history[-3:]])  # 只显示最近3个错误
            generation_prompt += f"""

之前的错误信息：
{error_info}

请根据这些错误修正你的实现。"""

        # 调用 LLM
        messages = [
            {"role": "system", "content": "你是一个专业的 Lean4 代码生成专家。严格按照要求的格式输出代码和证明。"},
            {"role": "user", "content": generation_prompt}
        ]

        response = self.llm.get_response(messages)

        # 解析响应，提取代码和证明
        code, proof = self._extract_code_and_proof(response)

        return {
            "code": code,
            "proof": proof,
            "raw_response": response,
            "success": True
        }

    def _extract_code_and_proof(self, response: str) -> tuple[str, str]:
        """
        从 LLM 响应中提取代码和证明

        Args:
            response: LLM 响应文本

        Returns:
            tuple: (code, proof)
        """
        code = ""
        proof = ""

        # 查找 CODEPART 和 PROOFPART
        if "CODEPART:" in response and "PROOFPART:" in response:
            parts = response.split("CODEPART:")
            if len(parts) > 1:
                code_proof_parts = parts[1].split("PROOFPART:")
                if len(code_proof_parts) >= 2:
                    code = self._clean_code_block(code_proof_parts[0].strip())
                    proof = self._clean_code_block(code_proof_parts[1].strip())

        return code, proof

    def _clean_code_block(self, text: str) -> str:
        """
        清理代码块（移除 markdown 标记等）
        参考 Lean4-LLM-Ai-Agent-Mooc 的 clean_code_block 函数
        """
        # 移除开头的代码块标记
        if text.startswith("```lean"):
            text = text[len("```lean"):].strip()
        elif text.startswith("```"):
            text = text[len("```"):].strip()

        # 移除结尾的代码块标记
        if text.endswith("```"):
            text = text[:-3].strip()

        # 移除一些特殊字符
        text = text.replace("`", "")
        text = text.replace("·", "")
        text = text.replace("#", "")

        return text.strip()
