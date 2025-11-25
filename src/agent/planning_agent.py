from .base import BaseAgent, AgentState
from typing import Dict, Any
from ..llm.base import BaseLLM


class PlanningAgent(BaseAgent):
    """规划智能体

    负责：
    1. 分析问题描述
    2. 理解任务模板
    3. 制定证明策略和步骤
    """

    def __init__(self, llm: BaseLLM):
        super().__init__(llm, "PlanningAgent")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        # * 1.prompt template
        planning_prompt = f"""
        You are an expert mathematician and Lean4 formalization planner.
In this PLANNING PHASE your ONLY job is to analyze the problem
and design a high-quality proof strategy. You must NOT write any Lean code.

================== Problem ==================
{state.problem_description}

================== Lean Theorem Template (for reference only) ==================
```lean
{state.task_template}
        The Lean theorem template already contains the correct imports, the theorem
statement, and a placeholder {{proof}} where the proof script will go.
You should NOT modify or restate the Lean code. It is shown only so that
you understand the formal goal and context.

Please respond in clear natural language (no Lean code) and follow EXACTLY
this structure:
	1.	INFORMAL RESTATEMENT
	•	Restate the problem in your own words.
	•	Clarify what is being quantified (e.g., “for any finite set S of points…”)
and what must be shown to exist.
	•	If the problem is geometric/combinatorial/analytic, explicitly say which.
	2.	KEY OBJECTS AND DEFINITIONS
	•	List the main mathematical objects that appear in the formal theorem,
for example:
	•	sets and their cardinalities (Set, ncard)
	•	geometric concepts (convexHull, collinearity)
	•	algebraic structures (groups, rings, etc., if present)
	•	For each object, explain informally how it will be used in the proof.
	3.	IMPORTANT LEMMAS AND FACTS (INFORMAL)
	•	List standard theorems / lemmas that are likely needed.
	•	You may refer to them by informal names (e.g. “pigeonhole principle”,
“Carathéodory’s theorem”, “properties of convex hulls”) or by likely
Lean names (e.g. convexHull_min, subset_convexHull, etc.).
	•	DO NOT write Lean statements or proofs here; just describe what they say.
	4.	HIGH-LEVEL PROOF STRATEGY (STEP-BY-STEP)
	•	Give a numbered outline (Step 1, Step 2, …) of the intended mathematical
proof, at the level a human mathematician would understand.
	•	Make sure the steps are concrete enough that a later agent can translate
them into a Lean proof script. Avoid hand-wavy phrases like “then it is
obvious”; instead, explain what should actually be shown.
	•	Highlight any case splits or structural choices (e.g. “consider whether
all 5 points lie on the boundary of the convex hull”, etc.).
	5.	HINTS FOR LEAN4 FORMALIZATION (TACTIC-LEVEL GUIDANCE, STILL INFORMAL)
	•	Describe how the high-level strategy might be implemented in Lean4:
	•	what to “use” as witnesses for existential goals,
	•	when to use intro, rcases, obtain, by_contra, have, etc.,
	•	how to work with finite sets (ncard, Finite), and
	•	how to work with convexHull and set inclusions (⊆, ∈).
	•	Mention typical tactic patterns that are appropriate for this kind of goal
(e.g. refine ?_, simp with relevant lemmas, rewriting equalities, etc.),
but DO NOT write actual tactic code.
	6.	POTENTIAL DIFFICULTIES AND SUBGOALS
	•	Identify the technically difficult parts of the formalization
(e.g., enumerating subsets of a finite set, proving non-collinearity,
working with convex hulls).
	•	For each difficulty, suggest one or more subgoals that, if proved,
would make the final result easier to formalize.
	•	These subgoals should be described in natural language only
(no Lean code), but should be reasonably precise.

STRICT CONSTRAINTS:
	•	Do NOT include any Lean code, theorem, lemma, def, begin, or end.
	•	Do NOT include ```lean code blocks.
	•	Do NOT try to fill in the proof; that will be done in the next phase.
	•	Your output must be purely natural language, following the numbered sections above.
"""
        # * 2. call llm
        messages = [
            {"role": "system", "content": "You are a professional Lean4 formal verification planning expert."},
            {"role": "user", "content": planning_prompt}
        ]
        plan = self.llm.get_response(messages)

        # * 3. update state
        state.planning_result = plan

        return {
            "plan": plan,
            "success": True
        }
