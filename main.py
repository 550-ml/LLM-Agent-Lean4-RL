"""
PutnamBench 主入口文件
适配 PutnamBench 数据格式
"""

from src.utils.putnam_loader import PutnamLoader
from src.agent.coordinator import AgentCoordinator
from src.utils.config_manager import ConfigManager
from typing import Dict, Optional, List
import argparse

import os
import sys
# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main_workflow_putnam(
    problem_description: str,
    task_template: str,
    config: Optional[Dict] = None,
    config_file: Optional[str] = None
) -> Dict[str, str]:
    """
    主工作流程（Putnam 格式）

    Args:
        problem_description: 问题描述
        task_template: 任务模板
        config: 配置字典（可选，会覆盖配置文件）
        config_file: 配置文件路径（可选，默认: "config/default.yaml"）

    Returns:
        Dict[str, str]: 包含 "code" 和 "proof" 的字典

    Example:
        # 使用默认配置
        result = main_workflow_putnam(description, template)

        # 使用自定义配置
        result = main_workflow_putnam(
            description,
            template,
            config={"planning_model": "o3-mini", "generation_model": "gpt-4o"}
        )

        # 使用指定配置文件
        result = main_workflow_putnam(
            description,
            template,
            config_file="config/custom.yaml"
        )
    """
    # 创建协调器（支持传入配置）
    coordinator = AgentCoordinator.from_config(
        config=config, config_file=config_file)

    result = coordinator.solve(problem_description, task_template)

    return result


def process_single_file(
    filename: str,
    loader: PutnamLoader,
    config_manager: ConfigManager,
    config_file: str,
    verbose: bool = True
) -> Optional[Dict[str, str]]:
    """
    处理单个文件

    Args:
        filename: 文件名
        loader: PutnamLoader 实例
        config_manager: ConfigManager 实例
        config_file: 配置文件路径
        verbose: 是否显示详细信息

    Returns:
        处理结果字典，如果失败返回 None
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"📖 处理文件: {filename}")
        print(f"{'='*60}")

    # 加载问题
    try:
        problem = loader.load_file(filename)
        if verbose:
            print(f"   定理名称: {problem.theorem_name}")
            print(f"   问题描述: {problem.docstring[:100]}..." if len(
                problem.docstring) > 100 else f"   问题描述: {problem.docstring}")
    except Exception as e:
        print(f"❌ 加载失败 [{filename}]: {e}")
        return None

    # 转换为任务格式
    if verbose:
        print("\n🔄 转换为任务格式...")
    problem_description, task_template = loader.convert_to_task_format(problem)

    # 从配置文件获取配置信息
    planning_model = config_manager.get("llm.planning.model", "o3-mini")
    generation_model = config_manager.get("llm.generation.model", "gpt-4o")
    max_retries = config_manager.get_max_retries()

    # 执行主工作流程
    if verbose:
        print("\n🚀 开始执行主工作流程...")
        print(f"   规划模型: {planning_model}")
        print(f"   生成模型: {generation_model}")
        print(f"   最大重试: {max_retries}")

    try:
        result = main_workflow_putnam(
            problem_description,
            task_template,
            config=None,
            config_file=config_file
        )

        if verbose:
            # 输出结果
            print("\n" + "="*60)
            print("✅ 完成！生成的证明：")
            print("="*60)
            print("\n[证明]")
            print(result.get("proof", result.get("code", "")))
            print("="*60)

            # 生成完整的定理（替换 sorry）
            full_theorem = problem.theorem_statement.replace(
                'sorry',
                result.get("proof", result.get("code", "sorry"))
            )
            print("\n[完整定理]")
            print(full_theorem)
            print("="*60)

        return {
            "filename": filename,
            "theorem_name": problem.theorem_name,
            "proof": result.get("proof", result.get("code", "")),
            "full_theorem": problem.theorem_statement.replace(
                'sorry',
                result.get("proof", result.get("code", "sorry"))
            ),
            "success": True
        }

    except Exception as e:
        print(f"\n❌ 处理失败 [{filename}]: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return {
            "filename": filename,
            "theorem_name": problem.theorem_name if 'problem' in locals() else "unknown",
            "success": False,
            "error": str(e)
        }


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
            if file.endswith('.lean'):
                # 使用绝对路径
                abs_path = os.path.abspath(os.path.join(root, file))
                files_to_process.append(abs_path)

    return sorted(files_to_process)


def main():
    parser = argparse.ArgumentParser(
        description="LLM-Agent-Lean4-RL: 自动生成和验证 Lean4 形式化证明（PutnamBench 格式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dir",
        type=str,
        default='./data/test/lean4/src/',
        help="要处理的文件夹路径"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/default.yaml",
        help="配置文件路径（默认: config/default.yaml）"
    )

    # 参数加载
    args = parser.parse_args()
    config_manager = ConfigManager(args.config)
    print(f"✅ 加载配置文件: {args.config}")
    benchmarks_dir = config_manager.get_benchmarks_dir()
    loader = PutnamLoader(benchmarks_dir)

    # 获取要处理的文件列表
    files_to_process = get_files_from_dir(args.dir)

    # 批量处理文件
    for filename in files_to_process:
        result = process_single_file(
            filename,
            loader,
            config_manager,
            args.config
        )
        print(result)


if __name__ == "__main__":
    main()
