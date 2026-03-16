import subprocess
import logging
from datetime import datetime

from observability.langfuse import langfuse
from evals.judge import ScoreResult

logger = logging.getLogger(__name__)


def _get_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def get_run_name() -> str:
    sha = _get_git_sha()
    return f"{datetime.utcnow():%Y-%m-%d}_{sha[:7]}"


def push_scores(trace_id: str, scores: list[ScoreResult]) -> None:
    for score in scores:
        try:
            langfuse.score(
                trace_id=trace_id,
                name=score.name,
                value=score.score,
                comment=score.reason,
            )
        except Exception as e:
            logger.error(f"Failed to push score {score.name} for trace {trace_id}: {e}")


def create_dataset_item(dataset_name: str, input_data: dict, expected_output: dict | None = None) -> str | None:
    """Create a dataset item in Langfuse and return its ID."""
    try:
        dataset = langfuse.get_dataset(dataset_name)
    except Exception:
        try:
            langfuse.create_dataset(dataset_name)
            dataset = langfuse.get_dataset(dataset_name)
        except Exception as e:
            logger.error(f"Failed to get/create dataset {dataset_name}: {e}")
            return None

    try:
        item = langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=input_data,
            expected_output=expected_output,
        )
        return item.id
    except Exception as e:
        logger.error(f"Failed to create dataset item: {e}")
        return None
