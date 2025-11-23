"""
Agent 基类定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass, field

from ..llm.base import BaseLLM


@dataclass
class AgentState:
    """智能体状态"""
    problem_description: str
    task_template: str
    current_code: str = ""
    current_proof: str = ""
    error_history: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 5
    planning_result: str = ""  # 规划智能体的分析结果


class BaseAgent(ABC):
    """
    智能体基类
    
    所有智能体都应该继承这个类
    """
    
    def __init__(self, llm: BaseLLM, name: str):
        """
        初始化智能体
        
        Args:
            llm: LLM 实例
            name: 智能体名称
        """
        self.llm = llm
        self.name = name
    
    @abstractmethod
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        执行智能体任务
        
        Args:
            state: 当前状态
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.name}(model={self.llm.config.model_name})"

