import json
import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from ..llm.base import BaseLLM
from ..utils.prompt_loader import PromptLoader
from ..verifier.lean4_runner import Lean4Result, Lean4Runner
from .base import AgentState, BaseAgent

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
        )
        response = self.llm.get_response(
            [
                {"role": "user", "content": user_prompt},
            ]
        )
        queries = self._parse_string_list(response)
        logger.info(f"生成检索查询: {queries}")
        return queries

    def select_relevant_theorems(
        self,
        problem,
        candidate_theorems: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """挑选相关定理"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_select_relevant_theorems",
            problem=problem,
            theorems=candidate_theorems,
        )
        response = self.llm.get_response(
            [
                {"role": "user", "content": user_prompt},
            ]
        )
        return response

    def generate_informal_proof(
        self,
        problem,
        relevant_theorems: List[Dict[str, Any]],
    ) -> str:
        """生成非形式证明"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_generate_informal_proof",
            problem=problem,
            useful_theorems_section=relevant_theorems,
        )
        return self.llm.get_response(user_prompt)

    def generate_sketch(self, problem: str, relevant_theorems: List[Dict[str, Any]], informal_proof: str) -> str:
        """生成证明带有step  sketch"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_create_lean_sketch",
            problem=problem,
            useful_theorems_section=relevant_theorems,
            informal_proof=informal_proof,
        )  # TODO lean hint
        return self.llm.get_response(user_prompt)

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


class ReasonerAgent2(BaseAgent):
    """Reasoner 负责数学理解、检索与 proof sketch 的上游逻辑。"""

    def __init__(
        self,
        llm: BaseLLM,
        *,
        prompt_loader: Optional[PromptLoader] = None,
        lean_runner: Optional[Lean4Runner] = None,
        retriever: Optional[Any] = None,
        retrieval_enabled: bool = True,
        max_queries: int = 3,
        top_k: int = 5,
    ):
        super().__init__(llm, "ReasonerAgent")
        self.prompt_loader = prompt_loader or PromptLoader()
        self.lean_runner = lean_runner
        self.retriever = retriever
        self.retrieval_enabled = retrieval_enabled
        self.max_queries = max_queries
        self.top_k = top_k
        try:
            self.system_prompt = self.prompt_loader.load_system_prompt("reasoner")
        except FileNotFoundError:
            self.system_prompt = "你是一名专业的数学推理智能体。"
            logger.warning("reasoner system prompt 未找到，已使用默认提示。")

    # ------------------------------------------------------------------
    # 生命周期 / 依赖注入
    # ------------------------------------------------------------------
    def set_retriever(self, retriever: Any) -> None:
        self.retriever = retriever

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """主执行流程（将在后续任务中补充）。"""
        raise NotImplementedError("ReasonerAgent.execute 尚未实现。")

    # ------------------------------------------------------------------
    # Theorem Retrieval
    # ------------------------------------------------------------------
    def retrieve_theorems(
        self,
        problem: str,
        error_message: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """实现伪代码 RETRIEVETHEOREMS。"""
        if not self.retrieval_enabled:
            logger.debug("检索关闭，返回空列表。")
            return []

        queries = self.generate_search_queries(problem, error_message)
        if not queries:
            return []

        candidates = self._semantic_search_engine(queries)
        if not candidates:
            logger.info("语义检索未返回候选定理。")
            return []

        return self.select_relevant_theorems(candidates, problem)

    def generate_search_queries(
        self,
        problem: str,
        error_message: Optional[str] = None,
    ) -> List[str]:
        """实现伪代码 GENERATESEARCHQUERIES。"""
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_search_query",
            problem=problem.strip(),
            error_message=(error_message or "无错误上下文").strip(),
            max_queries=self.max_queries,
        )
        response = self.llm.get_response(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        queries = self._parse_string_list(response)
        logger.debug("生成检索查询: %s", queries)
        return queries[: self.max_queries]

    def select_relevant_theorems(
        self,
        candidate_theorems: Sequence[Dict[str, Any]],
        problem: str,
        *,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """实现伪代码 SELECTRELEVANTTHEOREMS。"""
        if not candidate_theorems:
            return []

        max_results = max_results or self.top_k
        candidates_block = self._format_candidates_for_prompt(candidate_theorems)
        user_prompt = self.prompt_loader.load_and_format(
            "user",
            "reasoner_search_select",
            problem=problem.strip(),
            candidates=candidates_block,
            max_results=max_results,
        )
        response = self.llm.get_response(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        selected_ids = self._parse_int_list(response)
        selected: List[Dict[str, Any]] = []
        for idx in selected_ids:
            if 1 <= idx <= len(candidate_theorems):
                selected.append(candidate_theorems[idx - 1])
        if not selected:
            selected = list(candidate_theorems[:max_results])
        logger.debug("筛选后定理数量: %d", len(selected))
        return selected

    # ------------------------------------------------------------------
    # Lean Verification
    # ------------------------------------------------------------------
    def verify_proof(self, full_proof: str) -> Lean4Result:
        """实现伪代码 VERIFYPROOF。"""
        if not self.lean_runner:
            raise RuntimeError("Lean4Runner 未配置，无法验证证明。")
        return self.lean_runner.execute(full_proof)

    # ------------------------------------------------------------------
    # Error-driven augmentation
    # ------------------------------------------------------------------
    def augment_theorems(
        self,
        problem: str,
        existing_theorems: Optional[List[Dict[str, Any]]],
        error_message: Optional[str],
    ) -> List[Dict[str, Any]]:
        """实现伪代码 AUGMENTTHEOREMS。"""
        existing_theorems = existing_theorems or []
        if not error_message:
            return existing_theorems

        missing_ids = self._extract_missing_identifiers(error_message)
        if not missing_ids:
            return existing_theorems

        additional = self.retrieve_theorems(problem, error_message)
        combined = self._deduplicate_theorems(existing_theorems + additional)
        logger.debug(
            "根据错误补充定理：缺失 %s，新增 %d 条，总计 %d 条。",
            ",".join(sorted(missing_ids)) or "-",
            len(additional),
            len(combined),
        )
        return combined

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _semantic_search_engine(self, queries: Sequence[str]) -> List[Dict[str, Any]]:
        if not self.retriever:
            logger.warning("未配置 Retriever，语义检索返回空。")
            return []

        results: List[Dict[str, Any]] = []
        seen = set()
        for query in queries:
            try:
                retrieved = self.retriever.retrieve(query, top_k=self.top_k) or []
            except Exception as exc:  # noqa: BLE001
                logger.error("Retriever 调用失败: %s", exc)
                continue
            for item in retrieved:
                key = item.get("name") or item.get("statement") or str(item)
                if key in seen:
                    continue
                seen.add(key)
                results.append(item)
        return results

    def _format_candidates_for_prompt(self, candidate_theorems: Sequence[Dict[str, Any]]) -> str:
        lines = []
        for idx, theorem in enumerate(candidate_theorems, start=1):
            name = theorem.get("name") or f"Theorem_{idx}"
            statement = theorem.get("statement") or theorem.get("text", "")
            score = theorem.get("score")
            header = f"[{idx}] {name}"
            if score is not None:
                header += f" (score={score:.3f})" if isinstance(score, (int, float)) else f" (score={score})"
            lines.append(f"{header}\n{statement}".strip())
        return "\n\n".join(lines)

    def _parse_string_list(self, response: str) -> List[str]:
        response = (response or "").strip()
        if not response:
            return []
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            pass
        cleaned: List[str] = []
        for line in response.splitlines():
            candidate = line.strip("-• \t")
            if candidate:
                cleaned.append(candidate)
        return cleaned

    def _parse_int_list(self, response: str) -> List[int]:
        response = (response or "").strip()
        if not response:
            return []
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return [int(item) for item in data if isinstance(item, (int, float))]
        except json.JSONDecodeError:
            pass
        numbers = re.findall(r"\d+", response)
        return [int(num) for num in numbers]

    def _extract_missing_identifiers(self, error_message: str) -> List[str]:
        pattern = re.compile(
            r"(?:unknown identifier|unknown constant)\s+'?([\w\.]+)'?",
            re.IGNORECASE,
        )
        return pattern.findall(error_message or "")

    def _deduplicate_theorems(self, theorems: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique: List[Dict[str, Any]] = []
        seen = set()
        for theorem in theorems:
            key = theorem.get("name") or theorem.get("statement") or str(theorem)
            if key in seen:
                continue
            seen.add(key)
            unique.append(theorem)
        return unique
