#!/usr/bin/env python3
"""
简单的 LLM 测试脚本
加载 LLM，发送消息，查看回复
"""

import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("config/api_key.env")

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.llm.factory import LLMFactory


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 LLM 测试脚本")
    print("=" * 80)

    # 1. 配置 LLM（可以直接修改这里的参数）
    print("\n📋 配置 LLM...")
    llm_config = {
        "model_name": "gpt-5-mini",  # 修改为你想要的模型
        "temperature": 1.0,
        "max_tokens": 4500,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "max_retries": 3,
        "retry_delay": 1.0,
        "base_url": "https://api.chatanywhere.tech",  # 修改为你的 API 地址
    }

    print(f"  模型: {llm_config['model_name']}")
    print(f"  温度: {llm_config['temperature']}")
    print(f"  API: {llm_config['base_url']}")

    # 2. 创建 LLM 实例
    print("\n🔧 创建 LLM 实例...")
    try:
        llm = LLMFactory.create_from_dict(llm_config)
        print("  ✅ LLM 创建成功")
    except Exception as e:
        print(f"  ❌ 创建失败: {e}")
        traceback.print_exc()
        return

    # 3. 发送测试消息
    print("\n" + "=" * 80)
    print("💬 发送测试消息")
    print("=" * 80)

    # 在这里修改你要发送的消息
    test_message = """
    You are a Lean 4 expert. Your goal is to write a proof in Lean 4, according to the given proof sketch, using the supplied theorems.

Proof sketch:
theorem and_chain_test (P Q R : Prop) (h₁ : P ∧ Q) (h₂ : Q ∧ R) : Q ∧ (P ∧ R) := by
  -- Extract P from h₁
  have p_from_h1 : P := by
    exact h₁.left
  -- Extract Q from h₁
  have q_from_h1 : Q := by
    exact h₁.right
  -- Extract Q from h₂
  have q_from_h2 : Q := by
    exact h₂.left
  -- Extract R from h₂
  have r_from_h2 : R := by
    exact h₂.right
  -- Build P ∧ R from p_from_h1 and r_from_h2
  have p_and_r : P ∧ R := by
    apply And.intro
    · exact p_from_h1
    · exact r_from_h2
  -- Finally combine Q (choose q_from_h1) and P ∧ R to get Q ∧ (P ∧ R)
  apply And.intro
  · exact q_from_h1
  · exact p_and_r

Theorems:
['theorem p_from_h1 (P Q R : Prop) (h₁ : P ∧ Q) (h₂ : Q ∧ R) : P := by\nsorry\n', 'theorem q_from_h1 (P Q R : Prop) (h₁ : P ∧ Q) (h₂ : Q ∧ R) : Q := by\nsorry\n', 'theorem q_from_h2 (P Q R : Prop) (h₁ : P ∧ Q) (h₂ : Q ∧ R) : Q := by\nsorry\n', 'theorem r_from_h2 (P Q R : Prop) (h₁ : P ∧ Q) (h₂ : Q ∧ R) : R := by\nsorry\n', 'theorem p_and_r (P Q R : Prop) (h₁ : P ∧ Q) (h₂ : Q ∧ R) (p_from_h1 : P) (r_from_h2 : R) : P ∧ R := by\nsorry\n']

Instructions:
1. You can assume that the theorems are correct and use them directly in your proof.
2. Do NOT modify the given theorems.
3. Do NOT prove the given theorems.
4. Do NOT modify the given proof sketch steps. Simply apply the given theorems to complete the missing `sorry` steps.
5. Do NOT use `sorry` in your proof.
6. Do NOT include any imports or definitions or open statements.
7. Do NOT re-define the given theorems in your response.
8. Do NOT write a proof for any subgoal from scratch. ALWAYS use the supplied theorems.

IMPORTANT INSTRUCTION: Do NOT, under ANY circumstances, allow division and subtraction operations on natural number literals with UNDEFINED types, unless REQUIRED by the theorem statement. For example, do NOT allow literals like `1 / 3` or `2 / 5` or `1 - 3`. ALWAYS specify the types. AVOID natural number arithmetic UNLESS NEEDED by the theorem statement. ALWAYS specify types when describing fractions. For example, ((2 : R) / 3) or ((2 : Q) / 3) instead of (2 / 3). Do this everywhere EXCEPT the given theorem statement.

IMPORTANT INSTRUCTION: Do NOT, under ANY circumstances, allow division and subtraction operations on variables of type natural numbers (Nat or N), unless REQUIRED by the theorem statement. For example, do NOT allow expressions like (a-b) or (a/b) where a, b are of type N. ALWAYS cast the variables to a suitable type (Z, Q or R) when performing arithmetic operations. AVOID natural number arithmetic UNLESS NEEDED by the theorem statement.

Your answer should be a single Lean 4 block containing the completed proof for the given theorem.


    """

    print(f"\n👤 发送消息: {test_message}")
    print("\n🤔 等待 LLM 回复...")

    try:
        messages = [{"role": "user", "content": test_message}]
        response = llm.get_response(messages)

        # 显示回复
        print("\n" + "=" * 80)
        print("🤖 LLM 回复:")
        print("=" * 80)
        print(response)
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
