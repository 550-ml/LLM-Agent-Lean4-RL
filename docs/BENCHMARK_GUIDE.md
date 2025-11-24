# PutnamBench 数据集结构详解

## 📁 目录结构

```
data/benchmarks/lean4/
├── README.md                    # 数据集说明
├── LICENSE                      # 许可证
├── lakefile.lean               # Lean4 项目配置文件
├── lean-toolchain              # Lean4 版本（v4.22.0）
├── lake-manifest.json          # Lake 依赖清单
├── check_docstrings.lean       # 检查 docstring 的工具
├── src/                        # 源代码目录（核心数据）
│   ├── putnam_1962_a1.lean
│   ├── putnam_1962_a2.lean
│   ├── ...
│   └── putnam_2002_*.lean     # 约 500+ 个问题文件
└── scripts/                     # 工具脚本
    ├── extract_to_json.py      # 提取数据为 JSON
    ├── generate_files_by_year.py  # 按年份生成文件
    └── rewrite_solutions.py     # 将答案内联到问题中
```

## 📊 数据集规模

- **总文件数**: 约 500+ 个 `.lean` 文件
- **总代码行数**: 约 10,662 行
- **时间跨度**: 1962 年 - 2002 年（40 年的 Putnam 竞赛题目）
- **问题类型**: A 组和 B 组题目（每年 6 道 A 题 + 6 道 B 题）

## 📝 文件命名规则

```
putnam_YYYY_XN.lean
```

- `YYYY`: 年份（1962-2002）
- `X`: 题目组（`a` 或 `b`）
- `N`: 题目编号（1-6）

**示例**:
- `putnam_1962_a1.lean` → 1962 年 A 组第 1 题
- `putnam_1965_b3.lean` → 1965 年 B 组第 3 题
- `putnam_2000_a6.lean` → 2000 年 A 组第 6 题

## 📄 文件内容结构

每个 `.lean` 文件包含一个完整的定理，格式如下：

### 标准格式

```lean
import Mathlib

open MeasureTheory  -- 可选：打开命名空间

-- 可选：定义答案（用于某些问题）
abbrev putnam_XXXX_XX_solution : Type := sorry
-- 答案的注释（实际答案）

/--
问题描述（LaTeX 格式）
-/
theorem putnam_XXXX_XX
  (参数声明)
  (假设条件)
  : 结论 :=
  sorry  -- 需要证明的部分
```

### 示例 1: 简单几何问题

```lean
import Mathlib

open MeasureTheory

/--
Given five points in a plane, no three of which lie on a straight line, 
show that some four of these points form the vertices of a convex quadrilateral.
-/
theorem putnam_1962_a1
(S : Set (ℝ × ℝ))
(hS : S.ncard = 5)
(hnoncol : ∀ s ⊆ S, s.ncard = 3 → ¬Collinear ℝ s)
: ∃ T ⊆ S, T.ncard = 4 ∧ ¬∃ t ∈ T, t ∈ convexHull ℝ (T \ {t}) :=
sorry
```

**解析**:
- **Docstring**: 问题描述（自然语言 + LaTeX）
- **定理名称**: `putnam_1962_a1`
- **参数**: `S` 是平面上的点集
- **假设**: 
  - `hS`: 集合有 5 个点
  - `hnoncol`: 任意 3 个点不共线
- **结论**: 存在 4 个点构成凸四边形
- **证明**: `sorry`（需要填充）

### 示例 2: 带答案定义的问题

```lean
import Mathlib

open MeasureTheory Set

abbrev putnam_1962_a2_solution : Set (ℝ → ℝ) := sorry
-- {f : ℝ → ℝ | ∃ a c : ℝ, a ≥ 0 ∧ f = fun x ↦ a / (1 - c * x) ^ 2}

/--
Find every real-valued function $f$ whose domain is an interval $I$ 
(finite or infinite) having 0 as a left-hand endpoint, such that for every 
positive member $x$ of $I$ the average of $f$ over the closed interval 
$[0, x]$ is equal to the geometric mean of the numbers $f(0)$ and $f(x)$.
-/
theorem putnam_1962_a2
    (P : Set ℝ → (ℝ → ℝ) → Prop)
    (P_def : ∀ s f, P s f ↔ 0 ≤ f ∧ ∀ x ∈ s, ⨍ t in Ico 0 x, f t = √(f 0 * f x)) :
    (∀ f,
      (P (Ioi 0) f → ∃ g ∈ putnam_1962_a2_solution, EqOn f g (Ici 0)) ∧
      (∀ e > 0, P (Ioo 0 e) f → ∃ g ∈ putnam_1962_a2_solution, EqOn f g (Ico 0 e))) ∧
    ∀ f ∈ putnam_1962_a2_solution, P (Ioi 0) f ∨ (∃ e > 0, P (Ioo 0 e) f) :=
  sorry
```

**特点**:
- 有 `abbrev` 定义答案类型
- 答案在注释中给出（`-- {f : ℝ → ℝ | ...}`）
- 定理需要证明答案的正确性

### 示例 3: 几何计算问题

