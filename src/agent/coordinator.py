import logging
from typing import Any, Dict, List, Optional, Union

from src.agent.base import AgentState
from src.agent.reasoner_agent import ReasonerAgent
from src.llm import LLMConfig
from src.llm.factory import LLMFactory

from ..llm.base import BaseLLM
from ..llm.config_loader import ConfigLoader
from ..utils.config_manager import ConfigManager
from ..verifier.lean4_runner import Lean4Runner
from .generation_agent import GenerationAgent
from .planning_agent import PlanningAgent
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
        # prover: Optional[ProverAgent] = None,
    ):
        self.reasoner = reasoner
        self.retriever = retriever
        self.verification = verification
        self.max_depth = 5
        self.sketch_attemps = 3
        self.sketch_correction_attemps = 3
        self.theorem_corrections = 5
        self.subgoal_corrections = 5
        self.head_theorems_sketch = 5

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
            valid, verified_subgoals, proved_subgoals, error_justification = self.validate_subgoals(
                subgoals, header, problem
            )
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
        logger.info(f"Corrected proof: {corrected_proof}")
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
            full_proof = header + "\n" + relevant_theorems + "\n" + corrected_proof
            verified, error_message = self.verification.execute(full_proof)
            logger.info(f"Verified: {verified}, Error message: {error_message}")
            if verified:
                return corrected_proof
        return None

    def refine_sketch_based_error(
        self,
        sketch,
        error_message,
    ):
        refined_sketch = self.reasoner.refine_sketch_based_error(sketch, error_message)
        return refined_sketch

    def validate_subgoals(self, subgoals, header, problem):
        verified_subgoals = []
        proved_subgoals = []
        for subgoal in subgoals:
            proof = self.attemp_proverllm_proof(subgoal, header)
            if proof is not None:
                proved_subgoals.append(proof)
            else:
                correct, justification = self.check_mathematic_correctness(subgoal, header)
                if correct:
                    proved_subgoals.append(subgoal)
                else:
                    return None, justification

        return proved_subgoals

    def check_mathematic_correctness(
        self,
        subgoal,
        relevant_theorems,
    ):
        correct, justification = self.reasoner.check_mathematic_correctness(subgoal, relevant_theorems)
        return correct, justification

    def attemp_proverllm_proof(
        self,
        probelm,
        header,
    ):
        for _ in range(self.sketch_attemps):
            proof = self.prover.prove_subgoal(probelm)
            verified, error_message = self.verification.execute(header + proof)
            if verified:
                return proof
        return None


