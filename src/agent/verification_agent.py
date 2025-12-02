from .base import BaseAgent, AgentState
from ..verifier import lean4_runner
from ..llm import BaseLLM
import logging

logger = logging.getLogger(__name__)


class VerificationAgent:
    """
    验证智能体
    """

    def __init__(self, lean_runner: lean4_runner):
        super.__init__()
        self.lean_runner = lean_runner

    def execute(
        self,
        full_proof: str,
    ):
        """执行 Lean4 验证"""
        result = self.lean_runner.execute(full_proof)
        success = getattr(result, "success", False)
        output = getattr(result, "output", "")
        error = getattr(result, "error", "")
        if success:
            return {
                "success": True,
                "output": output,
            }
        return result

    def execute2(self, state: AgentState) -> dict:
        """执行 Lean4 验证"""

        # === 1. 将 proof 替换进去 ===
        if "{proof}" not in state.task_template:
            logger.error("❌ 模板中缺少 {proof} 占位符！")
            error_msg = "Template missing {{proof}} placeholder"
            if hasattr(state, "error_history"):
                state.error_history.append(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "output": None,
            }

        full_code = state.task_template.replace("{proof}", state.current_proof)
        logger.info(f"最后验证完整代码: {full_code}")
        # === 2. 运行 Lean ===
        result = self.lean_runner.execute(full_code)

        # === 3. 格式化输出 ===
        success = getattr(result, "success", False)
        output = getattr(result, "output", "")
        error = getattr(result, "error", "")

        if success:
            return {
                "success": True,
                "output": output,
            }

        normalized_error = error or "Unknown Lean4 error"

        # 将 Lean 错误信息和本次尝试的 proof 一并记录，便于生成阶段诊断
        if hasattr(state, "error_history"):
            state.error_history.append(f"Lean error: {normalized_error}\nProof attempt:\n{state.current_proof}")

        return {
            "success": False,
            "error": normalized_error,
            "output": output,
        }
