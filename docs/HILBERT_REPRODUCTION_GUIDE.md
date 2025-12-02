# HILBERT 论文完整复现指导文档

## 📚 论文信息

**论文标题**: Hilbert: Recursively Building Formal Proofs with Informal Reasoning  
**作者**: Varambally 等  
**年份**: 2025  
**arXiv**: https://arxiv.org/abs/2509.22819v1

## 🎯 核心架构概述

HILBERT 方法采用**五组件架构**，通过递归子目标分解来构建形式化证明：

```
┌─────────────┐
│ Coordinator │  ← 调度器：递归拆解子目标，组装完整证明
└──────┬──────┘
       │
       ├──→ Reasoner (通用 LLM)  ← 数学理解、非形式证明、proof sketch
       ├──→ Prover (Lean LLM)    ← 生成真正的 Lean 证明代码
       ├──→ Verifier (Lean4)     ← 严格验证证明
       └──→ Retriever            ← 语义检索有用定理
```

---

## 1️⃣ Reasoner（通用 LLM）

### 📋 功能职责

Reasoner 是系统的"大脑"，负责：

1. **数学理解**：理解问题的数学含义和结构
2. **非形式证明**：用自然语言描述证明思路
3. **生成 Proof Sketch**：生成包含 `have h : ... := by sorry` 的证明框架
4. **Shallow Solve**：尝试快速解决简单子目标

### 🔧 需要实现的功能

#### 1.1 数学理解模块

**输入**：
- 定理陈述（Lean4 格式）
- 问题描述（自然语言）

**输出**：
- 数学对象识别（集合、函数、关系等）
- 关键概念提取
- 问题类型分类（组合、几何、代数等）

**实现位置**: `src/agent/reasoner_agent.py`

**示例代码结构**:
```python
class ReasonerAgent(BaseAgent):
    def understand_problem(self, theorem_statement: str, description: str) -> Dict:
        """
        理解数学问题
        
        返回:
        {
            "objects": ["Set", "ncard", "convexHull"],
            "concepts": ["finite sets", "convex hull", "collinearity"],
            "problem_type": "combinatorial_geometry"
        }
        """
        prompt = f"""
        分析以下定理的数学结构：
        
        定理: {theorem_statement}
        描述: {description}
        
        请识别：
        1. 主要数学对象
        2. 关键概念
        3. 问题类型
        """
        # 调用 LLM
        return self.llm.get_response(messages)
```

#### 1.2 非形式证明生成

**输入**：
- 理解后的数学问题
- 定理陈述

**输出**：
- 自然语言证明思路
- 证明步骤大纲

**实现位置**: `src/agent/reasoner_agent.py`

**示例代码结构**:
```python
def generate_informal_proof(self, problem_understanding: Dict) -> str:
    """
    生成非形式证明
    
    返回自然语言描述的证明思路
    """
    prompt = f"""
    基于以下理解，用自然语言描述证明思路：
    
    问题理解: {problem_understanding}
    
    请提供：
    1. 证明的整体策略
    2. 关键步骤
    3. 需要使用的引理或定理
    """
    return self.llm.get_response(messages)
```

#### 1.3 Proof Sketch 生成

**这是 Reasoner 的核心功能**

**输入**：
- 非形式证明
- 定理陈述
- 当前证明状态（如果有）

**输出**：
- 包含 `have` 语句的证明框架
- 每个 `have` 使用 `by sorry` 占位

**关键格式**:
```lean
by
  have h1 : subgoal1 := by sorry
  have h2 : subgoal2 := by sorry
  -- 使用 h1 和 h2 完成主证明
  exact ...
```

**实现位置**: `src/agent/reasoner_agent.py`

**示例代码结构**:
```python
def generate_proof_sketch(
    self, 
    informal_proof: str, 
    theorem_statement: str,
    retrieved_lemmas: List[str] = None
) -> str:
    """
    生成 proof sketch
    
    返回包含 have ... := by sorry 的证明框架
    """
    lemmas_context = ""
    if retrieved_lemmas:
        lemmas_context = f"\n可能有用的引理:\n" + "\n".join(retrieved_lemmas)
    
    prompt = f"""
    基于以下非形式证明，生成 Lean4 proof sketch：
    
    非形式证明: {informal_proof}
    {lemmas_context}
    
    要求：
    1. 使用 have 语句分解子目标
    2. 每个 have 使用 'by sorry' 作为占位符
    3. 保持证明的逻辑结构
    4. 最后使用这些 have 完成主证明
    
    示例格式：
    ```lean
    by
      have h1 : subgoal1 := by sorry
      have h2 : subgoal2 := by sorry
      exact h1 h2
    ```
    """
    return self.llm.get_response(messages)
```

