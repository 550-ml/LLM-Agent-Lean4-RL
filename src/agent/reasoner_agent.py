import logging
import re
from typing import Any, Dict, List, Optional

from ..llm.base import BaseLLM
from ..utils.prompt_loader import PromptLoader
from .base import BaseAgent

logger = logging.getLogger(__name__)


class ReasonerAgent(BaseAgent):
    """Reasoner 负责数学理解、检索与 proof sketch 的上游逻辑。"""

    def __init__(
        self,
        llm: BaseLLM,
        prompt_loader: PromptLoader,
        retriever: Any,
    ):
        super().__init__(llm, "ReasonerAgent")
        self.prompt_loader = prompt_loader

    def _normalize_lean_code(self, code: str) -> str:
        """规范化 Lean 代码：移除 import/open 语句和包装文本

        Args:
            code: 原始 Lean 代码

        Returns:
            str: 规范化后的 Lean 代码
        """
        if not code:
            return ""

        lines = code.splitlines()
        cleaned_lines = []
        in_outer_namespace = False
        namespace_depth = 0

        for line in lines:
            stripped = line.strip()

            # 移除 import 语句（所有位置的 import）
            if stripped.startswith("import "):
                continue

            # 移除 open 语句（所有位置的 open）
            if stripped.startswith("open "):
                continue

            # 处理 namespace：只移除最外层的 namespace ... end 包装
            if stripped.startswith("namespace "):
                if namespace_depth == 0:
                    # 最外层的 namespace，标记并跳过
                    in_outer_namespace = True
                    namespace_depth += 1
                    continue
                else:
                    # 嵌套的 namespace，保留
                    namespace_depth += 1
                    cleaned_lines.append(line)
                    continue

            if stripped == "end":
                if in_outer_namespace and namespace_depth == 1:
                    # 最外层的 end，移除
                    in_outer_namespace = False
                    namespace_depth = 0
                    continue
                elif namespace_depth > 1:
                    # 嵌套的 end，保留
                    namespace_depth -= 1
                    cleaned_lines.append(line)
                    continue
                # 其他情况（不在 namespace 中的 end）保留

            # 保留所有其他行
            cleaned_lines.append(line)

        # 重新组合，去除首尾空行
        result = "\n".join(cleaned_lines).strip()

        # 确保以换行符结尾（如果代码不为空）
        if result:
            result = result.rstrip() + "\n"

        return result

    def _extract_lean_code(self, response: str) -> str:
        """统一提取 Lean 代码的辅助方法

        先尝试用正则匹配代码块，如果失败则用 replace 清理
        然后进行 normalize：移除 import/open 和包装文本

        Args:
            response: LLM 的响应文本

        Returns:
            str: 提取并规范化后的 Lean 代码
        """
        if not response:
            return ""

        # 1. 先用正则匹配 ```lean 或 ```lean4 代码块
        pattern = re.compile(r"```(?:lean4?)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(response)
        if matches:
            code = matches[0]
        else:
            # 2. 如果正则匹配失败，用 replace 方法清理
            code = response.replace("```lean4", "").replace("```lean", "")
            code = code.replace("```", "")
            code = code.replace("```", "")
            code = code.strip()

        # 3. 规范化代码：移除 import/open 和包装文本
        return self._normalize_lean_code(code)

    # ------------------------------------------------------------------
    # Theorem Retrieval
    # ------------------------------------------------------------------
    def generate_search_queries(
        self,
        problem: str,
        docstring: str,
        error_message: Optional[str] = None,
    ):
        """生成检索定理相关的检索query

        Args:
            problem (str): _description_
            error_message (Optional[str], optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_search_query",
            problem=problem,
            docstring=docstring,
            error_message=error_message,
        )
        response = self.llm.get_response(
            [
                {"role": "user", "content": user_prompt},
            ]
        )
        queries = self._parse_string_list(response)
        return queries

    def select_relevant_theorems(
        self,
        problem,
        docstring,
        candidate_theorems: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """挑选相关定理"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_search_answer",
            problem=problem,
            docstring=docstring,
            theorems=candidate_theorems,
        )
        response = self.llm.get_response(
            [
                {"role": "user", "content": user_prompt},
            ]
        )
        logger.info(f"response: {response}")
        return self._parse_response_list(response, candidate_theorems)

    def _parse_string_list(self, response: str) -> List[str]:
        """从 LLM 输出里提取 <search>...</search> 标签作为检索查询。"""
        response = (response or "").strip()
        if not response:
            return []
        pattern = re.compile(r"<search>(.*?)</search>", re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(response)
        queries: List[str] = []
        for raw in matches:
            cleaned = raw.strip()
            if cleaned:
                queries.append(cleaned)
        return queries

    def _parse_response_list(
        self,
        response: str,
        candidate_theorems: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """解析 LLM 返回的定理列表

        期望格式:
        ```
        <theorem>Finset.exists_subsuperset_card_eq</theorem>
        <theorem>mem_convexHull_iff_exists_fintype</theorem>
        <theorem>collinear_iff_not_affineIndependent_of_ne</theorem>
        <theorem>collinear_iff_finrank_le_one</theorem>
        ```
        """
        response = (response or "").strip()
        if not response:
            return []

        pattern = re.compile(r"<theorem>(.*?)</theorem>", re.DOTALL | re.IGNORECASE)
        raw_matches = pattern.findall(response)

        selected: List[Dict[str, Any]] = []

        for raw in raw_matches:
            cleaned = raw.strip()
            if not cleaned:
                continue

            # LLM 输出：可能是 "Finset.exists_subsuperset_card_eq" 或 "mem_convexHull_iff_exists_fintype"
            parts = cleaned.split(".")
            lemma_name = parts[-1]  # 只取最后一段作为真正的 lemma 名

            match = None
            for th in candidate_theorems:
                th_name = th.get("name")
                if th_name is None:
                    continue

                # th_name 可能是 ["Finset", "exists_subsuperset_card_eq"]，也可能是 "exists_subsuperset_card_eq"
                if isinstance(th_name, list):
                    th_full = ".".join(th_name)
                    th_lemma = th_name[-1] if th_name else ""
                else:
                    th_full = str(th_name)
                    th_lemma = th_full.split(".")[-1]

                # 两种匹配策略：
                # 1. 完整名一致（包括模块前缀）
                # 2. lemma 名一致（只比最后一段）
                if cleaned == th_full or lemma_name == th_lemma:
                    match = th
                    break

            if match:
                selected.append(match)

        return selected

    # ------------------------------------------------------------------
    # sketch
    # ------------------------------------------------------------------
    def generate_informal_proof(
        self,
        problem,
        relevant_theorems: List[Dict[str, Any]],
        docstring: str,
    ) -> str:
        """生成非形式证明"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_generate_informal_proof",
            problem=problem,
            useful_theorems_section=relevant_theorems,
            docstring=docstring,
        )
        informal_proof = self.llm.get_response(
            [
                {"role": "user", "content": user_prompt},
            ]
        )
        return informal_proof

    def generate_sketch(self, problem: str, relevant_theorems: List[Dict[str, Any]], informal_proof: str) -> str:
        """生成证明带有step  sketch"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_generate_lean_sketch",
            problem=problem,
            useful_theorems_section=relevant_theorems,
            informal_proof=informal_proof,
        )
        response = self.llm.get_response(
            [
                {"role": "user", "content": user_prompt},
            ]
        )
        return self._extract_lean_code(response)

    def correct_sketch_error(
        self,
        problem: str,
        docstring: str,
        sketch: str,
        error_message: str,
        augmented_theorems: List[Dict[str, Any]],
    ):
        """纠正sketch错误"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_correct_sketch_error",
            sketch=sketch,
            error_message=error_message,
            augmented_theorems=augmented_theorems,
            problem=problem,
            docstring=docstring,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        return extract_lean_code(response)

    def compress_sketch(
        self,
        sketch: str,
        problem: str,
        docstring: str,
    ) -> str:
        """压缩和优化 sketch，移除冗余的 have 语句"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_compress_sketch",
            sketch=sketch,
            problem=problem,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        return self._extract_lean_code(response)

    # ------------------------------------------------------------------
    # extract subgoals
    # ------------------------------------------------------------------
    def extract_subgoals(self, sketch: str) -> List[str]:
        """从sketch提取subgoals

        Args:
            sketch: 证明草图（包含sorry的Lean代码）
            lean_hints: Lean提示信息

        Returns:
            List[str]: 提取出的子目标定理列表，每个元素是一个独立的Lean代码块
        """
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_subgoal_extract",
            proof_sketch=sketch,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        subgoals = self._parse_lean_code_blocks(response)
        logger.info(f"从sketch中提取了 {len(subgoals)} 个子目标")
        return subgoals

    def _parse_lean_code_blocks(self, response: str) -> List[str]:
        """从LLM响应中提取所有Lean代码块

        Args:
            response: LLM的响应文本

        Returns:
            List[str]: 提取出的Lean代码块列表
        """
        response = (response or "").strip()
        if not response:
            return []

        # 匹配 ```lean 或 ```lean4 代码块
        # ```lean4\n...\n``` 或 ```lean\n...\n```
        pattern = re.compile(r"```(?:lean4?)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(response)
        return matches

    def correct_theorem_error(
        self,
        subgoal: str,
        error_message: str,
    ):
        """纠正子目标错误"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_subgoal_syntax_correction",
            error_message=error_message,
            subgoal=subgoal,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        return self._extract_lean_code(response)

    # ------------------------------------------------------------------
    # use sketch and theorems assemble
    # ------------------------------------------------------------------
    def use_sketch_and_throrems(
        self,
        sketch,
        all_theorems,
    ):
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_use_sketch_and_throrems",
            sketch=sketch,
            all_theorems=all_theorems,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        return self._extract_lean_code(response)
        # pattern = re.compile(r"```(?:lean4?)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
        # matches = pattern.findall(response)
        # return matches[0]

    def assembly_correction(
        self,
        error_message,
        sketch_assembled,
    ):
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_assembly_correction",
            error_message=error_message,
            sketch_assembled=sketch_assembled,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        logger.info(f"assembly correction response: {response}")
        return self._extract_lean_code(response)

    # ------------------------------------------------------------------
    # subgoal
    # ------------------------------------------------------------------
    def check_mathematic_correctness(
        self,
        subgoal,
    ):
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_check_mathematical_correctness",  #
            problem=subgoal,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])

        # 解析响应文本
        # 1. 检查是否包含 YES 或 NO
        response_upper = response.upper()
        if "YES" in response_upper:
            correct = True
        elif "NO" in response_upper:
            correct = False
        else:
            # 如果没有明确的 YES/NO，默认认为不正确
            logger.warning(f"Could not find YES/NO in response: {response[:200]}")
            correct = False

        # 2. 提取 justification（从 <justification></justification> 标签中）
        justification_pattern = re.compile(r"<justification>(.*?)</justification>", re.DOTALL | re.IGNORECASE)
        justification_match = justification_pattern.search(response)
        if justification_match:
            justification = justification_match.group(1).strip()
        else:
            # 如果没有找到标签，尝试提取整个响应作为理由
            justification = response.strip()
            logger.warning("Could not find <justification> tags in response, using full response")

        return correct, justification

    def refine_sketch_based_error(
        self,
        sketch,
        error_justification,
    ):
        """
        修复子问题
        """
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_refine_sketch_based_error",
            sketch=sketch,
            error_message=error_justification,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        return self._extract_lean_code(response)

    # 直接用通用llm解决问题
    def attemp_reasoner_proof(
        self,
        subgoal,
        relevant_theorems,
    ):
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_general_llm_proof",
            problem=subgoal,  # prompt 中使用的是 problem
            lean_hints="",  # 暂时为空
            tactic_hints="",  # 暂时为空
            relevant_theorems=relevant_theorems,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        return self._extract_lean_code(response)

    def correct_proof_error(
        self,
        proof,
        error_message,
        augmented_theorems,
    ):
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_correct_proof_error",
            proof=proof,
            error_message=error_message,
            augmented_theorems=augmented_theorems,
        )
        response = self.llm.get_response([{"role": "user", "content": user_prompt}])
        return self._extract_lean_code(response)


def _normalize_lean_code(code: str) -> str:
    """规范化 Lean 代码：移除 import/open 语句和包装文本（模块级函数）

    Args:
        code: 原始 Lean 代码

    Returns:
        str: 规范化后的 Lean 代码
    """
    if not code:
        return ""

    lines = code.splitlines()
    cleaned_lines = []
    in_outer_namespace = False
    namespace_depth = 0

    for line in lines:
        stripped = line.strip()

        # 移除 import 语句（所有位置的 import）
        if stripped.startswith("import "):
            continue

        # 移除 open 语句（所有位置的 open）
        if stripped.startswith("open "):
            continue

        # 处理 namespace：只移除最外层的 namespace ... end 包装
        if stripped.startswith("namespace "):
            if namespace_depth == 0:
                # 最外层的 namespace，标记并跳过
                in_outer_namespace = True
                namespace_depth += 1
                continue
            else:
                # 嵌套的 namespace，保留
                namespace_depth += 1
                cleaned_lines.append(line)
                continue

        if stripped == "end":
            if in_outer_namespace and namespace_depth == 1:
                # 最外层的 end，移除
                in_outer_namespace = False
                namespace_depth = 0
                continue
            elif namespace_depth > 1:
                # 嵌套的 end，保留
                namespace_depth -= 1
                cleaned_lines.append(line)
                continue
            # 其他情况（不在 namespace 中的 end）保留

        # 保留所有其他行
        cleaned_lines.append(line)

    # 重新组合，去除首尾空行
    result = "\n".join(cleaned_lines).strip()

    # 确保以换行符结尾（如果代码不为空）
    if result:
        result = result.rstrip() + "\n"

    return result


def extract_lean_code(raw: str) -> str:
    """提取 Lean 代码（用于需要查找 theorem/lemma 等关键字的场景）

    先尝试用正则匹配代码块，如果失败则查找第一个 Lean 关键字并清理
    然后进行 normalize：移除 import/open 和包装文本
    """
    if not raw:
        return ""

    # 1. 先用正则匹配 ```lean 或 ```lean4 代码块
    pattern = re.compile(r"```(?:lean4?)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
    matches = pattern.findall(raw)
    if matches:
        code = matches[0]
    else:
        # 2. 如果正则匹配失败，查找第一个 Lean 关键字
        lines = raw.splitlines()
        start_idx = 0

        for i, line in enumerate(lines):
            s = line.lstrip()
            if (
                s.startswith("theorem ")
                or s.startswith("lemma ")
                or s.startswith("def ")
                or s.startswith("namespace ")
                or s.startswith("structure ")
            ):
                start_idx = i
                break

        code_lines = lines[start_idx:]

        # 3. 去掉可能出现的 ```lean / ``` 这类 fence
        cleaned = []
        for line in code_lines:
            s = line.strip()
            if s.startswith("```"):
                continue
            cleaned.append(line)

        code = "\n".join(cleaned)

    # 4. 规范化代码：移除 import/open 和包装文本
    return _normalize_lean_code(code)
