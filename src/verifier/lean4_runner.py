"""
Lean4 代码执行器
"""

import subprocess
import os
import re
import uuid
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Lean4Result:
    """Lean4 执行结果"""
    success: bool
    output: str
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # 错误类型（如：类型不匹配、未定义标识符等）
    # 错误位置 {"line": 10, "column": 5}
    error_location: Optional[Dict[str, int]] = None
    goals: List[str] = field(default_factory=list)  # 当前证明目标
    hypotheses: List[str] = field(default_factory=list)  # 当前假设
    execution_time: float = 0.0  # 执行时间（秒）


class Lean4Runner:
    """
    Lean4 代码执行器（改进版）

    功能：
    1. 执行 Lean4 代码验证
    2. 解析错误信息（提取错误类型、位置等）
    3. 提取证明状态（goals, hypotheses）
    4. 支持并发验证（唯一临时文件）
    5. 自动清理临时文件

    使用方法：
        runner = Lean4Runner(project_path="lean_playground")
        result = runner.execute(lean_code)
        if result.success:
            print("验证成功！")
        else:
            print(f"验证失败: {result.error_message}")
    """

    def __init__(
        self,
        project_path: str,
        lean_version: str = None,
        cleanup: bool = False
    ):
        """
        初始化 Lean4 执行器

        Args:
            project_path: Lean4 项目路径（临时文件存放目录）
            lean_version: Lean4 版本（目前未使用，但保留用于未来扩展）
            cleanup: 是否自动清理临时文件
        """
        self.project_path = project_path
        self.lean_version = lean_version
        self.cleanup = cleanup
        self.temp_files = []  # 跟踪创建的临时文件，用于清理

    def execute(self, code: str, timeout: int = 60) -> Lean4Result:
        import time
        start_time = time.time()

        # 生成唯一临时文件名（支持并发）
        temp_file = f"temp_{uuid.uuid4().hex[:8]}.lean"
        temp_path = os.path.join(self.project_path+"/temp", temp_file)
        self.temp_files.append(temp_path)

        try:
            # 确保目录存在
            os.makedirs(self.project_path, exist_ok=True)

            # 写入临时文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(code)

            logger.debug(f"执行 Lean4 验证: {temp_file}")

            # 执行 Lean 编译验证
            result = subprocess.run(
                ["lake", "lean", temp_path],
                cwd=self.project_path,  # 在项目目录中执行
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,  # 不抛出异常，让我们自己处理错误
                timeout=timeout
            )

            execution_time = time.time() - start_time

            # 处理执行结果
            if result.returncode == 0:
                # 验证成功
                output = result.stdout.strip()
                return Lean4Result(
                    success=True,
                    output=output or "验证成功：代码编译通过",
                    execution_time=execution_time
                )
            else:
                # 验证失败，解析错误信息
                error_text = result.stderr.strip() or result.stdout.strip()
                parsed_error = self._parse_error(error_text)

                return Lean4Result(
                    success=False,
                    output=parsed_error["formatted_message"],
                    error_message=parsed_error["error_message"],
                    error_type=parsed_error["error_type"],
                    error_location=parsed_error["error_location"],
                    goals=parsed_error.get("goals", []),
                    hypotheses=parsed_error.get("hypotheses", []),
                    execution_time=execution_time
                )

        except FileNotFoundError:
            return Lean4Result(
                success=False,
                output="错误：未找到 Lean 可执行文件。请安装 Lean 4 并确保 'lake' 在 PATH 中。",
                error_message="Lean executable not found",
                error_type="系统错误",
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return Lean4Result(
                success=False,
                output=f"错误：Lean 执行超时（{timeout} 秒）。",
                error_message="Execution timeout",
                error_type="超时错误",
                execution_time=timeout
            )
        except PermissionError:
            return Lean4Result(
                success=False,
                output=f"错误：权限被拒绝，无法写入或执行文件 {temp_file}",
                error_message="Permission denied",
                error_type="权限错误",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            logger.exception(f"执行 Lean4 时发生意外错误: {e}")
            return Lean4Result(
                success=False,
                output=f"意外错误：{str(e)}",
                error_message=str(e),
                error_type="未知错误",
                execution_time=time.time() - start_time
            )
        finally:
            # 清理临时文件
            if self.cleanup and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    if temp_path in self.temp_files:
                        self.temp_files.remove(temp_path)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    def _parse_error(self, error_text: str) -> Dict:
        if not error_text:
            return {
                "error_message": "未知错误",
                "error_type": "未知",
                "error_location": None,
                "formatted_message": "验证失败：未知错误",
                "goals": [],
                "hypotheses": []
            }

        # 提取错误类型
        error_type = self._extract_error_type(error_text)

        # 提取错误位置（行号和列号）
        error_location = self._extract_error_location(error_text)

        # 提取证明状态（goals 和 hypotheses）
        goals = self._extract_goals(error_text)
        hypotheses = self._extract_hypotheses(error_text)

        # 格式化错误消息
        formatted_parts = []
        if error_location:
            formatted_parts.append(f"位置：第 {error_location.get('line', '?')} 行")
        if error_type:
            formatted_parts.append(f"类型：{error_type}")
        formatted_parts.append(f"\n错误详情：\n{error_text}")

        if goals:
            formatted_parts.append(
                "\n未完成的证明目标：\n" + "\n".join(f"  - {g}" for g in goals[:5]))

        formatted_message = "\n".join(formatted_parts)

        return {
            "error_message": error_text,
            "error_type": error_type,
            "error_location": error_location,
            "formatted_message": formatted_message,
            "goals": goals,
            "hypotheses": hypotheses
        }

    def _extract_error_type(self, error_text: str) -> str:
        """提取错误类型"""
        error_lower = error_text.lower()

        # 常见错误类型
        if "type mismatch" in error_lower or "类型不匹配" in error_text:
            return "类型不匹配"
        elif "unknown identifier" in error_lower or "未定义的标识符" in error_text:
            return "未定义的标识符"
        elif "tactic failed" in error_lower or "策略失败" in error_text:
            return "策略失败"
        elif "goals" in error_lower and ("unsolved" in error_lower or "未解决" in error_text):
            return "证明目标未完成"
        elif "syntax error" in error_lower or "语法错误" in error_text:
            return "语法错误"
        elif "expected" in error_lower and "got" in error_lower:
            return "类型/值不匹配"
        elif "cannot find" in error_lower:
            return "找不到定义"
        elif "timeout" in error_lower:
            return "超时"
        else:
            return "编译错误"

    def _extract_error_location(self, error_text: str) -> Optional[Dict[str, int]]:
        """提取错误位置（行号和列号）"""
        location = {}

        # 匹配行号：line 10, line:10, 第10行 等
        line_patterns = [
            r'line\s+(\d+)',
            r'line:(\d+)',
            r'第\s*(\d+)\s*行',
            r':(\d+):(\d+)',  # file.lean:10:5 格式
        ]

        for pattern in line_patterns:
            match = re.search(pattern, error_text, re.IGNORECASE)
            if match:
                location["line"] = int(match.group(1))
                # 如果有列号（第二个捕获组）
                if len(match.groups()) > 1 and match.group(2):
                    location["column"] = int(match.group(2))
                break

        return location if location else None

    def _extract_goals(self, error_text: str) -> List[str]:
        """提取证明目标（goals）"""
        goals = []

        # 匹配 goals 部分
        # 常见格式：
        # goals: ...
        # unsolved goals: ...
        # ⊢ ...
        goal_patterns = [
            r'goals?\s*:\s*(.+?)(?:\n\n|\Z)',
            r'unsolved\s+goals?\s*:\s*(.+?)(?:\n\n|\Z)',
            r'⊢\s*(.+?)(?:\n|$)',
        ]

        for pattern in goal_patterns:
            matches = re.finditer(pattern, error_text,
                                  re.MULTILINE | re.DOTALL)
            for match in matches:
                goal_text = match.group(1).strip()
                # 分割多个目标
                goal_lines = [line.strip()
                              for line in goal_text.split('\n') if line.strip()]
                goals.extend(goal_lines)

        # 去重并限制数量
        return list(dict.fromkeys(goals))[:10]  # 最多返回10个

    def _extract_hypotheses(self, error_text: str) -> List[str]:
        """提取假设（hypotheses）"""
        hypotheses = []

        # 匹配假设部分
        # 常见格式：
        # h1 : type
        # h2 : type := value
        hyp_pattern = r'(\w+)\s*:\s*([^\n]+)'
        matches = re.finditer(hyp_pattern, error_text)

        for match in matches:
            hyp_name = match.group(1)
            hyp_type = match.group(2).strip()
            # 排除一些常见的非假设内容
            if hyp_name not in ['goals', 'error', 'type', 'expected', 'got']:
                hypotheses.append(f"{hyp_name} : {hyp_type}")

        return hypotheses[:10]  # 最多返回10个

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

    def cleanup_temp_files(self):
        """清理所有临时文件"""
        for temp_path in self.temp_files[:]:  # 使用切片复制列表
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                self.temp_files.remove(temp_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_path}: {e}")

    def __del__(self):
        """析构函数：清理临时文件"""
        if self.cleanup:
            self.cleanup_temp_files()


def execute_lean_code(code: str, project_path: str = "/home/wangtuo/WorkSpace/lean/LLM-Agent-Lean4-RL/data/benchmarks/lean4") -> str:
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


if __name__ == "__main__":
    code = """
    import Mathlib

    /--
    这是一个简单的测试定理：
    对任意自然数 a b，a + b = b + a。
    -/
    theorem my_add_comm (a b : Nat) : a + b = b + a := by
    -- 直接用库里的现成引理 Nat.add_comm
    exact Nat.add_comm a b
    """
    print(code)
    result = execute_lean_code(code)
    print(result)
