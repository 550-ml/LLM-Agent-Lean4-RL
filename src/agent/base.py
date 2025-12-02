from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..llm.base import BaseLLM


@dataclass
class AgentState:
    """Agent State"""

    problem_description: str
    task_template: str
    current_proof: str = ""
    error_history: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 5
    planning_result: str = ""  # 规划智能体的分析结果


class BaseAgent(ABC):
    def __init__(self, llm: BaseLLM, name: str):
        self.llm = llm
        self.name = name

    def execute(self, state: AgentState) -> Dict[str, Any]:
        pass

    def __str__(self) -> str:
        return f"{self.name}(model={self.llm.config.model_name})"
