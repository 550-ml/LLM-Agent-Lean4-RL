import logging

from ..verifier import lean4_runner
from .base import AgentState

logger = logging.getLogger(__name__)


class VerificationAgent:
    """
    验证智能体
    """

    def __init__(self, lean_runner: lean4_runner):
        self.lean_runner = lean_runner

    def execute(
        self,
        full_proof: str,
    ):
        """执行 Lean4 验证"""
        result = self.lean_runner.execute(full_proof)
        success = getattr(result, "success", False)
        output = getattr(result, "output", "")
        return success, output