```lean
import Mathlib

open EuclideanGeometry Real

noncomputable abbrev putnam_1965_a1_solution : ℝ := sorry
-- Real.pi / 15

/--
Let $\triangle ABC$ satisfy $\angle CAB < \angle BCA < \frac{\pi}{2} < \angle ABC$. 
If the bisector of the external angle at $A$ meets line $BC$ at $P$, the bisector 
of the external angle at $B$ meets line $CA$ at $Q$, and $AP = BQ = AB$, 
find $\angle CAB$.
-/
theorem putnam_1965_a1
(A B C X Y : EuclideanSpace ℝ (Fin 2))
(hABC : ¬Collinear ℝ {A, B, C})
(hangles : ∠ C A B < ∠ B C A ∧ ∠ B C A < π/2 ∧ π/2 < ∠ A B C)
(hX : Collinear ℝ {X, B, C} ∧ ∠ X A B = (π - ∠ C A B)/2 ∧ dist A X = dist A B)
(hY : Collinear ℝ {Y, C, A} ∧ ∠ Y B C = (π - ∠ A B C)/2 ∧ dist B Y = dist A B)
: ∠ C A B = putnam_1965_a1_solution :=
sorry
```

**特点**:
- 使用 `EuclideanGeometry` 命名空间
- `noncomputable` 标记（涉及实数计算）
- 答案是一个数值（`Real.pi / 15`）

## 🔍 数据特点分析

### 1. **问题类型多样性**

- **几何问题**: 平面几何、立体几何、欧几里得几何
- **代数问题**: 函数、方程、不等式
- **数论问题**: 整数性质、同余
- **组合问题**: 计数、图论
- **分析问题**: 微积分、级数、极限

### 2. **形式化程度**

- ✅ **完全形式化**: 所有概念都用 Lean4 类型系统表达
- ✅ **使用 Mathlib**: 依赖 Mathlib 库的丰富定义
- ✅ **类型安全**: 所有证明都在类型系统内完成

### 3. **证明难度**

- **简单**: 直接应用定理（少数）
- **中等**: 需要组合多个引理
- **困难**: 需要创造性构造和复杂推理（多数）

### 4. **Docstring 格式**

- 使用 LaTeX 数学公式（`$...$` 或 `$$...$$`）
- 包含完整的自然语言描述
- 可能包含图表描述（用文字）

## 🆚 与参考项目的区别

### 参考项目（Lean4-LLM-Ai-Agent-Mooc）

```
task_id_0/
├── description.txt          # 纯文本描述
├── task.lean                # 带占位符的模板
│   ├── {{code}}            # 代码占位符
│   └── {{proof}}           # 证明占位符
├── signature.json          # 函数签名（JSON）
├── test.json              # 测试用例（JSON）
└── tests.lean              # Lean4 测试
```

**特点**:
- 结构化数据（JSON）
- 明确的占位符
- 包含测试用例
- 问题相对简单（教学性质）

### PutnamBench（你的数据）

```
putnam_1962_a1.lean
├── import Mathlib
├── /-- 问题描述 -/          # Docstring（LaTeX）
└── theorem ... := sorry     # 完整定理，sorry 需要替换
```

**特点**:
- 单一文件格式
- 问题描述在 docstring 中
- 没有明确的占位符标记
- 问题更复杂（竞赛级别）
- 需要从定理中提取信息

## 🛠️ 数据处理流程

### 1. 加载阶段

```python
loader = PutnamLoader("data/benchmarks/lean4")
problem = loader.load_file("putnam_1962_a1.lean")
```

**提取内容**:
- ✅ Imports（`import Mathlib`）
- ✅ Opens（`open MeasureTheory`）
- ✅ Docstring（问题描述）
- ✅ 定理名称
- ✅ 完整定理语句

### 2. 转换阶段

```python
description, template = loader.convert_to_task_format(problem)
```

**转换操作**:
- 将 `sorry` 替换为 `{{proof}}` 占位符
- 保留 imports 和 opens
- 提取 docstring 作为问题描述
- 生成任务模板

### 3. Agent 处理阶段

```python
coordinator = AgentCoordinator.from_config()
result = coordinator.solve(description, template)
```

**Agent 工作**:
1. **规划**: 分析问题，制定策略
2. **生成**: 生成证明步骤
3. **验证**: 执行 Lean4 验证

### 4. 输出阶段

```python
# 替换 sorry 为生成的证明
full_theorem = problem.theorem_statement.replace('sorry', result['proof'])
```

## 📈 数据集统计

根据文件列表分析：

- **年份分布**: 1962-2002（40 年）
- **每年题目数**: 约 12 题（6 A + 6 B）
- **总题目数**: 约 480 题（部分年份可能缺失某些题目）
- **文件大小**: 每个文件 10-50 行不等
- **复杂度**: 从简单计算到复杂证明

## 🎯 使用建议

### 1. **选择合适的问题**

- **初学者**: 选择早期年份（1962-1970）的 A 组题目
- **进阶**: 选择中期年份（1970-1990）的题目
- **高级**: 选择后期年份（1990-2002）的 B 组题目

### 2. **理解问题结构**

- 先看 docstring 理解自然语言描述
- 再看定理类型签名理解形式化要求
- 最后看假设条件理解约束

### 3. **利用 Mathlib**

- 问题都依赖 Mathlib
- 可以搜索 Mathlib 文档找到相关定理
- 使用 `#check` 和 `#print` 探索类型

### 4. **调试策略**

- 先验证语法（`lake lean`）
- 再验证类型（检查类型错误）
- 最后验证证明（检查逻辑错误）

## 📚 相关资源

- **Mathlib 文档**: https://leanprover-community.github.io/mathlib4_docs/
- **Lean4 教程**: https://leanprover.github.io/lean4/doc/
- **Putnam 竞赛**: https://www.maa.org/math-competitions/putnam-competition

---

**总结**: PutnamBench 是一个高质量的数学竞赛问题数据集，完全形式化在 Lean4 中。每个问题都是一个完整的定理，需要生成证明来替换 `sorry`。这与参考项目的教学性质不同，更适合研究级别的形式化证明生成。

