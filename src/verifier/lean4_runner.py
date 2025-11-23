"""
Lean4 代码执行器
参考 Lean4-LLM-Ai-Agent-Mooc 的 lean_runner.py
"""

import subprocess
import os
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class Lean4Result:
    """Lean4 执行结果"""
    success: bool
    output: str
    error_message: Optional[str] = None
    goals: List[str] = field(default_factory=list)  # 当前证明目标
    hypotheses: List[str] = field(default_factory=list)  # 当前假设


class Lean4Runner:
    """
    Lean4 代码执行器
    
    参考 Lean4-LLM-Ai-Agent-Mooc 的 execute_lean_code 函数
    但设计为类，更易于扩展和维护
    """
    
    def __init__(self, project_path: str = "lean_playground", lean_version: str = "4.24.0"):
        """
        初始化 Lean4 执行器
        
        Args:
            project_path: Lean4 项目路径（临时文件存放目录）
            lean_version: Lean4 版本（目前未使用，但保留用于未来扩展）
        """
        self.project_path = project_path
        self.lean_version = lean_version
        self.temp_file = "TempTest.lean"
    
    def execute(self, code: str, timeout: int = 60) -> Lean4Result:
        """
        执行 Lean4 代码
        
        Args:
            code: Lean4 代码
            timeout: 超时时间（秒）
        
        Returns:
            Lean4Result: 执行结果
        """
        temp_path = os.path.join(self.project_path, self.temp_file)
        
        try:
            # 确保目录存在
            os.makedirs(self.project_path, exist_ok=True)
            
            # 写入临时文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 执行 Lean 编译
            result = subprocess.run(
                ["lake", "lean", temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,  # 不抛出异常，让我们自己处理错误
                timeout=timeout
            )
            
            # 处理执行结果
            if result.returncode == 0:
                # 成功
                output = result.stdout.strip()
                return Lean4Result(
                    success=True,
                    output=f"Lean code executed successfully.\n{output}" if output else "Lean code executed successfully."
                )
            else:
                # 失败，提取错误信息
                error_message = result.stderr.strip()
                if not error_message and result.stdout.strip():
                    # 有些错误在 stdout 中
                    error_message = result.stdout.strip()
                
                return Lean4Result(
                    success=False,
                    output=f"Lean Error: {error_message}" if error_message else f"Lean execution failed with return code {result.returncode}",
                    error_message=error_message or f"Return code: {result.returncode}"
                )
        
        except FileNotFoundError:
            return Lean4Result(
                success=False,
                output="Error: Lean executable not found. Please install Lean 4 and ensure 'lake' is in your PATH.",
                error_message="Lean executable not found"
            )
        except subprocess.TimeoutExpired:
            return Lean4Result(
                success=False,
                output=f"Error: Lean execution timed out after {timeout} seconds.",
                error_message="Execution timeout"
            )
        except PermissionError:
            return Lean4Result(
                success=False,
                output=f"Error: Permission denied when writing to or executing {self.temp_file}",
                error_message="Permission denied"
            )
        except Exception as e:
            return Lean4Result(
                success=False,
                output=f"Unexpected error while running Lean: {str(e)}",
                error_message=str(e)
            )
    
    def check_syntax(self, code: str) -> bool:
        """
        检查语法（简单实现：尝试执行）
        
        Args:
            code: Lean4 代码
        
        Returns:
            bool: 语法是否正确
        """
        result = self.execute(code)
        return result.success


# 为了兼容 Lean4-LLM-Ai-Agent-Mooc 的接口，提供一个函数形式的接口
def execute_lean_code(code: str, project_path: str = "lean_playground") -> str:
    """
    执行 Lean4 代码（函数接口，兼容旧代码）
    
    Args:
        code: Lean4 代码
        project_path: 项目路径
    
    Returns:
        str: 执行结果或错误信息
    """
    runner = Lean4Runner(project_path=project_path)
    result = runner.execute(code)
    return result.output

