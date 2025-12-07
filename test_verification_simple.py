#!/usr/bin/env python3
"""
简单测试 Lean4Runner 的脚本
直接测试底层验证功能，不依赖其他模块
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.verifier.lean4_runner import Lean4Runner

def test_environment():
    """测试环境配置"""
    print("=" * 80)
    print("环境检查")
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
        lake_path = result.stdout.strip()
        print(f"✅ lake 路径: {lake_path}")
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
        lean_path = result.stdout.strip()
        print(f"✅ lean 路径: {lean_path}")
    except Exception as e:
        print(f"❌ lean 未找到: {e}")
        return False
    
    # 检查 PATH
    print(f"\nPATH 环境变量:")
    path_dirs = os.environ.get('PATH', '').split(':')
    for i, p in enumerate(path_dirs[:5]):  # 只显示前5个
        print(f"  {i+1}. {p}")
    print(f"  ... (共 {len(path_dirs)} 个目录)")
    
    # 检查项目目录
    project_path = Path("data/benchmarks/lean4")
    print(f"\n项目配置:")
    print(f"  项目路径: {project_path.absolute()}")
    print(f"  项目存在: {project_path.exists()}")
    
    if project_path.exists():
        lakefile = project_path / "lakefile.lean"
        print(f"  lakefile.lean: {lakefile.exists()}")
        
        lake_manifest = project_path / "lake-manifest.json"
        print(f"  lake-manifest.json: {lake_manifest.exists()}")
        
        # 列出目录内容
        print(f"\n  目录内容:")
        for item in sorted(project_path.iterdir())[:10]:
            print(f"    - {item.name}")
    
    print()
    return True

def test_simple_correct():
    """测试 1: 简单的正确定理"""
    print("=" * 80)
    print("测试 1: 简单的正确定理 (1 + 1 = 2)")
    print("=" * 80)
    
    code = """import Mathlib

theorem simple_test : 1 + 1 = 2 := by
  rfl
"""
    
    print(f"代码:\n{code}")
    print("\n执行验证...")
    
    try:
        lean_runner = Lean4Runner(project_path="data/benchmarks/lean4")
        result = lean_runner.execute(code)
        
        print(f"\n结果:")
        print(f"  成功: {result.success}")
        print(f"  输出: {result.output}")
        if hasattr(result, 'error_type'):
            print(f"  错误类型: {result.error_type}")
        if hasattr(result, 'execution_time'):
            print(f"  执行时间: {result.execution_time:.2f}s")
        print()
        
        return result.success
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_error():
    """测试 2: 有错误的定理"""
    print("=" * 80)
    print("测试 2: 有错误的定理 (1 + 1 = 3)")
    print("=" * 80)
    
    code = """import Mathlib

theorem error_test : 1 + 1 = 3 := by
  rfl
"""
    
    print(f"代码:\n{code}")
    print("\n执行验证...")
    
    try:
        lean_runner = Lean4Runner(project_path="data/benchmarks/lean4")
        result = lean_runner.execute(code)
        
        print(f"\n结果:")
        print(f"  成功: {result.success}")
        print(f"  输出: {result.output}")
        if hasattr(result, 'error_type'):
            print(f"  错误类型: {result.error_type}")
        if hasattr(result, 'error_line'):
            print(f"  错误行: {result.error_line}")
        if hasattr(result, 'execution_time'):
            print(f"  执行时间: {result.execution_time:.2f}s")
        print()
        
        # 这个测试期望失败
        return not result.success
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_mathlib():
    """测试 3: 使用 Mathlib 的定理"""
    print("=" * 80)
    print("测试 3: 使用 Mathlib 定理 (Nat.add_comm)")
    print("=" * 80)
    
    code = """import Mathlib

theorem test_nat_add (n m : ℕ) : n + m = m + n := by
  exact Nat.add_comm n m
"""
    
    print(f"代码:\n{code}")
    print("\n执行验证...")
    
    try:
        lean_runner = Lean4Runner(project_path="data/benchmarks/lean4")
        result = lean_runner.execute(code)
        
        print(f"\n结果:")
        print(f"  成功: {result.success}")
        print(f"  输出: {result.output}")
        if hasattr(result, 'error_type'):
            print(f"  错误类型: {result.error_type}")
        if hasattr(result, 'execution_time'):
            print(f"  执行时间: {result.execution_time:.2f}s")
        print()
        
        return result.success
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n🔍 开始测试 Lean4Runner\n")
    
    # 测试环境
    if not test_environment():
        print("❌ 环境检查失败！")
        return
    
    # 运行测试
    results = []
    
    results.append(("简单正确定理", test_simple_correct()))
    results.append(("简单错误定理", test_simple_error()))
    results.append(("Mathlib 定理", test_with_mathlib()))
    
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
        print("\n🎉 所有测试通过！Lean 4 验证环境正常工作")
    else:
        print("\n⚠️  部分测试失败，请检查上面的错误信息")

if __name__ == "__main__":
    main()