#### 1.4 Shallow Solve

**功能**：尝试快速解决简单的子目标

**输入**：
- 子目标（Lean4 格式）
- 可用引理

**输出**：
- 如果简单，直接返回证明
- 如果复杂，返回 None（交给 Prover）

**实现位置**: `src/agent/reasoner_agent.py`

**示例代码结构**:
```python
def shallow_solve(self, subgoal: str, context: Dict) -> Optional[str]:
    """
    尝试快速解决简单子目标
    
    返回: 证明代码或 None
    """
    prompt = f"""
    尝试快速解决以下子目标（如果很简单）：
    
    子目标: {subgoal}
    上下文: {context}
    
    如果可以通过简单的 tactic（如 simp, rfl, trivial）解决，返回证明。
    否则返回 "COMPLEX"。
    """
    response = self.llm.get_response(messages)
    if "COMPLEX" in response:
        return None
    return response
```

### 📝 完整 Reasoner 接口

```python
class ReasonerAgent(BaseAgent):
    def __init__(self, llm: BaseLLM):
        super().__init__(llm, "ReasonerAgent")
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        执行 Reasoner 的完整流程
        """
        # 1. 数学理解
        understanding = self.understand_problem(
            state.theorem_statement, 
            state.problem_description
        )
        
        # 2. 非形式证明
        informal_proof = self.generate_informal_proof(understanding)
        
        # 3. 生成 proof sketch（如果有检索到的引理）
        retrieved_lemmas = state.get("retrieved_lemmas", [])
        proof_sketch = self.generate_proof_sketch(
            informal_proof, 
            state.theorem_statement,
            retrieved_lemmas
        )
        
        # 4. 尝试 shallow solve（可选）
        # 这里可以尝试解决 proof sketch 中的简单子目标
        
        return {
            "understanding": understanding,
            "informal_proof": informal_proof,
            "proof_sketch": proof_sketch,
            "success": True
        }
```

---

## 2️⃣ Prover（Lean LLM）

### 📋 功能职责

Prover 负责将 proof sketch 中的 `sorry` 替换为真正的 Lean 证明代码。

### 🔧 需要实现的功能

#### 2.1 子目标证明生成

**输入**：
- Proof sketch 中的子目标（`have h : ... := by sorry`）
- 上下文（已证明的引理、假设等）
- 错误历史（如果之前失败过）

**输出**：
- 完整的 Lean 证明代码（替换 `by sorry`）

**实现位置**: `src/agent/prover_agent.py`

**示例代码结构**:
```python
class ProverAgent(BaseAgent):
    def __init__(self, llm: BaseLLM):
        super().__init__(llm, "ProverAgent")
    
    def prove_subgoal(
        self, 
        subgoal: str, 
        context: Dict,
        error_history: List[str] = None
    ) -> str:
        """
        证明单个子目标
        
        输入示例:
        subgoal = "have h1 : ∀ x, x ∈ S → x ∈ T := by sorry"
        """
        error_context = ""
        if error_history:
            error_context = f"\n之前的错误:\n" + "\n".join(error_history[-3:])
        
        prompt = f"""
        证明以下子目标：
        
        子目标: {subgoal}
        上下文: {context}
        {error_context}
        
        要求：
        1. 生成完整的 Lean 证明代码
        2. 不使用 sorry
        3. 可以使用上下文中的引理和假设
        """
        return self.llm.get_response(messages)
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        执行 Prover 流程
        
        从 proof sketch 中提取所有 sorry 子目标，逐个证明
        """
        proof_sketch = state.proof_sketch
        subgoals = self._extract_subgoals(proof_sketch)
        
        proved_subgoals = {}
        for subgoal_id, subgoal in subgoals.items():
            proof = self.prove_subgoal(
                subgoal, 
                state.context,
                state.error_history
            )
            proved_subgoals[subgoal_id] = proof
        
        # 组装完整证明
        complete_proof = self._assemble_proof(proof_sketch, proved_subgoals)
        
        return {
            "proof": complete_proof,
            "subgoals": proved_subgoals,
            "success": True
        }
    
    def _extract_subgoals(self, proof_sketch: str) -> Dict[str, str]:
        """
        从 proof sketch 中提取所有 have ... := by sorry
        """
        import re
        pattern = r'have\s+(\w+)\s*:\s*([^:]+):=\s*by\s+sorry'
        matches = re.finditer(pattern, proof_sketch, re.MULTILINE)
        
        subgoals = {}
        for i, match in enumerate(matches):
            var_name = match.group(1)
            goal_type = match.group(2).strip()
            subgoals[f"subgoal_{i}"] = f"have {var_name} : {goal_type} := by sorry"
        
        return subgoals
    
    def _assemble_proof(self, proof_sketch: str, proved_subgoals: Dict) -> str:
        """
        将证明好的子目标组装回完整证明
        """
        # 替换 proof sketch 中的 sorry 为实际证明
        result = proof_sketch
        for subgoal_id, proof in proved_subgoals.items():
            # 找到对应的 have 语句并替换
            result = result.replace("by sorry", proof, 1)
        return result
```

