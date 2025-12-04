"""
测试 Lean4 验证环境的错误信息
"""

from src.verifier.lean4_runner import Lean4Runner

# 项目路径
PROJECT_PATH = "/home/wangtuo/WorkSpace/lean/LLM-Agent-Lean4-RL/data/benchmarks/lean4"

# 创建 runner
runner = Lean4Runner(project_path=PROJECT_PATH, cleanup=False)

# 测试代码示例 - 各种错误类型
test_cases = {
    "错误1 - 使用 sorry（会产生警告）": """
import Mathlib

theorem wrong_proof_1 : ∀ n : ℕ, n + 0 = n := by
  intro n
  sorry
""",
    "错误2 - 不可能证明的命题（1+1=3）": """
import Mathlib

theorem wrong_proof_2 : 1 + 1 = 3 := by
  rfl
""",
    "错误3 - 未定义的策略/标识符": """
import Mathlib

theorem wrong_proof_3 : ∀ x : ℕ, x > 0 → x ≥ 1 := by
  intro x hx
  undefined_tactic
""",
    "错误4 - 证明不完整（目标未完成）": """
import Mathlib

theorem wrong_proof_4 : ∀ a b : ℕ, a + b = b + a := by
  intro a b
""",
    "错误5 - 类型不匹配": """
import Mathlib

theorem wrong_proof_5 : (1 : ℕ) = (1 : ℤ) := by
  rfl
""",
    "正确的证明（对比参考）": """
import Mathlib

theorem correct_proof : ∀ n : ℕ, n = n := by
  intro n
  rfl
""",
}

print("=" * 80)
print("Lean4 验证环境错误信息测试")
print("=" * 80)

for name, code in test_cases.items():
    print(f"\n{'=' * 80}")
    print(f"测试: {name}")
    print("-" * 40)
    print("代码:")
    print(code)
    print("-" * 40)

    result = runner.execute(code, timeout=120)

    print(f"成功: {result.success}")
    print(f"执行时间: {result.execution_time:.2f}秒")

    if result.error_type:
        print(f"错误类型: {result.error_type}")

    if result.error_location:
        print(f"错误位置: {result.error_location}")

    if result.goals:
        print(f"未完成目标: {result.goals}")

    print("\n输出/错误信息:")
    print(result.output)
    print("=" * 80)
