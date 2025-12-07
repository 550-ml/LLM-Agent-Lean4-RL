"""
PutnamBench 数据加载器
用于加载和处理 PutnamBench 数据集的 .lean 文件
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class PutnamProblem:
    file_path: str
    file_name: str
    total_content: str
    header: str
    problem: str
    docstring: str  # 问题描述，中文


class PutnamLoader:
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)

    def load_lean_files(self):
        """加载所有 .lean 文件"""
        return [f for f in self.data_path.glob("*.lean")]

    def load_file(self, filename: str) -> PutnamProblem:
        if os.path.isabs(filename) or os.path.dirname(filename):
            file_path = filename

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self._parse_lean_file(content, file_path)

    def _parse_lean_file(self, content: str, file_path: str) -> PutnamProblem:
        """解析 Lean4 文件（简化版）"""
        # 提取 imports
        imports = "\n".join(re.findall(r"^import\s+.*$", content, re.MULTILINE))

        # 提取 opens
        opens = "\n".join(re.findall(r"^open\s+.*$", content, re.MULTILINE))

        # 合并 header（imports + opens）
        header = f"{imports}\n{opens}".strip()

        # 提取 docstring
        docstring_match = re.search(r"/--(.*?)-/", content, re.DOTALL)
        docstring = docstring_match.group(1).strip() if docstring_match else ""

        # 提取 theorem 语句（从 theorem 开始到文件末尾）
        theorem_match = re.search(r"(?:theorem|def|abbrev)\s+\w+", content)
        if not theorem_match:
            raise ValueError(f"无法找到定理: {file_path}")

        problem = content[theorem_match.start() :].strip()

        return PutnamProblem(
            file_path=file_path,
            file_name=Path(file_path).name,
            total_content=content,
            header=header,
            problem=problem,
            docstring=docstring,
        )

    def list_all_problems(self) -> List[str]:
        """
        列出所有问题文件

        Returns:
            List[str]: 文件名列表
        """
        if not os.path.exists(self.src_dir):
            return []

        files = [f for f in os.listdir(self.src_dir) if f.endswith(".lean")]
        return sorted(files)
