"""
Eval runner for SCYES agent.

Usage:
    python -m evals.runner                          # run all datasets
    python -m evals.runner --dataset tool_selection # run one dataset
    python -m evals.runner --no-langfuse            # skip Langfuse push
    python -m evals.runner --fail-under 0.75        # exit 1 if score < threshold
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from integrations.tavily import tavily_search
from integrations.wikipedia import wikipedia
from integrations.giphy import giphy
from integrations.google_calendar import list_calendar_events, create_calendar_event
from llm.google import google_model
from evals.judge import ScoreResult, score_tool_use, score_word_count, score_with_llm
from evals.langfuse_sync import get_run_name, push_scores

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DATASETS_DIR = Path(__file__).parent / "datasets"

EVAL_TOOLS = [
    tavily_search,
    wikipedia,
    giphy,
    list_calendar_events,
    create_calendar_event,
]


def invoke_agent_for_eval(message: str) -> tuple[str, list[str]]:
    """Invoke agent and return (response_text, list_of_tool_names_called)."""
    system_prompt = SystemMessage(
        content=[
            {
                "type": "text",
                "text": (
                    f"You're a chatbot. Please keep your responses concise, specifically to below 300 words. "
                    f"Today is {datetime.today().strftime('%Y-%m-%d')}. "
                    f"The current time is {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')} UTC."
                ),
            }
        ]
    )
    agent = create_agent(google_model, system_prompt=system_prompt, tools=EVAL_TOOLS)
    result = agent.invoke(message)

    messages = result.get("messages", []) if isinstance(result, dict) else []
    tool_calls = [
        tc["name"]
        for msg in messages
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    response_text = messages[-1].content if messages else (result.content if hasattr(result, "content") else "")
    return response_text, tool_calls


def run_tool_selection_case(case: dict, run_name: str, push_langfuse: bool) -> tuple[bool, float]:
    case_id = case["id"]
    logger.info(f"  Running case: {case_id}")

    try:
        response_text, tool_calls = invoke_agent_for_eval(case["input"])
    except Exception as e:
        logger.error(f"  Agent error for {case_id}: {e}")
        return False, 0.0

    score = score_tool_use(
        expected=case["expected_tools"],
        actual=tool_calls,
        mode=case["expected_tools_mode"],
    )

    status = "PASS" if score.passed else "FAIL"
    print(f"    [{status}] tool_use  score={score.score:.2f}  {score.reason}")
    print(f"           tools called: {tool_calls}")

    if push_langfuse:
        try:
            from observability.langfuse import langfuse
            trace = langfuse.trace(
                name=f"eval_{case_id}",
                input=case["input"],
                output=response_text,
                metadata={"run_name": run_name, "dataset": "tool_selection", "case_id": case_id},
                tags=case.get("tags", []),
            )
            push_scores(trace.id, [score])
        except Exception as e:
            logger.warning(f"  Langfuse push failed: {e}")

    return score.passed, score.score


def run_response_quality_case(case: dict, run_name: str, push_langfuse: bool) -> tuple[bool, float]:
    case_id = case["id"]
    logger.info(f"  Running case: {case_id}")

    try:
        response_text, _ = invoke_agent_for_eval(case["input"])
    except Exception as e:
        logger.error(f"  Agent error for {case_id}: {e}")
        return False, 0.0

    scores: list[ScoreResult] = []
    scores.append(score_word_count(response_text))
    scores.append(score_with_llm(case["input"], response_text, case["judge_criteria"]))

    for s in scores:
        status = "PASS" if s.passed else "FAIL"
        print(f"    [{status}] {s.name:20s}  score={s.score:.2f}  {s.reason}")

    if push_langfuse:
        try:
            from observability.langfuse import langfuse
            trace = langfuse.trace(
                name=f"eval_{case_id}",
                input=case["input"],
                output=response_text,
                metadata={"run_name": run_name, "dataset": "response_quality", "case_id": case_id},
                tags=case.get("tags", []),
            )
            push_scores(trace.id, scores)
        except Exception as e:
            logger.warning(f"  Langfuse push failed: {e}")

    all_passed = all(s.passed for s in scores)
    avg_score = sum(s.score for s in scores) / len(scores)
    return all_passed, avg_score


def load_dataset(name: str) -> list[dict]:
    path = DATASETS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with open(path) as f:
        return json.load(f)


def run_dataset(name: str, run_name: str, push_langfuse: bool) -> tuple[int, int, float]:
    """Returns (passed, total, avg_score)."""
    print(f"\n{'='*60}")
    print(f"Dataset: {name}  (run: {run_name})")
    print(f"{'='*60}")

    cases = load_dataset(name)
    # Skip placeholder regression cases
    cases = [c for c in cases if c.get("input") != "placeholder - replace with real regression case"]

    if not cases:
        print("  No cases to run.")
        return 0, 0, 1.0

    passed_count = 0
    scores = []

    for case in cases:
        print(f"\n  [{case['id']}] {case['input'][:70]}...")
        if name == "tool_selection":
            passed, score = run_tool_selection_case(case, run_name, push_langfuse)
        elif name in ("response_quality", "regression"):
            passed, score = run_response_quality_case(case, run_name, push_langfuse)
        else:
            # Unknown dataset: try tool_selection format first
            if "expected_tools" in case:
                passed, score = run_tool_selection_case(case, run_name, push_langfuse)
            else:
                passed, score = run_response_quality_case(case, run_name, push_langfuse)

        if passed:
            passed_count += 1
        scores.append(score)

    avg_score = sum(scores) / len(scores) if scores else 0.0
    print(f"\n  Summary: {passed_count}/{len(cases)} passed  avg_score={avg_score:.3f}")
    return passed_count, len(cases), avg_score


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SCYES agent evals")
    parser.add_argument(
        "--dataset",
        choices=["tool_selection", "response_quality", "regression", "all"],
        default="all",
        help="Which dataset to run (default: all)",
    )
    parser.add_argument(
        "--no-langfuse",
        action="store_true",
        help="Skip pushing results to Langfuse",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=None,
        metavar="THRESHOLD",
        help="Exit with code 1 if composite score is below this threshold (0.0–1.0)",
    )
    args = parser.parse_args()

    push_langfuse = not args.no_langfuse
    run_name = get_run_name()

    datasets_to_run = (
        ["tool_selection", "response_quality", "regression"]
        if args.dataset == "all"
        else [args.dataset]
    )

    all_scores: list[float] = []
    for dataset_name in datasets_to_run:
        _, _, avg = run_dataset(dataset_name, run_name, push_langfuse)
        all_scores.append(avg)

    composite = sum(all_scores) / len(all_scores) if all_scores else 0.0

    print(f"\n{'='*60}")
    print(f"Composite score: {composite:.3f}")
    if args.fail_under is not None:
        if composite < args.fail_under:
            print(f"FAILED: composite {composite:.3f} < threshold {args.fail_under}")
            sys.exit(1)
        else:
            print(f"PASSED: composite {composite:.3f} >= threshold {args.fail_under}")
    print(f"{'='*60}")

    if push_langfuse:
        try:
            from observability.langfuse import langfuse
            langfuse.flush()
        except Exception as e:
            logger.warning(f"Langfuse flush failed: {e}")


if __name__ == "__main__":
    main()