### 📝 关键实现细节

1. **子目标提取**：使用正则表达式提取所有 `have ... := by sorry`
2. **上下文管理**：维护已证明的引理和假设
3. **错误处理**：记录失败原因，用于下次尝试
4. **证明组装**：将证明好的子目标替换回原位置

---

## 3️⃣ Verifier（Lean4）

### 📋 功能职责

Verifier 使用 Lean4 编译器严格验证生成的证明。

### 🔧 现有实现

**实现位置**: `src/verifier/lean4_runner.py`

**主要功能**：
- ✅ 执行 Lean4 代码验证
- ✅ 解析错误信息
- ✅ 提取错误类型和位置
- ✅ 提取证明状态（goals, hypotheses）

### 🔧 需要增强的功能

#### 3.1 子目标验证

**功能**：验证单个子目标，而不是整个证明

**实现位置**: `src/verifier/lean4_runner.py`

**示例代码**:
```python
def verify_subgoal(self, subgoal_statement: str, context: str) -> Lean4Result:
    """
    验证单个子目标
    
    输入:
    - subgoal_statement: "have h : P := by ..."
    - context: 上下文代码（imports, 假设等）
    """
    full_code = f"""
    {context}
    
    {subgoal_statement}
    """
    return self.execute(full_code)
```

#### 3.2 提取未解决的子目标

**功能**：从错误信息中提取哪些子目标未解决

**实现位置**: `src/verifier/lean4_runner.py`

**示例代码**:
```python
def extract_unsolved_subgoals(self, error_text: str) -> List[str]:
    """
    从错误信息中提取未解决的子目标
    
    返回: 子目标列表
    """
    # 查找 "have h : ... := by sorry" 或未完成的证明
    pattern = r'have\s+(\w+)\s*:\s*([^:]+):=\s*by\s+sorry'
    unsolved = re.findall(pattern, error_text)
    return unsolved
```

---

## 4️⃣ Retriever（语义检索）

### 📋 功能职责

Retriever 从定理库中检索可能有用的定理和引理。

### 🔧 需要实现的功能

#### 4.1 定理库构建

**功能**：构建可搜索的定理库

**实现位置**: `src/retriever/theorem_db.py`

**示例代码结构**:
```python
class TheoremDB:
    def __init__(self, mathlib_path: str = None):
        """
        初始化定理库
        
        Args:
            mathlib_path: Mathlib 路径（可选）
        """
        self.theorems = []  # List of (name, statement, embedding)
        self.embeddings = None  # 向量数据库
    
    def build_index(self, theorem_files: List[str]):
        """
        构建定理索引
        
        从 Lean 文件中提取所有定理和引理
        """
        for file_path in theorem_files:
            theorems = self._extract_theorems(file_path)
            for theorem in theorems:
                self.theorems.append(theorem)
        
        # 生成 embeddings
        self._build_embeddings()
    
    def _extract_theorems(self, file_path: str) -> List[Dict]:
        """
        从 Lean 文件中提取定理
        
        返回: [{"name": "...", "statement": "...", "type": "theorem|lemma"}]
        """
        # 使用正则表达式或 AST 解析
        # 提取 theorem, lemma, def 等
        pass
    
    def _build_embeddings(self):
        """
        为所有定理生成向量嵌入
        """
        # 使用 sentence-transformers 或 OpenAI embeddings
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        statements = [t["statement"] for t in self.theorems]
        self.embeddings = model.encode(statements)
```

