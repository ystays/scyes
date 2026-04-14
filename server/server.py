"""FastAPI server"""

from typing import Any

from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from llm.langchain_agent import ainvoke_agent
from llm.adk_agent import ainvoke_adk_agent
from fastapi import StreamingResponse

import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="My API Server")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello!", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api_server"}

class InvokeRequest(BaseModel):
    input: str

@app.post("/agent/invoke")
async def invoke(request: InvokeRequest) -> Any:
    output = await ainvoke_agent(request.input)
    return {"output": output}


@app.post("/adk-agent/invoke")
async def invoke_adk(request: InvokeRequest) -> Any:
    output = await ainvoke_adk_agent(request.input)
    return {"output": output}

@app.post("/pydantic-agent/invoke")
async def invoke_pydantic(http_request: Request, request: InvokeRequest) -> Any:
    output = await http_request.app.state.deep_agent.ainvoke(request.input)
    return {"output": output}


@app.post("/pydantic-agent/stream")
async def stream_pydantic(http_request: Request, request: InvokeRequest):
    async def generate():
        async for chunk in http_request.app.state.deep_agent.astream(request.input):
            yield chunk
    return StreamingResponse(generate(), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
