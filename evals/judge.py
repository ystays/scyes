import json
import logging
from dataclasses import dataclass

from llm.google import gemini_2_5_flash_model

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    name: str
    passed: bool
    score: float  # 0.0–1.0
    reason: str


def score_tool_use(
    expected: list[str], actual: list[str], mode: str
) -> ScoreResult:
    """Score whether the agent called the expected tools."""
    actual_set = set(actual)
    expected_set = set(expected)

    if mode == "exact":
        passed = actual_set == expected_set
        if passed:
            score = 1.0
            reason = f"Exact match: {actual_set}"
        else:
            score = 0.0
            extra = actual_set - expected_set
            missing = expected_set - actual_set
            reason = f"Expected exactly {expected_set}, got {actual_set}. Extra: {extra}, Missing: {missing}"

    elif mode == "all":
        missing = expected_set - actual_set
        passed = len(missing) == 0
        if passed:
            score = 1.0
            reason = f"All expected tools called: {expected_set}"
        else:
            score = len(expected_set - missing) / len(expected_set) if expected_set else 0.0
            reason = f"Missing tools: {missing}. Called: {actual_set}"

    elif mode == "any":
        intersection = expected_set & actual_set
        passed = len(intersection) > 0
        if passed:
            score = 1.0
            reason = f"At least one expected tool called: {intersection}"
        else:
            score = 0.0
            reason = f"None of {expected_set} were called. Got: {actual_set}"

    else:
        raise ValueError(f"Unknown mode: {mode}")

    return ScoreResult(name="tool_use", passed=passed, score=score, reason=reason)


def score_word_count(text: str, limit: int = 300) -> ScoreResult:
    """Score whether the response is within the word count limit."""
    count = len(text.split())
    passed = count <= limit
    score = 1.0 if passed else max(0.0, 1.0 - (count - limit) / limit)
    reason = f"{count} words (limit: {limit})"
    return ScoreResult(name="word_count", passed=passed, score=score, reason=reason)


def score_with_llm(input: str, response: str, criteria: str) -> ScoreResult:
    """Use LLM-as-judge to score response quality."""
    prompt = f"""You are an objective evaluator. Score the following AI response based on the given criteria.

User input: {input}

AI response: {response}

Evaluation criteria: {criteria}

Respond with valid JSON only, no markdown:
{{"score": <integer 1-5>, "reason": "<one sentence explanation>"}}

Score guide: 1=very poor, 2=poor, 3=acceptable, 4=good, 5=excellent"""

    try:
        result = gemini_2_5_flash_model.invoke(prompt)
        raw = result.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        llm_score = int(data["score"])
        reason = data.get("reason", "")
        normalized = (llm_score - 1) / 4.0  # 1-5 → 0.0-1.0
        passed = llm_score >= 4
        return ScoreResult(
            name="response_quality",
            passed=passed,
            score=normalized,
            reason=f"LLM score {llm_score}/5: {reason}",
        )
    except Exception as e:
        logger.error(f"LLM judge failed: {e}")
        return ScoreResult(
            name="response_quality",
            passed=False,
            score=0.0,
            reason=f"Judge error: {e}",
        )
