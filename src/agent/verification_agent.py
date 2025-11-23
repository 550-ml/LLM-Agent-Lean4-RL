"""
验证智能体：验证 Lean4 代码的正确性
参考 Lean4-LLM-Ai-Agent-Mooc 的 main.py 中的验证部分
"""

from typing import Dict, Any
from .base import BaseAgent, AgentState
from ..verifier.lean4_runner import Lean4Runner


class VerificationAgent(BaseAgent):
    """
    验证智能体
    
    负责：
    1. 执行 Lean4 代码验证
    2. 分析错误信息
    3. 提供修复建议
    """
    
    def __init__(self, lean_runner: Lean4Runner, llm=None):
        """
        初始化验证智能体
        
        Args:
            lean_runner: Lean4 执行器
            llm: LLM 实例（可选，验证智能体主要使用 lean_runner）
        """
        # 验证智能体主要使用 lean_runner，但为了保持接口一致性，需要一个 LLM
        # 如果未提供，创建一个虚拟的
        if llm is None:
            from ..llm.base import BaseLLM, LLMConfig
            # 创建一个简单的虚拟 LLM
            class DummyLLM(BaseLLM):
                def generate(self, messages, **kwargs):
                    return None
                def stream_generate(self, messages, **kwargs):
                    yield ""
            llm = DummyLLM(LLMConfig(model_name="dummy"))
        
        super().__init__(llm, "VerificationAgent")
        self.lean_runner = lean_runner
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        执行验证任务
        
        Args:
            state: 当前状态
        
        Returns:
            Dict[str, Any]: 包含 "success" 和 "error" 键的字典
        """
        # 将代码和证明插入模板
        full_code = state.task_template.replace("{{code}}", state.current_code).replace("{{proof}}", state.current_proof)
        
        # 执行验证
        result = self.lean_runner.execute(full_code)
        
        if result.success:
            return {
                "success": True,
                "output": result.output,
                "error": None
            }
        else:
            # 提取错误信息
            error_msg = result.error_message or result.output
            return {
                "success": False,
                "output": result.output,
                "error": error_msg
            }

