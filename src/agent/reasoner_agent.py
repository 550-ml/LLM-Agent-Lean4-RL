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

    # ------------------------------------------------------------------
    # Theorem Retrieval
    # ------------------------------------------------------------------
    def generate_search_queries(
        self,
        problem: str,
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
        candidate_theorems: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """挑选相关定理"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_search_answer",
            problem=problem,
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
                {"role": "system", "content": "You are a Lean 4 expert who is trying to help write a proof in Lean 4."},
                {"role": "user", "content": user_prompt},
            ]
        )
        # 去掉response中的```lean4```和```lean```
        response = response.replace("```lean4", "").replace("```lean", "")
        response = response.replace("```", "")
        response = response.replace("```", "")
        return response

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
        pattern = re.compile(r"```(?:lean4?)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(response)
        return matches[0]

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
        return response
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
        response = response.replace("```lean4", "").replace("```lean", "")
        response = response.replace("```", "")
        response = response.replace("```", "")
        return response

    # ------------------------------------------------------------------
    # subgoal
    # ------------------------------------------------------------------
    def check_mathematic_correctness(
        self,
        subgoal,
    ):
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_check_mathematic_correctness",
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
        return self.llm.get_response([{"role": "user", "content": user_prompt}])

    def attemp_reasoner_proof(
        self,
        subgoal,
        relevant_theorems,
    ):
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_attemp_reasoner_proof",
            subgoal=subgoal,
            relevant_theorems=relevant_theorems,
        )
        return self.llm.get_response([{"role": "user", "content": user_prompt}])


def extract_lean_code(raw: str) -> str:
    lines = raw.splitlines()
    start_idx = 0

    # 1. 找到第一行 Lean 代码的起点
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

    # 2. 去掉可能出现的 ```lean / ``` 这类 fence
    cleaned = []
    for line in code_lines:
        s = line.strip()
        if s.startswith("```"):
            continue
        cleaned.append(line)

    # 3. 去掉末尾多余空行
    return "\n".join(cleaned).rstrip() + "\n"
