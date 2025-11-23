"""
PutnamBench 数据加载器
用于加载和处理 PutnamBench 数据集的 .lean 文件
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PutnamProblem:
    """Putnam 问题数据结构"""
    file_path: str
    theorem_name: str
    docstring: str  # 问题描述（从 /-- ... -/ 中提取）
    theorem_statement: str  # 完整的定理语句（包含 sorry）
    imports: List[str]  # import 语句
    opens: List[str]  # open 语句


class PutnamLoader:
    """
    PutnamBench 数据加载器

    从 .lean 文件中提取定理信息，并转换为适合 Agent 使用的格式
    """

    def __init__(self, benchmarks_dir: str):
        """
        初始化加载器

        Args:
            benchmarks_dir: PutnamBench 数据目录（包含 src/ 文件夹）
        """
        self.benchmarks_dir = benchmarks_dir
        self.src_dir = os.path.join(benchmarks_dir, "src")

    def load_file(self, filename: str) -> PutnamProblem:
        """
        加载单个 .lean 文件

        Args:
            filename: 文件名（如 "putnam_1962_a1.lean"）或完整路径

        Returns:
            PutnamProblem: 问题数据
        """
        if os.path.isabs(filename) or os.path.dirname(filename):
            file_path = filename
        else:
            file_path = os.path.join(self.src_dir, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self._parse_lean_file(content, file_path)

    def _parse_lean_file(self, content: str, file_path: str) -> PutnamProblem:
        """
        解析 Lean4 文件内容

        Args:
            content: 文件内容
            file_path: 文件路径

        Returns:
            PutnamProblem: 问题数据
        """
        # 提取 imports
        imports = re.findall(r'^import\s+(\S+)', content, re.MULTILINE)

        # 提取 opens
        opens = re.findall(r'^open\s+(\S+)', content, re.MULTILINE)

        # 提取 docstring（/-- ... -/）
        # Lean4 的 docstring 格式是 /-- ... -/（开头两个-，结尾一个-）
        docstring_match = re.search(r'/--(.*?)-/', content, re.DOTALL)
        docstring = docstring_match.group(1).strip() if docstring_match else ""

        # 提取定理名称和语句
        # 匹配 theorem 或 def 开头的定义，直到 sorry 或 :=
        theorem_pattern = r'(theorem|def|abbrev)\s+(\w+)[\s\S]*?(?:sorry|:=)'
        theorem_match = re.search(theorem_pattern, content, re.MULTILINE)

        if not theorem_match:
            raise ValueError(f"无法找到定理定义: {file_path}")

        theorem_name = theorem_match.group(2)

        # 提取完整的定理语句（从 theorem/def 开始到 sorry 结束）
        # 使用更精确的方法：逐行解析
        lines = content.split('\n')
        in_theorem = False
        theorem_lines = []
        brace_count = 0
        paren_count = 0

        for i, line in enumerate(lines):
            # 检查是否开始定理定义
            if re.match(r'\s*(?:theorem|def|abbrev)\s+\w+', line):
                in_theorem = True
                theorem_lines = [line]
                # 计算初始的括号和花括号
                brace_count = line.count('{') - line.count('}')
                paren_count = line.count('(') - line.count(')')
                continue

            if in_theorem:
                theorem_lines.append(line)
                # 更新括号计数
                brace_count += line.count('{') - line.count('}')
                paren_count += line.count('(') - line.count(')')

                # 如果遇到 sorry 且括号匹配，说明定理结束
                if 'sorry' in line and brace_count == 0 and paren_count == 0:
                    break

        theorem_statement = '\n'.join(theorem_lines).strip()

        return PutnamProblem(
            file_path=file_path,
            theorem_name=theorem_name,
            docstring=docstring,
            theorem_statement=theorem_statement,
            imports=imports,
            opens=opens
        )

    def list_all_problems(self) -> List[str]:
        """
        列出所有问题文件

        Returns:
            List[str]: 文件名列表
        """
        if not os.path.exists(self.src_dir):
            return []

        files = [f for f in os.listdir(self.src_dir) if f.endswith('.lean')]
        return sorted(files)

    def convert_to_task_format(self, problem: PutnamProblem) -> Tuple[str, str]:
        """
        将 Putnam 问题转换为任务格式（description + task_template）

        Args:
            problem: Putnam 问题

        Returns:
            Tuple[str, str]: (problem_description, task_template)
        """
        # 问题描述：使用 docstring
        problem_description = f"""-----Description-----
{problem.docstring}

-----Theorem-----
{problem.theorem_name}

-----Statement-----
{problem.theorem_statement}"""

        # 生成任务模板：将 sorry 替换为占位符
        # 构建 imports 和 opens
        import_lines = '\n'.join([f"import {imp}" for imp in problem.imports])
        open_lines = '\n'.join([f"open {op}" for op in problem.opens])

        # 将定理语句中的 sorry 替换为占位符
        theorem_template = problem.theorem_statement

        # 如果定理是 theorem ... := by sorry 的形式（最常见）
        if ':= by' in theorem_template and 'sorry' in theorem_template:
            # 替换 := by sorry 为 := by {{proof}}
            # 处理多行的情况
            theorem_template = re.sub(
                r':=\s+by\s+sorry',
                ':= by\n  -- << PROOF START >>\n  {{proof}}\n  -- << PROOF END >>',
                theorem_template,
                flags=re.MULTILINE
            )
        elif ':= sorry' in theorem_template:
            # 替换 := sorry 为 := {{code}}（用于 def 或 abbrev）
            theorem_template = re.sub(
                r':=\s+sorry',
                ':= -- << CODE START >>\n  {{code}}\n  -- << CODE END >>',
                theorem_template,
                flags=re.MULTILINE
            )
        else:
            # 默认情况：替换 sorry 为证明占位符
            # 保持缩进
            lines = theorem_template.split('\n')
            new_lines = []
            for line in lines:
                if 'sorry' in line:
                    # 保持原有缩进
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    new_lines.append(f"{indent_str}-- << PROOF START >>")
                    new_lines.append(f"{indent_str}{{proof}}")
                    new_lines.append(f"{indent_str}-- << PROOF END >>")
                else:
                    new_lines.append(line)
            theorem_template = '\n'.join(new_lines)

        # 构建完整的任务模板
        template_parts = []
        if import_lines:
            template_parts.append(import_lines)
        if open_lines:
            template_parts.append(open_lines)
        if template_parts:
            template_parts.append("")  # 空行

        template_parts.append(theorem_template)

        task_template = '\n'.join(template_parts)

        return problem_description, task_template
