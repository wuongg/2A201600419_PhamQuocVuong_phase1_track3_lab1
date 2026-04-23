from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .mock_runtime import FAILURE_MODE_BY_QID, actor_answer, evaluator, reflector
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

# Bonus: adaptive_max_attempts — map difficulty to max attempts
DIFFICULTY_MAX_ATTEMPTS = {"easy": 2, "medium": 3, "hard": 5}

def _compress_memory(memory: list[str], max_entries: int = 3) -> list[str]:
    """Bonus: memory_compression — keep only the most recent strategies,
    summarizing older ones into a single condensed entry."""
    if len(memory) <= max_entries:
        return memory
    kept = memory[-max_entries:]
    older = memory[:-max_entries]
    summary = "Earlier strategies tried: " + "; ".join(older) + "."
    return [summary] + kept

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    adaptive: bool = False
    compress_memory: bool = False
    memory_max_entries: int = 3

    def _effective_max_attempts(self, example: QAExample) -> int:
        if self.adaptive:
            return DIFFICULTY_MAX_ATTEMPTS.get(example.difficulty, self.max_attempts)
        return self.max_attempts

    def run(self, example: QAExample) -> RunRecord:
        eff_max = self._effective_max_attempts(example)
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        for attempt_id in range(1, eff_max + 1):
            # Bonus: memory_compression — compress before each attempt
            if self.compress_memory:
                reflection_memory = _compress_memory(reflection_memory, self.memory_max_entries)
            answer = actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            judge = evaluator(example, answer)
            # Mock token estimate — replace with actual token count from LLM response when using real model
            token_estimate = 320 + (attempt_id * 65) + (120 if self.agent_type == "reflexion" else 0)
            # Mock latency — replace with actual latency measurement when using real model
            latency_ms = 160 + (attempt_id * 40) + (90 if self.agent_type == "reflexion" else 0)
            trace = AttemptTrace(attempt_id=attempt_id, answer=answer, score=judge.score, reason=judge.reason, token_estimate=token_estimate, latency_ms=latency_ms)
            final_answer = answer
            final_score = judge.score
            if judge.score == 1:
                traces.append(trace)
                break

            # Reflexion logic: reflect on failure and update memory for next attempt
            if self.agent_type == "reflexion" and attempt_id < eff_max:
                reflection = reflector(example, attempt_id, judge)
                reflections.append(reflection)
                reflection_memory.append(reflection.next_strategy)
                trace.reflection = reflection
            traces.append(trace)
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = "none" if final_score == 1 else FAILURE_MODE_BY_QID.get(example.qid, "wrong_final_answer")
        return RunRecord(qid=example.qid, question=example.question, gold_answer=example.gold_answer, agent_type=self.agent_type, predicted_answer=final_answer, is_correct=bool(final_score), attempts=len(traces), token_estimate=total_tokens, latency_ms=total_latency, failure_mode=failure_mode, reflections=reflections, traces=traces)

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3, adaptive: bool = True, compress_memory: bool = True) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts, adaptive=adaptive, compress_memory=compress_memory)