#### 4.2 语义检索

**功能**：基于查询检索相关定理

**实现位置**: `src/retriever/retriever_agent.py`

**示例代码结构**:
```python
class RetrieverAgent:
    def __init__(self, theorem_db: TheoremDB, llm: BaseLLM = None):
        self.theorem_db = theorem_db
        self.llm = llm  # 可选：用于查询重写
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        use_llm_rewrite: bool = False
    ) -> List[Dict]:
        """
        检索相关定理
        
        Args:
            query: 查询字符串（可以是自然语言或 Lean 代码）
            top_k: 返回前 k 个结果
            use_llm_rewrite: 是否使用 LLM 重写查询
        
        Returns:
            [{"name": "...", "statement": "...", "score": 0.9}]
        """
        # 可选：使用 LLM 重写查询
        if use_llm_rewrite and self.llm:
            query = self._rewrite_query(query)
        
        # 生成查询向量
        query_embedding = self._encode_query(query)
        
        # 计算相似度
        similarities = self._compute_similarities(query_embedding)
        
        # 返回 top_k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            results.append({
                **self.theorem_db.theorems[idx],
                "score": float(similarities[idx])
            })
        
        return results
    
    def _rewrite_query(self, query: str) -> str:
        """
        使用 LLM 将自然语言查询重写为更精确的数学描述
        """
        prompt = f"""
        将以下查询重写为更精确的数学描述：
        
        查询: {query}
        
        返回：数学概念和关键词
        """
        return self.llm.get_response(messages)
    
    def _encode_query(self, query: str) -> np.ndarray:
        """生成查询向量"""
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode([query])[0]
    
    def _compute_similarities(self, query_embedding: np.ndarray) -> np.ndarray:
        """计算余弦相似度"""
        import numpy as np
        similarities = np.dot(self.theorem_db.embeddings, query_embedding)
        return similarities
```

#### 4.3 集成到工作流

**在 Reasoner 中使用 Retriever**:

```python
# 在 ReasonerAgent 中
def execute(self, state: AgentState) -> Dict[str, Any]:
    # 1. 检索相关定理
    if hasattr(state, 'retriever'):
        retrieved = state.retriever.retrieve(
            query=state.theorem_statement,
            top_k=5
        )
        state.retrieved_lemmas = retrieved
    
    # 2. 生成 proof sketch（使用检索到的引理）
    proof_sketch = self.generate_proof_sketch(
        informal_proof,
        state.theorem_statement,
        retrieved_lemmas=state.retrieved_lemmas
    )
    
    # ...
```

### 📝 实现步骤

1. **安装依赖**:
```bash
pip install sentence-transformers numpy
```

2. **构建定理库**:
```python
from src.retriever.theorem_db import TheoremDB

db = TheoremDB()
db.build_index([
    "data/benchmarks/lean4/src/**/*.lean",
    # 或 Mathlib 路径
])
db.save("data/theorem_db.pkl")
```

3. **使用 Retriever**:
```python
from src.retriever.retriever_agent import RetrieverAgent

retriever = RetrieverAgent(db)
results = retriever.retrieve("convex hull of finite set", top_k=5)
```

---

## 5️⃣ Coordinator（调度器）

### 📋 功能职责

Coordinator 是系统的核心调度器，负责：

1. **递归拆解子目标**：将复杂证明分解为子目标
2. **调度各组件**：协调 Reasoner、Prover、Verifier、Retriever
3. **组装完整证明**：将所有子目标证明组装成完整证明
4. **错误处理和重试**：管理失败重试逻辑

### 🔧 需要实现的功能

#### 5.1 递归子目标分解

**核心算法**：

```
function solve(goal):
    if is_simple(goal):
        return shallow_solve(goal)
    
    sketch = reasoner.generate_sketch(goal)
    subgoals = extract_subgoals(sketch)
    
    proved_subgoals = {}
    for subgoal in subgoals:
        if subgoal not in proved_subgoals:
            proof = solve(subgoal)  // 递归！
            proved_subgoals[subgoal] = proof
    
    return assemble(sketch, proved_subgoals)
```

