"""
规划智能体：分析问题，制定证明策略
参考 Lean4-LLM-Ai-Agent-Mooc 的 main.py 中的 reasoning_agent 部分
"""

from typing import Dict, Any
from .base import BaseAgent, AgentState


class PlanningAgent(BaseAgent):
    """
    规划智能体
    
    负责：
    1. 分析问题描述
    2. 理解任务模板
    3. 制定证明策略和步骤
    """
    
    def __init__(self, llm: BaseLLM):
        """
        初始化规划智能体
        
        Args:
            llm: LLM 实例（通常使用推理能力强的模型，如 o3-mini）
        """
        super().__init__(llm, "PlanningAgent")
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        执行规划任务
        
        Args:
            state: 当前状态
        
        Returns:
            Dict[str, Any]: 包含 "plan" 键的字典
        """
        # 构建规划提示词
        planning_prompt = f"""你是一个专业的 Lean4 形式化证明规划专家。请分析以下问题并制定证明策略。

问题描述：
{state.problem_description}

Lean4 代码模板：
{state.task_template}

你的任务是：
1. 分析问题，理解需要实现的功能和需要证明的性质
2. 识别关键概念和可能需要的定理
3. 制定证明策略和步骤
4. 指出可能遇到的难点

请提供详细的分析和规划，帮助后续的代码生成和证明。"""
        
        # 调用 LLM
        messages = [
            {"role": "system", "content": "你是一个专业的 Lean4 形式化证明规划专家。"},
            {"role": "user", "content": planning_prompt}
        ]
        
        plan = self.llm.get_response(messages)
        
        # 更新状态
        state.planning_result = plan
        
        return {
            "plan": plan,
            "success": True
        }

