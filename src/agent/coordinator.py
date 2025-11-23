"""
多智能体协调器：管理多智能体协作
参考 Lean4-LLM-Ai-Agent-Mooc 的 main.py 中的 main_workflow 函数
"""

import os
import yaml
from typing import Dict, Optional
from .base import AgentState
from .planning_agent import PlanningAgent
from .generation_agent import GenerationAgent
from .verification_agent import VerificationAgent
from ..llm.base import BaseLLM, LLMConfig
from ..llm.factory import LLMFactory
from ..llm.config_loader import ConfigLoader
from ..verifier.lean4_runner import Lean4Runner


class AgentCoordinator:
    """
    多智能体协调器

    负责协调规划、生成、验证三个智能体的工作流程
    """

    def __init__(
        self,
        planning_agent: Optional[PlanningAgent] = None,
        generation_agent: Optional[GenerationAgent] = None,
        verification_agent: Optional[VerificationAgent] = None,
        planning_llm: Optional[BaseLLM] = None,
        generation_llm: Optional[BaseLLM] = None,
        lean_runner: Optional[Lean4Runner] = None,
        max_retries: int = 5
    ):
        """
        初始化协调器

        Args:
            planning_agent: 规划智能体（如果为 None，会自动创建）
            generation_agent: 生成智能体（如果为 None，会自动创建）
            verification_agent: 验证智能体（如果为 None，会自动创建）
            planning_llm: 规划智能体使用的 LLM（默认使用 o3-mini）
            generation_llm: 生成智能体使用的 LLM（默认使用 gpt-4o）
            lean_runner: Lean4 执行器（如果为 None，会自动创建）
            max_retries: 最大重试次数（默认 5）
        """
        # 创建默认 LLM（如果未提供）
        if planning_llm is None:
            planning_config = LLMConfig(model_name="o3-mini", temperature=0.7)
            planning_llm = LLMFactory.create_llm(planning_config)

        if generation_llm is None:
            generation_config = LLMConfig(model_name="gpt-4o", temperature=0.7)
            generation_llm = LLMFactory.create_llm(generation_config)

        # 创建智能体（如果未提供）
        if planning_agent is None:
            self.planning_agent = PlanningAgent(planning_llm)
        else:
            self.planning_agent = planning_agent

        if generation_agent is None:
            self.generation_agent = GenerationAgent(generation_llm)
        else:
            self.generation_agent = generation_agent

        if lean_runner is None:
            lean_runner = Lean4Runner()

        if verification_agent is None:
            self.verification_agent = VerificationAgent(lean_runner)
        else:
            self.verification_agent = verification_agent

        # 保存 max_retries 供 solve() 使用
        self.default_max_retries = max_retries

    @classmethod
    def from_config(cls, config: Optional[Dict] = None, config_file: Optional[str] = None) -> 'AgentCoordinator':
        """
        从配置创建协调器（便于从配置文件加载）

        Args:
            config: 配置字典（如果提供，会覆盖配置文件）
            config_file: 配置文件路径（默认: "config/default.yaml"）

        Returns:
            AgentCoordinator: 协调器实例

        Example:
            # 从默认配置文件加载
            coordinator = AgentCoordinator.from_config()

            # 从指定配置文件加载
            coordinator = AgentCoordinator.from_config(config_file="config/custom.yaml")

            # 使用字典配置（覆盖文件配置）
            coordinator = AgentCoordinator.from_config({
                "planning_model": "o3-mini",
                "generation_model": "gpt-4o"
            })
        """
        if config_file is None:
            config_file = "config/default.yaml"

        # 从配置文件加载（如果文件存在）
        if os.path.exists(config_file):
            try:
                planning_config = ConfigLoader.load_planning_config(
                    config_file)
                generation_config = ConfigLoader.load_generation_config(
                    config_file)
            except Exception as e:
                # 如果加载失败，使用默认配置
                import logging
                logging.warning(f"无法从配置文件加载，使用默认配置: {e}")
                planning_config = LLMConfig(
                    model_name="o3-mini", temperature=0.7)
                generation_config = LLMConfig(
                    model_name="gpt-4o", temperature=0.7)
        else:
            # 如果文件不存在，使用默认配置
            planning_config = LLMConfig(model_name="o3-mini", temperature=0.7)
            generation_config = LLMConfig(model_name="gpt-4o", temperature=0.7)

        # 如果提供了 config 字典，覆盖配置
        if config:
            if "planning_model" in config:
                planning_config.model_name = config["planning_model"]
            if "planning_temperature" in config:
                planning_config.temperature = config["planning_temperature"]
            if "generation_model" in config:
                generation_config.model_name = config["generation_model"]
            if "generation_temperature" in config:
                generation_config.temperature = config["generation_temperature"]

        planning_llm = LLMFactory.create_llm(planning_config)
        generation_llm = LLMFactory.create_llm(generation_config)

        # 从配置文件读取 max_retries（如果文件存在）
        max_retries = 5  # 默认值
        if config_file and os.path.exists(config_file):
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    full_config = yaml.safe_load(f)
                max_retries = full_config.get(
                    "agent", {}).get("max_retries", 5)
            except Exception:
                pass  # 如果读取失败，使用默认值

        return cls(
            planning_llm=planning_llm,
            generation_llm=generation_llm,
            max_retries=max_retries
        )

    def solve(self, problem_description: str, task_template: str, max_retries: Optional[int] = None) -> Dict[str, str]:
        """
        解决问题的主流程

        参考 Lean4-LLM-Ai-Agent-Mooc 的 main_workflow 函数

        Args:
            problem_description: 问题描述（从 description.txt 读取）
            task_template: 任务模板（从 task.lean 读取）
            max_retries: 最大重试次数（如果为 None，使用默认值 5）

        Returns:
            Dict[str, str]: 包含 "code" 和 "proof" 的字典

        Raises:
            Exception: 如果超过最大重试次数仍未成功
        """
        # 使用默认值或传入的值
        if max_retries is None:
            max_retries = getattr(self, 'default_max_retries', 5)

        # 初始化状态
        # 如果 max_retries 为 None，尝试从配置文件读取
        if max_retries is None and hasattr(self, '_config_manager'):
            max_retries = self._config_manager.get_max_retries()
        elif max_retries is None:
            max_retries = 5  # 默认值

        state = AgentState(
            problem_description=problem_description,
            task_template=task_template,
            max_retries=max_retries
        )

        # 步骤 1: 规划阶段
        print("🔍 [规划阶段] 分析问题并制定策略...")
        planning_result = self.planning_agent.execute(state)
        if not planning_result.get("success"):
            raise Exception("规划阶段失败")
        print("✅ 规划完成")

        # 步骤 2: 生成阶段
        print("\n💻 [生成阶段] 生成代码和证明...")
        generation_result = self.generation_agent.execute(state)
        if not generation_result.get("success"):
            raise Exception("生成阶段失败")

        state.current_code = generation_result["code"]
        state.current_proof = generation_result["proof"]
        print(
            f"✅ 代码生成完成 (代码长度: {len(state.current_code)}, 证明长度: {len(state.current_proof)})")

        # 步骤 3: 验证阶段（迭代）
        print("\n🔬 [验证阶段] 验证代码正确性...")
        while state.retry_count < state.max_retries:
            verification_result = self.verification_agent.execute(state)

            if verification_result["success"]:
                print("✅ 验证成功！")
                return {
                    "code": state.current_code,
                    "proof": state.current_proof
                }
            else:
                # 验证失败，记录错误并重试
                error = verification_result["error"]
                state.error_history.append(error)
                state.retry_count += 1

                print(f"❌ 验证失败 (尝试 {state.retry_count}/{state.max_retries})")
                print(f"   错误: {error[:200]}...")  # 只显示前200个字符

                if state.retry_count < state.max_retries:
                    print("🔄 重新生成...")
                    # 重新生成
                    generation_result = self.generation_agent.execute(state)
                    if generation_result.get("success"):
                        state.current_code = generation_result["code"]
                        state.current_proof = generation_result["proof"]
                    else:
                        print("❌ 重新生成失败")

        # 超过最大重试次数
        raise Exception(
            f"超过最大重试次数 ({state.max_retries})。"
            f"最后生成的代码和证明已返回，但验证未通过。"
            f"错误历史: {state.error_history[-1] if state.error_history else '无'}"
        )