**实现位置**: `src/agent/coordinator.py`（需要大幅增强）

**示例代码结构**:
```python
class Coordinator:
    def __init__(
        self,
        reasoner: ReasonerAgent,
        prover: ProverAgent,
        verifier: VerificationAgent,
        retriever: RetrieverAgent = None
    ):
        self.reasoner = reasoner
        self.prover = prover
        self.verifier = verifier
        self.retriever = retriever
        
        # 子目标缓存
        self.subgoal_cache = {}
        # 最大递归深度
        self.max_depth = 10
    
    def solve(self, problem_description: str, task_template: str) -> Dict:
        """
        主求解函数
        """
        state = AgentState(
            problem_description=problem_description,
            task_template=task_template
        )
        
        # 提取主目标
        main_goal = self._extract_main_goal(task_template)
        
        # 递归求解
        proof = self._solve_recursive(main_goal, state, depth=0)
        
        if proof:
            # 组装完整证明
            full_proof = self._assemble_full_proof(task_template, proof)
            
            # 最终验证
            verification = self.verifier.execute(
                AgentState(current_proof=full_proof, task_template=task_template)
            )
            
            return {
                "success": verification.get("success", False),
                "proof": full_proof,
                "verification": verification
            }
        else:
            return {"success": False, "error": "Failed to solve"}
    
    def _solve_recursive(
        self, 
        goal: str, 
        state: AgentState, 
        depth: int
    ) -> Optional[str]:
        """
        递归求解子目标
        
        Args:
            goal: 要证明的目标（Lean 格式）
            state: 当前状态
            depth: 递归深度
        
        Returns:
            证明代码或 None
        """
        # 检查缓存
        goal_hash = self._hash_goal(goal)
        if goal_hash in self.subgoal_cache:
            return self.subgoal_cache[goal_hash]
        
        # 检查深度
        if depth >= self.max_depth:
            return None
        
        # 1. 检索相关引理
        if self.retriever:
            retrieved = self.retriever.retrieve(goal, top_k=5)
            state.retrieved_lemmas = retrieved
        
        # 2. Reasoner 生成 proof sketch
        reasoner_result = self.reasoner.execute(state)
        proof_sketch = reasoner_result.get("proof_sketch")
        
        if not proof_sketch:
            return None
        
        # 3. 提取子目标
        subgoals = self._extract_subgoals_from_sketch(proof_sketch)
        
        # 4. 递归求解每个子目标
        proved_subgoals = {}
        for subgoal_id, subgoal in subgoals.items():
            # 尝试 shallow solve
            shallow_proof = self.reasoner.shallow_solve(subgoal, state.context)
            
            if shallow_proof:
                proved_subgoals[subgoal_id] = shallow_proof
            else:
                # 递归求解
                subgoal_proof = self._solve_recursive(
                    subgoal, 
                    state, 
                    depth + 1
                )
                
                if subgoal_proof:
                    proved_subgoals[subgoal_id] = subgoal_proof
                else:
                    # 子目标求解失败，尝试 Prover
                    prover_result = self.prover.prove_subgoal(
                        subgoal,
                        state.context,
                        state.error_history
                    )
                    
                    # 验证子目标
                    verification = self.verifier.verify_subgoal(
                        f"have {subgoal_id} : {subgoal} := by {prover_result}",
                        state.context
                    )
                    
                    if verification.success:
                        proved_subgoals[subgoal_id] = prover_result
                    else:
                        # 记录错误，继续尝试
                        state.error_history.append(verification.error_message)
        
        # 5. 如果所有子目标都解决了，组装证明
        if len(proved_subgoals) == len(subgoals):
            assembled = self._assemble_from_sketch(proof_sketch, proved_subgoals)
            # 缓存结果
            self.subgoal_cache[goal_hash] = assembled
            return assembled
        
        return None
    
    def _extract_subgoals_from_sketch(self, proof_sketch: str) -> Dict[str, str]:
        """
        从 proof sketch 中提取子目标
        
        返回: {"subgoal_1": "have h1 : P := by sorry", ...}
        """
        import re
        pattern = r'have\s+(\w+)\s*:\s*([^:]+):=\s*by\s+sorry'
        matches = re.finditer(pattern, proof_sketch, re.MULTILINE)
        
        subgoals = {}
        for i, match in enumerate(matches):
            var_name = match.group(1)
            goal_type = match.group(2).strip()
            subgoals[f"subgoal_{i}"] = goal_type
        
        return subgoals
    
    def _assemble_from_sketch(
        self, 
        proof_sketch: str, 
        proved_subgoals: Dict[str, str]
    ) -> str:
        """
        将证明好的子目标组装回 proof sketch
        """
        result = proof_sketch
        subgoal_ids = list(proved_subgoals.keys())
        
        for subgoal_id, proof in proved_subgoals.items():
            # 替换对应的 sorry
            result = result.replace("by sorry", f"by {proof}", 1)
        
        return result
    
    def _hash_goal(self, goal: str) -> str:
        """生成目标的哈希值（用于缓存）"""
        import hashlib
        return hashlib.md5(goal.encode()).hexdigest()
```

