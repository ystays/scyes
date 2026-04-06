import logging

from pydantic_ai import RunContext
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.tools import ToolDefinition

from llm.pydantic_agent.deps import AgentDeps

logger = logging.getLogger(__name__)


async def log_tool_call(
    ctx: RunContext[AgentDeps],
    /,
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: dict,
) -> dict:
    """Log each tool call before execution."""
    logger.info("tool_call user=%s tool=%s args=%s", ctx.deps.user_id, tool_def.name, args)
    return args
