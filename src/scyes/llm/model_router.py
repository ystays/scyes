import re
from typing import Literal

from langchain_core.language_models import BaseChatModel

from scyes.llm.google import gemini_2_5_flash_model, google_model

# Patterns that signal a simple, short factual question
_SIMPLE_PATTERNS = re.compile(
    r"^(what is|what's|who is|who's|when (is|was|did)|where is|where's|"
    r"how (many|much|old|tall|far)|define|what does .+ mean)\b",
    re.IGNORECASE,
)

# Keywords that signal the query needs deeper reasoning
_COMPLEX_KEYWORDS = re.compile(
    r"\b(explain|analyze|analyse|compare|contrast|difference between|"
    r"how does .+ work|write|generate|summarize|debate|pros and cons|"
    r"step.by.step|implement|refactor|debug|review|critique|evaluate)\b",
    re.IGNORECASE,
)

_COMPLEX_WORD_THRESHOLD = 30
_SIMPLE_WORD_THRESHOLD = 10


def classify_complexity(message: str) -> Literal["standard", "complex"]:
    words = message.split()
    word_count = len(words)

    if word_count >= _COMPLEX_WORD_THRESHOLD or _COMPLEX_KEYWORDS.search(message):
        return "complex"

    if word_count <= _SIMPLE_WORD_THRESHOLD and _SIMPLE_PATTERNS.match(message.strip()):
        return "standard"

    return "standard"


def get_model(message: str) -> BaseChatModel:
    complexity = classify_complexity(message)
    if complexity == "complex":
        return gemini_2_5_flash_model
    return google_model
