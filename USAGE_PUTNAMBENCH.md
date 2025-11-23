# PutnamBench 数据格式使用指南

## 数据格式说明

PutnamBench 的数据格式与参考项目（Lean4-LLM-Ai-Agent-Mooc）不同：

### 参考项目格式
- 每个任务是一个文件夹（如 `task_id_0/`）
- 包含 `description.txt`、`task.lean`（带占位符）、`signature.json` 等

### PutnamBench 格式
- 直接是 `.lean` 文件
- 每个文件包含一个定理，证明是 `sorry`
- 问题描述在 docstring（`/-- ... -/`）中

## 使用方法

### 1. 列出所有可用问题

```bash
python src/main_putnam.py --list
```

### 2. 处理单个问题

```bash
python src/main_putnam.py --file putnam_1962_a1.lean
```

### 3. 指定数据目录

```bash
python src/main_putnam.py \
  --benchmarks-dir data/benchmarks/lean4 \
  --file putnam_1962_a1.lean
```

### 4. 在代码中使用

```python
from src.utils.putnam_loader import PutnamLoader
from src.agent.coordinator import AgentCoordinator

# 创建加载器
loader = PutnamLoader("data/benchmarks/lean4")

# 加载问题
problem = loader.load_file("putnam_1962_a1.lean")

# 转换为任务格式
description, template = loader.convert_to_task_format(problem)

# 创建协调器并解决问题
coordinator = AgentCoordinator.from_config()
result = coordinator.solve(description, template)

print(result["proof"])
```

## 数据转换流程

1. **加载 .lean 文件** → 提取定理、docstring、imports 等
2. **转换为任务格式** → 生成 `description` 和 `task_template`
3. **Agent 处理** → 规划 → 生成 → 验证
4. **输出结果** → 替换 `sorry` 为生成的证明

## 测试加载器

```bash
python test_putnam_loader.py
```

这会测试：
- 列出所有问题文件
- 加载单个文件
- 解析定理和描述
- 转换为任务格式

## 注意事项

1. **定理格式**：PutnamBench 的定理主要是 `theorem ... := by sorry` 形式
2. **Docstring**：问题描述在 `/-- ... -/` 中，可能包含 LaTeX 数学公式
3. **Imports**：需要保留原有的 `import` 和 `open` 语句
4. **占位符**：`sorry` 会被替换为 `{{proof}}` 占位符

## 示例输出

处理 `putnam_1962_a1.lean` 后，会生成：

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
: ∃ T ⊆ S, T.ncard = 4 ∧ ¬∃ t ∈ T, t ∈ convexHull ℝ (T \ {t}) := by
  -- << PROOF START >>
  {{proof}}
  -- << PROOF END >>
```

Agent 会生成证明来替换 `{{proof}}`。

