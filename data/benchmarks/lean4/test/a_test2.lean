import Mathlib

/-
题目说明（非形式化表述）：
设 P, Q, R 为命题。已知 P ∧ Q 和 Q ∧ R 同时为真，证明 Q ∧ (P ∧ R) 为真。
也就是在“链式”出现的三个命题里，把 Q 提到最前面，其余保持顺序。
-/

theorem and_chain_test (P Q R : Prop) (h₁ : P ∧ Q) (h₂ : Q ∧ R) : Q ∧ (P ∧ R) := by
  sorry