#### 5.2 错误处理和重试

**功能**：管理失败重试逻辑

**实现位置**: `src/agent/coordinator.py`

**示例代码**:
```python
def _solve_with_retry(
    self, 
    goal: str, 
    state: AgentState, 
    max_retries: int = 3
) -> Optional[str]:
    """
    带重试的求解
    """
    for attempt in range(max_retries):
        try:
            proof = self._solve_recursive(goal, state, depth=0)
            if proof:
                return proof
        except Exception as e:
            state.error_history.append(str(e))
        
        # 等待后重试
        time.sleep(1)
    
    return None
```

---

## 🏗️ 完整实现步骤

### 步骤 1: 创建文件结构

```bash
mkdir -p src/agent/reasoner
mkdir -p src/agent/prover
mkdir -p src/retriever
touch src/agent/reasoner_agent.py
touch src/agent/prover_agent.py
touch src/retriever/theorem_db.py
touch src/retriever/retriever_agent.py
```

### 步骤 2: 实现 Reasoner

1. 创建 `src/agent/reasoner_agent.py`
2. 实现 `understand_problem()`
3. 实现 `generate_informal_proof()`
4. 实现 `generate_proof_sketch()`（核心）
5. 实现 `shallow_solve()`

### 步骤 3: 实现 Prover

1. 创建 `src/agent/prover_agent.py`
2. 实现 `prove_subgoal()`
3. 实现 `_extract_subgoals()`
4. 实现 `_assemble_proof()`

### 步骤 4: 增强 Verifier

1. 在 `src/verifier/lean4_runner.py` 中添加：
   - `verify_subgoal()`
   - `extract_unsolved_subgoals()`

### 步骤 5: 实现 Retriever

1. 安装依赖：`pip install sentence-transformers`
2. 创建 `src/retriever/theorem_db.py`
3. 实现定理库构建
4. 创建 `src/retriever/retriever_agent.py`
5. 实现语义检索

### 步骤 6: 增强 Coordinator

1. 修改 `src/agent/coordinator.py`
2. 实现递归子目标分解
3. 集成所有组件
4. 实现错误处理和重试

### 步骤 7: 更新配置

在 `config/default.yaml` 中添加：

```yaml
# Retriever 配置
retriever:
  enabled: true
  theorem_db_path: "data/theorem_db.pkl"
  top_k: 5
  use_llm_rewrite: false

# Coordinator 配置
coordinator:
  max_depth: 10
  max_retries: 3
  enable_caching: true
```

### 步骤 8: 测试

```python
from src.agent.coordinator import Coordinator
from src.agent.reasoner_agent import ReasonerAgent
from src.agent.prover_agent import ProverAgent
from src.agent.verification_agent import VerificationAgent
from src.retriever.retriever_agent import RetrieverAgent

# 初始化组件
reasoner = ReasonerAgent(llm_reasoner)
prover = ProverAgent(llm_prover)
verifier = VerificationAgent(lean_runner, llm_verifier)
retriever = RetrieverAgent(theorem_db)

# 创建 Coordinator
coordinator = Coordinator(
    reasoner=reasoner,
    prover=prover,
    verifier=verifier,
    retriever=retriever
)

# 求解
result = coordinator.solve(problem_description, task_template)
```

---

## 📊 工作流程图

