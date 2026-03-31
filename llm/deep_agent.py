from typing import AsyncIterator, Any
import logging

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from integrations.tavily import tavily_search
from integrations.wikipedia import wikipedia
from integrations.giphy import giphy
from integrations.google_calendar import list_calendar_events, create_calendar_event
from integrations.mcp import HA_MCP_CONFIG
from integrations.msg_scheduler import create_msg_scheduler_tool

from llm.google import google_model  # noqa F401 — ensures GOOGLE_API_KEY is set
from llm.prompt import deepagent_system_prompt
from config import app_config

from observability.langfuse import langfuse  # noqa F401
from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

_BASE_TOOLS = [tavily_search, wikipedia, giphy, list_calendar_events, create_calendar_event]


def _db_url() -> str:
    cfg = app_config.get_database_config()
    return (
        f"postgresql://{cfg['username']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['db_name']}"
    )


def _make_backend(runtime):
    """Route /memories/ to the persistent store; everything else stays in thread state."""
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": StoreBackend(
                runtime,
                namespace=lambda ctx: (ctx.runtime.context.user_id,),
            )
        },
    )


class DeepAgent:
    def __init__(self, checkpointer, store, store_ctx, invoke_agent):
        self._checkpointer = checkpointer
        self._store = store
        self._store_ctx = store_ctx
        self._invoke_agent = invoke_agent
        self._langfuse_handler = CallbackHandler()

    @classmethod
    async def create(cls) -> "DeepAgent":
        """Initialize Postgres-backed checkpointer and store. Call once at startup."""
        url = _db_url()

        store_ctx = PostgresStore.from_conn_string(url)
        store = store_ctx.__enter__()
        store.setup()

        checkpointer = await AsyncPostgresSaver.from_conn_string(url)
        await checkpointer.setup()

        invoke_agent = create_deep_agent(
            tools=_BASE_TOOLS,
            system_prompt=deepagent_system_prompt(),
            checkpointer=checkpointer,
            store=store,
            backend=_make_backend,
        )

        logger.info("Deep agent memory initialized.")
        return cls(checkpointer, store, store_ctx, invoke_agent)

    async def close(self):
        """Release Postgres connections. Call once at shutdown."""
        self._store_ctx.__exit__(None, None, None)

    def _config(self, user_id: str) -> dict:
        return {
            "configurable": {"thread_id": user_id, "user_id": user_id},
            "callbacks": [self._langfuse_handler],
        }

    async def ainvoke(self, message: str, user_id: str = "server") -> str:
        try:
            async with MultiServerMCPClient(HA_MCP_CONFIG) as mcp_client:
                try:
                    mcp_tools = await mcp_client.get_tools()
                except Exception as mcp_err:
                    logger.warning(f"MCP tools unavailable, skipping: {mcp_err}")
                    mcp_tools = []

            response = await self._invoke_agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=self._config(user_id),
            )
            return response["messages"][-1].content
        except Exception as e:
            logger.exception("Error invoking deep agent")
            return f"Error invoking deep agent: {str(e)}"

    async def astream(
        self,
        message: str,
        user_id: str,
        bot=None,
        channel_id: int = 0,
        scheduler=None,
    ) -> AsyncIterator[dict[str, Any] | Any]:
        try:
            async with MultiServerMCPClient(HA_MCP_CONFIG) as mcp_client:
                try:
                    mcp_tools = await mcp_client.get_tools()
                except Exception as mcp_err:
                    logger.warning(f"MCP tools unavailable, skipping: {mcp_err}")
                    mcp_tools = []

                tools = _BASE_TOOLS + [
                    create_msg_scheduler_tool(bot, channel_id, scheduler),
                ] + mcp_tools

                agent = create_deep_agent(
                    tools=tools,
                    system_prompt=deepagent_system_prompt(),
                    checkpointer=self._checkpointer,
                    store=self._store,
                    backend=_make_backend,
                )
                async for item in agent.astream(
                    {"messages": [HumanMessage(content=message)]},
                    stream_mode="messages",
                    config=self._config(user_id),
                ):
                    yield item
        except Exception as e:
            logger.exception("Error streaming deep agent response")
            yield AIMessageChunk(content=f"Error streaming deep agent response: {str(e)}"), {}
