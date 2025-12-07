#!/usr/bin/env python3
"""
测试 VerificationAgent 的脚本
用于诊断 Lean 4 验证环境的问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.verifier.lean4_runner import Lean4Runner
from src.agent.verification_agent import VerificationAgent

def test_simple_theorem():
    """测试一个简单的定理"""
    print("=" * 80)
    print("测试 1: 简单的正确定理")
    print("=" * 80)
    
    code = """
import Mathlib

theorem simple_test : 1 + 1 = 2 := by
  rfl
"""
    
    # 创建 Lean4Runner
    lean_runner = Lean4Runner(project_path="data/benchmarks/lean4/test")
    
    # 创建 VerificationAgent
    verification_agent = VerificationAgent(lean_runner=lean_runner)
    
    # 执行验证
    print(f"代码:\n{code}")
    print("\n执行验证...")
    success, output = verification_agent.execute(code)
    
    print(f"\n结果:")
    print(f"  成功: {success}")
    print(f"  输出: {output}")
    print()
    
    return success

def test_error_theorem():
    """测试一个有错误的定理"""
    print("=" * 80)
    print("测试 2: 有错误的定理")
    print("=" * 80)
    
    code = """
import Mathlib

theorem error_test : 1 + 1 = 3 := by
  rfl
"""
    
    lean_runner = Lean4Runner(project_path="data/benchmarks/lean4/test")
    verification_agent = VerificationAgent(lean_runner=lean_runner)
    
    print(f"代码:\n{code}")
    print("\n执行验证...")
    success, output = verification_agent.execute(code)
    
    print(f"\n结果:")
    print(f"  成功: {success}")
    print(f"  错误信息: {output}")
    print()
    
    return not success  # 应该失败才对

def test_complex_theorem():
    """测试一个稍微复杂的定理"""
    print("=" * 80)
    print("测试 3: 复杂定理")
    print("=" * 80)
    
    code = """
import Mathlib

theorem test_nat_add (n m : ℕ) : n + m = m + n := by
  exact Nat.add_comm n m
"""
    
    lean_runner = Lean4Runner(project_path="data/benchmarks/lean4/test")
    verification_agent = VerificationAgent(lean_runner=lean_runner)
    
    print(f"代码:\n{code}")
    print("\n执行验证...")
    success, output = verification_agent.execute(code)
    
    print(f"\n结果:")
    print(f"  成功: {success}")
    print(f"  输出: {output}")
    print()
    
    return success

def test_environment():
    """测试环境配置"""
    print("=" * 80)
    print("测试 0: 环境检查")
    print("=" * 80)
    
    import subprocess
    
    # 检查 lake
    try:
        result = subprocess.run(
            ["which", "lake"],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        print(f"lake 路径: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ lake 未找到: {e}")
        return False
    
    # 检查 lean
    try:
        result = subprocess.run(
            ["which", "lean"],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        print(f"lean 路径: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ lean 未找到: {e}")
        return False
    
    # 检查项目目录
    project_path = Path("data/benchmarks/lean4/test")
    print(f"项目路径: {project_path.absolute()}")
    print(f"项目存在: {project_path.exists()}")
    
    if project_path.exists():
        lakefile = project_path / "lakefile.lean"
        print(f"lakefile.lean 存在: {lakefile.exists()}")
        
        lake_manifest = project_path / "lake-manifest.json"
        print(f"lake-manifest.json 存在: {lake_manifest.exists()}")
    
    print()
    return True

def main():
    """主测试函数"""
    print("\n🔍 开始测试 VerificationAgent\n")
    
    # 测试环境
    if not test_environment():
        print("❌ 环境检查失败！")
        return
    
    # 运行测试
    results = []
    
    try:
        results.append(("简单定理", test_simple_theorem()))
    except Exception as e:
        print(f"❌ 测试 1 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("简单定理", False))
    
    try:
        results.append(("错误定理", test_error_theorem()))
    except Exception as e:
        print(f"❌ 测试 2 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("错误定理", False))
    
    try:
        results.append(("复杂定理", test_complex_theorem()))
    except Exception as e:
        print(f"❌ 测试 3 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("复杂定理", False))
    
    # 总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查上面的错误信息")

if __name__ == "__main__":
    main()