class AgentCoordinator:
    """多智能体的协调器

    负责协调规划、生成、验证三个智能体的工作流
    """

    def __init__(
        self,
        planning_agent: Optional[PlanningAgent] = None,
        generation_agent: Optional[GenerationAgent] = None,
        verification_agent: Optional[VerificationAgent] = None,
        planning_llm: Optional[BaseLLM] = None,
        generation_llm: Optional[BaseLLM] = None,
        verification_llm: Optional[BaseLLM] = None,
        lean_runner: Optional[Lean4Runner] = None,
        max_retries: int = 5,
    ):
        # 1.创建默认的llm
        if planning_llm is None:
            planning_config = LLMConfig(model_name="o3-mini", temperature=0.7)
            planning_llm = LLMFactory.create_llm(planning_config)
        if generation_llm is None:
            generation_config = LLMConfig(model_name="gpt-4o", temperature=0.7)
            generation_llm = LLMFactory.create_llm(generation_config)
        if verification_llm is None:
            verification_config = LLMConfig(model_name="o3-mini", temperature=0.7)
            verification_llm = LLMFactory.create_llm(verification_config)
        self.max_retries = max_retries

        # 2.创建智能体
        if planning_agent is None:
            self.planning_agent = PlanningAgent(planning_llm)
            logger.info(f"规划智能体: {self.planning_agent}")
        if generation_agent is None:
            self.generation_agent = GenerationAgent(generation_llm)
            logger.info(f"生成智能体: {self.generation_agent}")
        if verification_agent is None:
            self.verification_agent = VerificationAgent(lean_runner, verification_llm)
            logger.info(f"验证智能体: {self.verification_agent}")

    @classmethod
    def from_config(
        cls,
        config_manager: Optional[Union[ConfigManager, str]] = None,
        config: Optional[Dict] = None,
    ) -> "AgentCoordinator":
        """
        从配置创建协调器

        Args:
            config_manager: ConfigManager 实例或配置文件路径（字符串）
            config: 可选的配置字典，用于覆盖配置文件中的设置
        Returns:
            AgentCoordinator: 协调器实例
        """
        # 1. 处理 config_manager 参数
        if config_manager is None:
            # 默认使用配置文件
            config_file = "config/default.yaml"
            config_manager = ConfigManager(config_file)
        elif isinstance(config_manager, str):
            # 如果是字符串，当作配置文件路径
            config_file = config_manager
            config_manager = ConfigManager(config_file)
        # 如果已经是 ConfigManager 实例，直接使用

        # 2. 从 ConfigManager 加载 LLM 配置
        try:
            planning_config_dict = config_manager.get_llm_config("planning")
            generation_config_dict = config_manager.get_llm_config("generation")
            verification_config_dict = config_manager.get_llm_config("verification")

            # 转换为 LLMConfig 对象
            planning_config = ConfigLoader.load_from_dict(planning_config_dict)
            generation_config = ConfigLoader.load_from_dict(generation_config_dict)
            verification_config = ConfigLoader.load_from_dict(verification_config_dict)
        except Exception as e:
            logger.warning(f"无法从配置文件加载，使用默认配置: {e}")
            planning_config = LLMConfig(model_name="gpt-4o-mini", temperature=0.7)
            generation_config = LLMConfig(model_name="gpt-4o", temperature=0.7)
            verification_config = LLMConfig(model_name="gpt-4o-mini", temperature=0.7)

        # 3. 使用 config 字典覆盖配置（如果提供）
        if config is not None:
            if "planning_model" in config:
                planning_config.model_name = config["planning_model"]
            if "planning_temperature" in config:
                planning_config.temperature = config["planning_temperature"]
            if "generation_model" in config:
                generation_config.model_name = config["generation_model"]
            if "generation_temperature" in config:
                generation_config.temperature = config["generation_temperature"]
            if "verification_model" in config:
                verification_config.model_name = config["verification_model"]
            if "verification_temperature" in config:
                verification_config.temperature = config["verification_temperature"]

        # 4. 创建 LLM 实例
        planning_llm = LLMFactory.create_llm(planning_config)
        generation_llm = LLMFactory.create_llm(generation_config)
        verification_llm = LLMFactory.create_llm(verification_config)
        lean_runner = Lean4Runner(
            project_path=config_manager.get_verifier_config().get("project_path"),
        )

        # 5. 获取 max_retries
        max_retries = config_manager.get_max_retries()

        return cls(
            planning_llm=planning_llm,
            generation_llm=generation_llm,
            verification_llm=verification_llm,
            lean_runner=lean_runner,
            max_retries=max_retries,
        )

    def solve(self, problem_description: str, task_template: str) -> Dict[str, str]:
        """
        解决问题的主流程
        """
        state = AgentState(
            problem_description=problem_description,
            task_template=task_template,
            max_retries=self.max_retries,
        )

        # 1. 规划阶段
        planning_result = self.planning_agent.execute(state)
        logger.info(f"规划阶段结果: {planning_result}")

        last_error: Optional[str] = None

        for attempt in range(state.max_retries):
            state.retry_count = attempt
            logger.info(f"===== 第 {attempt + 1}/{state.max_retries} 轮生成-验证 =====")

            # 2. 生成阶段
            generation_result = self.generation_agent.execute(state)
            logger.info(f"生成阶段结果: {generation_result}")

            # 3. 验证阶段
            verification_result = self.verification_agent.execute(state)
            logger.info(f"验证阶段结果: {verification_result}")

            if verification_result.get("success"):
                logger.info("✅ 证明验证通过，流程结束")
                return {
                    "success": True,
                    "proof": state.current_proof,
                    "verification_output": verification_result.get("output"),
                    "attempts": attempt + 1,
                }

            last_error = verification_result.get("error") or "Unknown verification error"
            logger.warning(f"❌ 第 {attempt + 1} 轮验证失败: {last_error}. 将错误反馈给生成阶段重试。")

        logger.error("🚫 达到最大重试次数仍未通过验证")
        return {
            "success": False,
            "proof": state.current_proof,
            "error": last_error,
            "attempts": state.max_retries,
        }
