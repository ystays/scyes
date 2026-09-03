import json
import random
from pathlib import Path
from langchain.tools import tool

_QUESTIONS: list[dict] = json.loads(
    (Path(__file__).parent.parent / "rag" / "questions.json").read_text()
)


@tool
def get_random_leetcode_question(category: str = "", difficulty: str = "") -> str:
    """Retrieve a random LeetCode question directly from the local dataset.

    Args:
        category: Optional filter: Array, Binary, DP, Graph, Interval, Linked List,
                  Matrix, String, Tree, Heap, Two Pointers.
        difficulty: Optional filter: Easy, Medium, Hard.
    """
    questions = list(_QUESTIONS)

    if category:
        questions = [q for q in questions if q["category"] == category]
    if difficulty:
        questions = [q for q in questions if q["difficulty"] == difficulty]

    if not questions:
        return "No questions found matching your criteria."

    q = random.choice(questions)
    examples = "\n".join(
        f"Input: {e['input']}\nOutput: {e['output']}"
        + (f"\nExplanation: {e['explanation']}" if e.get("explanation") else "")
        for e in q.get("examples", [])
    )
    content = f"{q['title']}\n\n{q['description']}\n\nExamples:\n{examples}"
    return f"**{q['title']}** ({q['difficulty']} | {q['category']})\n{q['url']}\n\n{content}"
