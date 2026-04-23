from __future__ import annotations
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .utils import normalize_answer

FIRST_ATTEMPT_WRONG = {
    "hp2": "London", "hp4": "Atlantic Ocean", "hp6": "Red Sea", "hp8": "Andes",
    "hp13": "Egypt", "hp15": "Japan", "hp25": "Brazil", "hp27": "Congo River",
    "hp28": "Venezuela waterfall", "hp33": "Dubai tower", "hp35": "Peru",
    "hp37": "volcano", "hp43": "Pacific Ocean deep", "hp48": "Badaling wall",
    "hp10": "Agra", "hp17": "China", "hp32": "Rome currency",
    "hp42": "Netherlands", "hp45": "Athens language", "hp50": "London currency",
    "hp52": "Moscow", "hp55": "Athens", "hp58": "Colorado River",
    "hp60": "Berlin", "hp62": "Granada", "hp65": "Japan",
    "hp67": "United States", "hp70": "Cambodia", "hp72": "Japan",
    "hp75": "Dubai", "hp77": "Pisa", "hp80": "Istanbul",
    "hp82": "China", "hp85": "Cape Town", "hp87": "Istanbul",
    "hp90": "Paris", "hp92": "United States", "hp95": "Cape Town",
    "hp97": "Moscow", "hp100": "Toronto",
}
FAILURE_MODE_BY_QID = {
    "hp2": "incomplete_multi_hop", "hp4": "wrong_final_answer", "hp6": "entity_drift",
    "hp8": "entity_drift", "hp13": "incomplete_multi_hop", "hp15": "incomplete_multi_hop",
    "hp25": "wrong_final_answer", "hp27": "entity_drift", "hp28": "incomplete_multi_hop",
    "hp33": "incomplete_multi_hop", "hp35": "incomplete_multi_hop", "hp37": "wrong_final_answer",
    "hp43": "incomplete_multi_hop", "hp48": "incomplete_multi_hop", "hp10": "incomplete_multi_hop",
    "hp17": "incomplete_multi_hop", "hp32": "incomplete_multi_hop", "hp42": "incomplete_multi_hop",
    "hp45": "incomplete_multi_hop", "hp50": "incomplete_multi_hop",
    "hp52": "incomplete_multi_hop", "hp55": "incomplete_multi_hop", "hp58": "wrong_final_answer",
    "hp60": "incomplete_multi_hop", "hp62": "incomplete_multi_hop", "hp65": "incomplete_multi_hop",
    "hp67": "incomplete_multi_hop", "hp70": "incomplete_multi_hop", "hp72": "incomplete_multi_hop",
    "hp75": "incomplete_multi_hop", "hp77": "incomplete_multi_hop", "hp80": "incomplete_multi_hop",
    "hp82": "incomplete_multi_hop", "hp85": "incomplete_multi_hop", "hp87": "incomplete_multi_hop",
    "hp90": "incomplete_multi_hop", "hp92": "incomplete_multi_hop", "hp95": "incomplete_multi_hop",
    "hp97": "incomplete_multi_hop", "hp100": "incomplete_multi_hop",
}

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> str:
    if example.qid not in FIRST_ATTEMPT_WRONG:
        return example.gold_answer
    if agent_type == "react":
        return FIRST_ATTEMPT_WRONG[example.qid]
    if attempt_id == 1 and not reflection_memory:
        return FIRST_ATTEMPT_WRONG[example.qid]
    return example.gold_answer

def evaluator(example: QAExample, answer: str) -> JudgeResult:
    if normalize_answer(example.gold_answer) == normalize_answer(answer):
        return JudgeResult(score=1, reason="Final answer matches the gold answer after normalization.")
    if normalize_answer(answer) == "london":
        return JudgeResult(score=0, reason="The answer stopped at the birthplace city and never completed the second hop to the river.", missing_evidence=["Need to identify the river that flows through London."], spurious_claims=[])
    return JudgeResult(score=0, reason="The final answer selected the wrong second-hop entity.", missing_evidence=["Need to ground the answer in the second paragraph."], spurious_claims=[answer])

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> ReflectionEntry:
    strategy = "Do the second hop explicitly: birthplace city -> river through that city." if example.qid == "hp2" else "Verify the final entity against the second paragraph before answering."
    return ReflectionEntry(attempt_id=attempt_id, failure_reason=judge.reason, lesson="A partial first-hop answer is not enough; the final answer must complete all hops.", next_strategy=strategy)
