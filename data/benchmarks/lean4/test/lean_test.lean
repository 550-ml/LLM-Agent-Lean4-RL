import Mathlib

/--
这是一个简单的测试定理：
对任意自然数 a b，a + b = b + a。
-/
theorem my_add_comm (a b : Nat) : a + b = b + a := by
  -- 直接用库里的现成引理 Nat.add_comm
  exact Nat.add_comm a b