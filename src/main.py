"""
主入口文件
参考 Lean4-LLM-Ai-Agent-Mooc 的 main.py
"""

import os
import sys
import argparse
from typing import Dict, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.coordinator import AgentCoordinator


def get_problem_and_code_from_taskpath(task_path: str) -> Tuple[str, str]:
    """
    从任务路径读取问题描述和代码模板
    参考 Lean4-LLM-Ai-Agent-Mooc 的 get_problem_and_code_from_taskpath 函数
    
    Args:
        task_path: 任务目录路径（包含 description.txt 和 task.lean）
    
    Returns:
        Tuple[str, str]: (问题描述, Lean4 代码模板)
    """
    description_path = os.path.join(task_path, "description.txt")
    task_lean_path = os.path.join(task_path, "task.lean")
    
    if not os.path.exists(description_path):
        raise FileNotFoundError(f"找不到文件: {description_path}")
    if not os.path.exists(task_lean_path):
        raise FileNotFoundError(f"找不到文件: {task_lean_path}")
    
    with open(description_path, "r", encoding="utf-8") as f:
        problem_description = f.read()
    
    with open(task_lean_path, "r", encoding="utf-8") as f:
        task_template = f.read()
    
    return problem_description, task_template


def main_workflow(problem_description: str, task_template: str) -> Dict[str, str]:
    """
    主工作流程
    参考 Lean4-LLM-Ai-Agent-Mooc 的 main_workflow 函数
    
    Args:
        problem_description: 问题描述
        task_template: 任务模板
    
    Returns:
        Dict[str, str]: 包含 "code" 和 "proof" 的字典
    """
    # 创建协调器
    coordinator = AgentCoordinator.from_config()
    
    # 解决问题
    result = coordinator.solve(problem_description, task_template)
    
    return result


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="LLM-Agent-Lean4-RL: 自动生成和验证 Lean4 形式化证明")
    parser.add_argument(
        "--task-path",
        type=str,
        required=True,
        help="任务目录路径（包含 description.txt 和 task.lean）"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="最大重试次数（默认: 5）"
    )
    
    args = parser.parse_args()
    
    # 读取问题描述和模板
    print(f"📖 读取任务: {args.task_path}")
    problem_description, task_template = get_problem_and_code_from_taskpath(args.task_path)
    
    # 执行主工作流程
    print("\n🚀 开始执行主工作流程...\n")
    result = main_workflow(problem_description, task_template)
    
    # 输出结果
    print("\n" + "="*50)
    print("✅ 完成！生成的代码和证明：")
    print("="*50)
    print("\n[代码]")
    print(result["code"])
    print("\n[证明]")
    print(result["proof"])
    print("="*50)


if __name__ == "__main__":
    main()

