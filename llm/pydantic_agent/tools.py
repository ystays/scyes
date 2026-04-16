import asyncio
import os

from pydantic_ai import RunContext

from llm.pydantic_agent.deps import AgentDeps, InMemoryBackend

# Fallback used when no deps are injected (e.g. pydantic-ai CLI passes deps=None).
_default_deps = AgentDeps(fs=InMemoryBackend(), user_id="cli")


def _deps(ctx: RunContext[AgentDeps | None]) -> AgentDeps:
    return ctx.deps if ctx.deps is not None else _default_deps


async def ls(ctx: RunContext[AgentDeps | None], path: str) -> list[str]:
    """List files in the virtual filesystem at the given path."""
    return await _deps(ctx).fs.ls(path)


async def read_file(ctx: RunContext[AgentDeps | None], path: str) -> str:
    """Read a file from the virtual filesystem."""
    return await _deps(ctx).fs.read(path)


async def write_file(ctx: RunContext[AgentDeps | None], path: str, content: str) -> str:
    """Write content to a file in the virtual filesystem."""
    await _deps(ctx).fs.write(path, content)
    return f"Wrote {len(content)} chars to {path}."


async def edit_file(
    ctx: RunContext[AgentDeps | None], path: str, old_str: str, new_str: str
) -> str:
    """Replace old_str with new_str in a virtual filesystem file."""
    await _deps(ctx).fs.edit(path, old_str, new_str)
    return f"Edited {path}."


async def bash(ctx: RunContext[AgentDeps | None], command: str, timeout: int = 30) -> str:
    """Run a shell command and return its output (stdout + stderr combined)."""
    timeout = min(timeout, 120)
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=os.getcwd(),
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return f"Command timed out after {timeout}s."

    output = stdout.decode(errors="replace")
    max_chars = 20_000
    if len(output) > max_chars:
        half = max_chars // 2
        output = output[:half] + "\n...[truncated]...\n" + output[-half:]

    exit_code = proc.returncode
    if exit_code != 0:
        output = f"[exit code {exit_code}]\n{output}"
    return output or "(no output)"
