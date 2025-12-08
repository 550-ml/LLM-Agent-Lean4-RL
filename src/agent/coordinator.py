import logging
from typing import Any, Dict, List, Optional

from src.agent.reasoner_agent import ReasonerAgent

from .prover_agent import ProverAgent
from .retriever_agent import RetrieverAgent
from .verification_agent import VerificationAgent

logger = logging.getLogger(__name__)


class HilbertCoordinator:
    """整体框架协调器
    1. 直接解决用solver解决的问题
    2. 调用reason递归解决问题
    """

    def __init__(
        self,
        # 一般在benchmark推理的时候，都应该只建立一个LLM
        reasoner: Optional[ReasonerAgent] = None,
        retriever: Optional[RetrieverAgent] = None,
        verification: Optional[VerificationAgent] = None,
        prover: Optional[ProverAgent] = None,
    ):
        self.reasoner = reasoner
        self.retriever = retriever
        self.verification = verification
        self.prover = prover
        self.max_depth = 5
        self.sketch_attemps = 3
        self.sketch_correction_attemps = 3
        self.theorem_corrections = 5
        self.subgoal_corrections = 5
        self.head_theorems_sketch = 5
        self.prover_attemps = 3

    def generate_proof(
        self,
        problem: str,
        header: str,
        docstring: str,
    ) -> str:
        """对一个问题进行求解，不管是难还是简单

        Args:
            problem (str): 只有对应的theorem_statement
            header (str): header就是前面的import前文
        """
        # TODO: 调用ProveAgent进行求解
        # 2. 子问题拆分并且求解
        subgoals = self.subgoal_decomposition(problem, header, docstring)

    def subgoal_decomposition(self, problem: str, header: str, docstring: str, depth: int = 1):
        """子问题拆分并且求解"""
        if depth >= self.max_depth:
            return None
        for attempt in range(self.sketch_attemps):
            # 1. 检索相关mathlibs定理
            relevant_theorems = self.retrieve_theorems(problem)
            # 2. 生成证明sketch
            proof_sketch = self.generate_proof_sketch(
                problem,
                relevant_theorems,
                docstring,
            )
            # 3. refine_and_validate_sketch
            sketch_assembled, subgoals, proved_subgoals = self.refine_and_validate_sketch(
                proof_sketch, header, relevant_theorems, problem, docstring
            )
            # TODO sketch_assembled, subgoals, proved_subgoals ← REFINEANDVALIDATESKETCH(sketch, header, relevant_theorems) 进一步整理

    def solve_all_subgoals(self, subgoals, proved_subgoals, sketch_assembled, header, depth):
        pass

    # * 1. 检索相关mathlibs定理
    def retrieve_theorems(
        self,
        problem: str,
        error_message: Optional[str] = None,
    ):
        """检索相关mathlibs定理"""
        # 1. 生成检索查询
        search_queries = self.reasoner.generate_search_queries(problem, error_message)
        logger.info(f"Search queries: {search_queries}")
        # 2. 调用retriever检索相关mathlibs定理
        candidate_theorems = self.retriever.batch_retrieve(search_queries)
        logger.info(f"Candidate theorems: {candidate_theorems}")
        # 3. 挑选相关定理, <theorem>...</theorem>
        relevant_theorems = self.reasoner.select_relevant_theorems(problem, candidate_theorems)
        logger.info(f"relevant_theorems: {relevant_theorems}")
        return relevant_theorems

    # * 2. 生成证明sketch
    def generate_proof_sketch(
        self,
        problem: str,
        relevant_theorems: List[Dict[str, Any]],
        docstring: str,
    ) -> str:
        """生成证明sketch"""
        informal_proof = self.reasoner.generate_informal_proof(problem, relevant_theorems, docstring)  # 自然语言
        logger.info(f"Informal proof: {informal_proof}")
        proof_sketch = self.reasoner.generate_sketch(problem, relevant_theorems, informal_proof)  # 证明sketch
        logger.info(f"Proof sketch: {proof_sketch}")
        return proof_sketch

    # * 3. 修复并验证sketch
    def refine_and_validate_sketch(
        self,
        sketch: str,
        header: str,
        relevant_theorems: List[Dict[str, Any]],
        problem: str,
        docstring: str,
    ):
        """修复并验证sketch"""
        for attempt in range(self.sketch_correction_attemps):
            # 1. sketch 能完整过lean4
            sketch_syntactic = self.complete_and_correct_syntax_error(
                sketch, header, relevant_theorems, problem, docstring
            )
            logger.info(f"Sketch syntactic: {sketch_syntactic}")
            if sketch_syntactic is None:
                return None
            # 2. 提取要证明的子定理
            subgoals = self.extract_subgoals(sketch_syntactic, header)
            if subgoals is None:
                return None
            # 3.重新生成一个“结构清晰、引用子目标”的完整证明草稿
            sketch_assembled = self.assemble_proof_from_subgoals(sketch_syntactic, subgoals, header, problem)
            if sketch_assembled is None:
                return None
            # 4. 验证子定理
            valid, verified_subgoals, proved_subgoals, error_justification = self.validate_subgoals(subgoals, header)
            if valid:
                return sketch_assembled, verified_subgoals, proved_subgoals
            else:
                refined_sketch = self.refine_sketch_based_error(sketch, error_justification)
                if refined_sketch is not None:
                    return refined_sketch, verified_subgoals, proved_subgoals
                else:
                    return None, None, None

    # * 3.1 完成sketch并纠正语法错误
    def complete_and_correct_syntax_error(
        self,
        sketch: str,
        header: str,
        relevant_theorems: List[Dict[str, Any]],
        problem: str,
        docstring: str,
    ) -> str:
        """完成并纠正语法错误"""
        full_code = header + sketch
        logger.debug(f"Full code: {full_code}")
        verified, error_message = self.verification.execute(full_code)
        logger.info(f"Verified: {verified}, Error message: {error_message}")
        #  要返回
        if verified:
            return sketch
        for _ in range(self.theorem_corrections):
            augmented_theorems = self.augment_theorems(error_message, relevant_theorems, problem=problem)
            logger.info(f"Augmented theorems: {augmented_theorems}")
            sketch = self.reasoner.correct_sketch_error(problem, docstring, sketch, error_message, augmented_theorems)
            logger.info(f"Corrected sketch: {sketch}")
            code = header + "\n" + sketch
            verified, error_message = self.verification.execute(code)
            logger.debug(f"Code: {code}")
            logger.info(f"Verified: {verified}, Error message: {error_message}")
            if verified:
                return sketch
        return None

    # * 3.1.1
    def augment_theorems(
        self,
        error_message: str,
        existing_theorems: List[Dict[str, Any]],
        problem: str,
    ):
        """根据错误信息增强已有的定理"""
        # 从错误信息中提取缺失的标识符（如 "unknown identifier 'convexHull'"）
        missing_ids = self._extract_missing_identifiers(error_message)
        logger.info(f"Missing identifiers: {missing_ids}")

        # 基于错误信息检索额外的定理
        if missing_ids:
            additional_theorems = self.retrieve_theorems(problem, error_message)
            logger.info(f"Additional theorems: {additional_theorems}")
            return existing_theorems + additional_theorems
        return existing_theorems

    def _extract_missing_identifiers(self, error_message: str) -> List[str]:
        """从错误信息中提取缺失的标识符

        示例错误信息:
        - "unknown identifier 'convexHull'"
        - "unknown constant 'Finset.card_eq'"
        """
        import re

        pattern = re.compile(
            r"(?:unknown identifier|unknown constant)\s+'?([\w\.]+)'?",
            re.IGNORECASE,
        )
        return pattern.findall(error_message or "")

    # * 3.2 提取子目标
    def extract_subgoals(self, sketch: str, header: str) -> List[str]:
        subgoals = self.reasoner.extract_subgoals(sketch)
        logger.info(f"Subgoals: {subgoals}")
        correct_subgoals = []
        for subgoal in subgoals:
            logger.info(f"Subgoal: {subgoal}")
            verified, error_message = self.verification.execute(header + "\n" + subgoal)
            logger.info(f"Verified: {verified}, Error message: {error_message}")
            if verified:
                correct_subgoals.append(subgoal)
            else:
                corrected = False
                for _ in range(self.subgoal_corrections):
                    correct_subgoal = self.reasoner.correct_theorem_error(subgoal, error_message)
                    logger.info(f"Corrected subgoal: {correct_subgoal}")
                    verified, error_message = self.verification.execute(header + "\n" + correct_subgoal)
                    logger.info(f"Verified: {verified}, Error message: {error_message}")
                    if verified:
                        correct_subgoals.append(correct_subgoal)
                        corrected = True
                        break
                if not corrected:
                    return None
        return correct_subgoals

    # * 3.3 重新组装sketch
    def assemble_proof_from_subgoals(self, sketch, subgoals, header, problem):
        # all_theorems = self.concate_theorems(subgoals)
        sketch_assembeld = self.reasoner.use_sketch_and_throrems(sketch, subgoals)
        logger.info(f"Sketch assembled: {sketch_assembeld}")
        corrected_proof = self.verify_and_correct_proof_with_theorems(sketch_assembeld, header, subgoals, problem)
        logger.info(f"assembled proof: {corrected_proof}")
        return corrected_proof

    def verify_and_correct_proof_with_theorems(
        self,
        sketch_assembled,
        header,
        relevant_theorems,
        problem,
    ):
        theorems_block = "\n\n".join(relevant_theorems)
        full_proof = header + "\n" + theorems_block + "\n" + sketch_assembled
        verified, error_message = self.verification.execute(full_proof)
        logger.info(f"Verified: {verified}, Error message: {error_message}")
        if verified:
            return sketch_assembled
        for _ in range(self.head_theorems_sketch):
            corrected_proof = self.reasoner.assembly_correction(error_message, sketch_assembled)
            logger.info(f"Corrected proof: {corrected_proof}")
            full_proof = header + "\n" + theorems_block + "\n" + corrected_proof
            verified, error_message = self.verification.execute(full_proof)
            logger.info(f"Verified: {verified}, Error message: {error_message}")
            if verified:
                return corrected_proof
        return None

    # * 3.4 证明子定理
    def validate_subgoals(self, subgoals, header):
        verified_subgoals = []
        proved_subgoals = {}
        for subgoal in subgoals:
            proof = self.attemp_proverllm_proof(subgoal, header)
            if proof is not None:
                verified_subgoals.append(proof)
                proved_subgoals[subgoal] = proof
            else:
                correct, justification = self.check_mathematic_correctness(subgoal)
                if correct:
                    verified_subgoals.append(subgoal)
                else:
                    return False, None, None, justification
        return True, verified_subgoals, proved_subgoals, None

    def attemp_proverllm_proof(
        self,
        probelm,
        header,
    ):
        if self.prover is None:
            logger.warning("ProverAgent is not initialized, skipping prover proof attempt")
            return None

        for _ in range(self.prover_attemps):
            proof = self.prover.prove_subgoal(probelm, header)
            if not proof:
                continue
            verified, error_message = self.verification.execute(header + "\n" + proof)
            if verified:
                return proof
        return None

    def check_mathematic_correctness(
        self,
        subgoal,
    ):
        correct, justification = self.reasoner.check_mathematic_correctness(subgoal)
        return correct, justification

    def refine_sketch_based_error(
        self,
        sketch,
        error_message,
    ):
        "sketch修复"
        refined_sketch = self.reasoner.refine_sketch_based_error(sketch, error_message)
        return refined_sketch
