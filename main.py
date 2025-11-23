"""
PutnamBench 主入口文件
适配 PutnamBench 数据格式
"""

from src.utils.putnam_loader import PutnamLoader
from src.agent.coordinator import AgentCoordinator
from src.utils.config_manager import ConfigManager
from typing import Dict, Tuple, Optional
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

    # 解决问题（从配置文件读取 max_retries）
    # 注意：这里需要从配置文件中读取 max_retries，但为了保持接口简洁，
    # 我们可以在 coordinator.solve() 中从 config 读取，或者在这里传递
    result = coordinator.solve(problem_description, task_template)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="LLM-Agent-Lean4-RL: 自动生成和验证 Lean4 形式化证明（PutnamBench 格式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        type=str,
        help="要处理的问题文件（如 putnam_1962_a1.lean）"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的问题文件"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/default.yaml",
        help="配置文件路径（默认: config/default.yaml）"
    )

    args = parser.parse_args()

    config_manager = ConfigManager(args.config)
    print(f"✅ 加载配置文件: {args.config}")

    benchmarks_dir = config_manager.get_benchmarks_dir()
    loader = PutnamLoader(benchmarks_dir)

    if args.list:
        files = loader.list_all_problems()
        print(f"找到 {len(files)} 个问题文件：")
        for f in files[:20]:  # 只显示前20个
            print(f"  - {f}")
        if len(files) > 20:
            print(f"  ... 还有 {len(files) - 20} 个文件")
        return

    if not args.file:
        print("❌ 错误: 请指定 --file 参数或使用 --list 查看可用文件")
        parser.print_help()
        return

    # 加载问题
    print(f"📖 加载问题: {args.file}")
    try:
        problem = loader.load_file(args.file)
        print(f"   定理名称: {problem.theorem_name}")
        print(f"   问题描述: {problem.docstring}")
        print(f"   定理语句: {problem.theorem_statement}")
        print(f"   导入语句: {problem.imports}")
        print(f"   打开语句: {problem.opens}")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return

    # 转换为任务格式
    print("\n🔄 转换为任务格式...")
    problem_description, task_template = loader.convert_to_task_format(problem)
    print(f"   问题描述: {problem_description[:200]}...")  # 只显示前200字符
    print(f"   任务模板: {task_template[:200]}...")  # 只显示前200字符

    # 从配置文件获取配置信息
    planning_model = config_manager.get("llm.planning.model", "o3-mini")
    generation_model = config_manager.get("llm.generation.model", "gpt-4o")
    max_retries = config_manager.get_max_retries()

    # 执行主工作流程（使用配置文件）
    print("\n🚀 开始执行主工作流程...\n")
    print(f"   配置文件: {args.config}")
    print(f"   规划模型: {planning_model}")
    print(f"   生成模型: {generation_model}")
    print(f"   最大重试: {max_retries}")
    print()

    try:
        result = main_workflow_putnam(
            problem_description,
            task_template,
            config=None,  # 不传 config，让函数从配置文件加载
            config_file=args.config
        )

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

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
