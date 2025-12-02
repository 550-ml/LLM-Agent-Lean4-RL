"""
PutnamBench 主入口文件
适配 PutnamBench 数据格式
"""

import argparse
import os
import sys
from typing import Dict, List, Optional

from dotenv import load_dotenv

from src.agent.coordinator import AgentCoordinator, HilbertCoordinator
from src.agent.reasoner_agent import ReasonerAgent
from src.agent.retriever_agent import RetrieverAgent
from src.agent.verification_agent import VerificationAgent
from src.llm.factory import LLMFactory
from src.utils.config_manager import ConfigManager
from src.utils.prompt_loader import PromptLoader
from src.utils.putnam_loader import PutnamLoader
from src.verifier.lean4_runner import Lean4Runner

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv("config/api_key.env")


def main_workflow_putnam(
    problem_description: str,
    task_template: str,
    config_manager: Optional[ConfigManager] = None,
    config: Optional[Dict] = None,
) -> Dict[str, str]:
    """
    主工作流程（Putnam 格式）

    Args:
        problem_description: 问题描述
        task_template: 任务模板
        config_manager: ConfigManager 实例（如果为 None，会使用默认配置）
        config: 可选的配置字典，用于覆盖配置

    Returns:
        Dict[str, str]: 包含 "code" 和 "proof" 的字典
    """
    # 创建协调器（统一使用 ConfigManager）
    coordinator = AgentCoordinator.from_config(config_manager=config_manager, config=config)

    result = coordinator.solve(problem_description, task_template)

    return result


def process_single_file(
    filename: str,
    loader: PutnamLoader,
    config_manager: ConfigManager,
):
    """处理单个文件

    Args:
        filename (str): 文件名
        loader (PutnamLoader): PutnamLoader 实例
        config_manager (ConfigManager): ConfigManager 实例
    """
    # 1. 题目加载
    problem = loader.load_file(filename)
    problem_description, task_template = loader.convert_to_task_format(problem)
    logger.info(f"Problem Description: {problem_description}")
    logger.info(f"Task Template: {task_template}")
    # 2. Agent流程, 这里可以自定义
    try:
        result = main_workflow_putnam(problem_description, task_template, config_manager=config_manager)
    except Exception as e:
        logger.error(f"处理失败: {e}")
        return None
    return result


def get_files_from_dir(
    dir_path: str,
) -> List[str]:
    """从指定目录递归获取所有 .lean 文件

    Args:
        dir_path: 目录路径（绝对路径或相对路径，直接使用用户提供的路径）

    Returns:
        List[str]: 文件的绝对路径列表
    """
    # 如果是相对路径，转换为绝对路径（相对于当前工作目录）
    if os.path.isabs(dir_path):
        target_dir = dir_path
    else:
        target_dir = os.path.abspath(dir_path)

    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"目录不存在: {target_dir}")

    if not os.path.isdir(target_dir):
        raise ValueError(f"路径不是目录: {target_dir}")

    # 递归查找所有 .lean 文件，返回绝对路径
    files_to_process = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".lean"):
                # 使用绝对路径
                abs_path = os.path.abspath(os.path.join(root, file))
                files_to_process.append(abs_path)

    return sorted(files_to_process)


def main():
    # 1. 数据加载
    data_path = config_manager.get_data_dir()
    loader = PutnamLoader(data_path)
    lean_files = loader.load_lean_files()  # [Path("data/benchmarks/lean4/test/putnam_1962_a1.lean"), Path("data/benchmarks/lean4/test/putnam_1962_a2.lean"), ...]

    # 2.相关模型加载
    prompt_loader = PromptLoader(**config_manager.get_prompt_loader_config())
    reasoner_llm = LLMFactory.create_from_dict(config_manager.get_llm_config("reasoner"))
    retriever = RetrieverAgent(**config_manager.get_retriever_config())
    reansoner = ReasonerAgent(reasoner_llm, prompt_loader=prompt_loader)
    lean_runner = Lean4Runner(project_path=config_manager.get_data_dir())
    verification = VerificationAgent(lean_runner)

    coordinator = HilbertCoordinator(reasoner=reansoner, retriever=retriever, verification=verification)

    # 3. 处理每个文件
    for filename in lean_files:
        problem = loader.load_file(filename)

    # for filename in :
    #     result = process_single_file(filename, loader, config_manager)
    #     break


if __name__ == "__main__":
    # 1. 参数解析
    parser = argparse.ArgumentParser(
        description="LLM-Agent-Lean4-RL: 自动生成和验证 Lean4 形式化证明（PutnamBench 格式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dir", type=str, default="./data/benchmarks/lean4/test", help="要处理的文件夹路径")
    parser.add_argument(
        "--config", type=str, default="config/default.yaml", help="配置文件路径（默认: config/default.yaml）"
    )
    args = parser.parse_args()
    config_manager = ConfigManager(args.config)
    logger = config_manager.init_logger()
    logger.info(f"✅ 加载配置文件: {args.config}")

    # 2. 主流程
    main()