```
开始
  │
  ├─→ Coordinator.solve()
  │     │
  │     ├─→ Retriever.retrieve()  ← 检索相关定理
  │     │
  │     ├─→ Reasoner.execute()
  │     │     ├─→ understand_problem()
  │     │     ├─→ generate_informal_proof()
  │     │     └─→ generate_proof_sketch()  ← 生成 have ... := by sorry
  │     │
  │     ├─→ 提取子目标
  │     │
  │     ├─→ 对每个子目标：
  │     │     ├─→ Reasoner.shallow_solve()  ← 尝试快速解决
  │     │     │     ├─→ 成功 → 使用结果
  │     │     │     └─→ 失败 → 继续
  │     │     │
  │     │     ├─→ Coordinator._solve_recursive()  ← 递归求解
  │     │     │     └─→ (重复上述流程)
  │     │     │
  │     │     ├─→ Prover.prove_subgoal()  ← 生成证明
  │     │     │
  │     │     └─→ Verifier.verify_subgoal()  ← 验证
  │     │           ├─→ 成功 → 缓存结果
  │     │           └─→ 失败 → 记录错误，重试
  │     │
  │     └─→ 组装完整证明
  │
  └─→ 返回结果
```

---

## 🔑 关键实现要点

### 1. Proof Sketch 格式

**正确格式**:
```lean
by
  have h1 : subgoal1 := by sorry
  have h2 : subgoal2 := by sorry
  -- 使用 h1, h2 完成证明
  exact h1 h2
```

**错误格式**:
```lean
by sorry  -- 太简单，没有分解
```

### 2. 递归终止条件

- 达到最大深度
- 子目标太简单（可用 shallow solve）
- 子目标已在缓存中

### 3. 错误处理策略

- 记录每次失败的错误信息
- 在下次尝试时传递给 LLM
- 限制重试次数

### 4. 性能优化

- **缓存**：已解决的子目标缓存起来
- **并行**：可以并行求解独立的子目标
- **提前终止**：如果主证明已失败，停止求解子目标

---

## 📝 测试用例

### 测试 1: 简单证明

```python
problem = """
Given a finite set S with 5 points, no 3 collinear.
Prove: ∃ T ⊆ S, |T| = 4, such that no point in T is in the convex hull of the others.
"""

result = coordinator.solve(problem, task_template)
assert result["success"] == True
```

### 测试 2: 递归子目标

```python
# 测试递归分解
sketch = """
by
  have h1 : subgoal1 := by sorry
  have h2 : subgoal2 := by sorry
  exact h1 h2
"""

# 应该能递归求解 h1 和 h2
```

### 测试 3: Retriever

```python
# 测试检索
results = retriever.retrieve("convex hull", top_k=5)
assert len(results) == 5
assert all("score" in r for r in results)
```

---

## 🐛 常见问题

### Q1: Proof sketch 生成失败

**原因**: LLM 没有遵循格式要求

**解决**: 
- 加强提示词
- 添加示例
- 使用更严格的输出解析

### Q2: 递归深度过深

**原因**: 子目标分解过于细致

**解决**:
- 设置合理的最大深度
- 合并简单子目标
- 使用 shallow solve 提前终止

### Q3: Retriever 检索不相关

**原因**: 查询向量不准确

**解决**:
- 使用 LLM 重写查询
- 调整相似度阈值
- 使用更好的 embedding 模型

---

## 📚 参考资料

- **Lean4 文档**: https://leanprover-community.github.io/
- **Mathlib**: https://github.com/leanprover-community/mathlib4
- **Sentence Transformers**: https://www.sbert.net/
- **论文**: https://arxiv.org/abs/2509.22819v1

---

## ✅ 实现检查清单

- [ ] Reasoner: 数学理解模块
- [ ] Reasoner: 非形式证明生成
- [ ] Reasoner: Proof sketch 生成（核心）
- [ ] Reasoner: Shallow solve
- [ ] Prover: 子目标证明生成
- [ ] Prover: 证明组装
- [ ] Verifier: 子目标验证（增强）
- [ ] Retriever: 定理库构建
- [ ] Retriever: 语义检索
- [ ] Coordinator: 递归子目标分解
- [ ] Coordinator: 组件协调
- [ ] Coordinator: 错误处理和重试
- [ ] 配置文件更新
- [ ] 单元测试
- [ ] 集成测试

---

**完成以上所有步骤后，您将拥有一个完整的 HILBERT 系统实现！** 🎉

