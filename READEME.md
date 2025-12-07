# 开发日记
11.24 
- 完成data数据加载
- 完成LLM类的构建，能从openai-api加载，并且通信，支持本地vLLM
- 完成lean4runner，能根据benckmark的环境进行lean4语言的验证
下一步：
- 完成Agent的开发，串起来这三个
  - 基础闭环
  - 多轮自我修复机制
  - 提示词：Agent = prompt + 结构化循环逻辑 + 状态管理 + 错误修复策略 + 搜索策略


11.25·
- 完成基础闭环
- 完成多轮修复，但是仍然没法验证问题
下一步：
- 可以实现更精细化的agent还有提示词，可能需要看论文去了

11.27
- 复现论文
  - 构建定理库

11.28
- 预计完成工作：
  - 向量retrivev检索模块，编码informal的向量.
  - 然后检索query-对应定理
  
11.30
- 完成向量构建，使用faiss，存到本地。写个test脚本。使用的时候，加载faiss，加载dataset，然后embedding，最后查找对应定理

12.4 
- 整体代码框架完成，但是没有运行跑通
  
明天
- 调试整体代码

# lean的理解
```
by
  -- Step 1: Convert S into a finite list of 5 points
  -- We will need an enumeration lemma for finite sets
  obtain ⟨p1, p2, p3, p4, p5, hSenum⟩ :=
    by
      -- TODO: Use `Set.ncard_eq_fintype` or `finite_of_ncard` to extract 5 elements
      sorry

  -- Step 2: Consider the convex hull of all 5 points
  let hull5 := convexHull ℝ {p1, p2, p3, p4, p5}

  -- Step 3: One of the 5 points must be a vertex of the convex hull
  -- (otherwise all 5 lie inside convex hull of others → contradiction)
  have h_vertex :
      ∃ v ∈ {p1, p2, p3, p4, p5},
        v ∉ convexHull ℝ ({p1, p2, p3, p4, p5} \ {v}) :=
    by
      -- TODO: Proof by pigeonhole principle + non-collinearity
      sorry

  -- Unpack the witness point
  obtain ⟨v, hv_set, hv_out⟩ := h_vertex

  -- Step 4: Let T be any 4-point subset removing this vertex
  let T := ({p1, p2, p3, p4, p5} \ {v})

  have hT_subset : T ⊆ S := by
    -- direct by construction
    sorry

  have hT_card : T.ncard = 4 := by
    -- because S has 5 points and we removed exactly one
    -- use lemma: ncard_diff_singleton_of_mem
    sorry

  -- Step 5: Show the property required in the theorem
  have h_convex_property :
      ¬ ∃ t ∈ T, t ∈ convexHull ℝ (T \ {t}) :=
    by
      intro h
      rcases h with ⟨t, htT, ht_in_hull⟩
      -- but v was chosen as the unique point outside the hull
      -- contradiction with hv_out
      sorry

  -- Step 6: Return result
  exact ⟨T, hT_subset, hT_card, h_convex_property⟩
```

- by就是要开始证明的意思，Theorem A：B := by
- sorry 就是暂时不证明

- 检查语法
- 上下文正确
- 左侧必须合法

# 例子
## sketch
```lean
theorem example_theorem
  (A B C : Set ℝ)
  (h1 : A ⊆ B)
  (h2 : B ⊆ C)
  : A ⊆ C := by
  intro x
  intro hxA

  -- Subgoal 1: Show x ∈ B using h1
  have hxB : x ∈ B := by
    -- reasoning: A ⊆ B, x ∈ A → x ∈ B
    sorry

  -- Subgoal 2: Show x ∈ C using h2
  have hxC : x ∈ C := by
    -- reasoning: B ⊆ C, x ∈ B → x ∈ C
    sorry

  -- Final step: combine subgoals
  exact hxC
```