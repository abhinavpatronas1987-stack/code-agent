"""FastAPI server with WebSocket support for the coding agent."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config.settings import get_settings
from src.agents.coding_agent import CodingAgent


# Store active sessions
sessions: dict[str, CodingAgent] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Ollama model: {settings.ollama_model}")
    print(f"Server: http://{settings.host}:{settings.port}")
    yield
    # Shutdown
    sessions.clear()
    print("Server shutdown complete")


app = FastAPI(
    title="Code Agent API",
    description="Agentic Development Environment API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str | None = None
    workspace: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""
    session_id: str
    response: str
    tool_calls: list[dict] = []


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    workspace: str | None = None
    message_count: int = 0


# REST Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the coding agent.

    This endpoint processes messages synchronously (non-streaming).
    For streaming responses, use the WebSocket endpoint.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Get or create agent for this session
    if session_id not in sessions:
        sessions[session_id] = CodingAgent(
            session_id=session_id,
            workspace=request.workspace,
        )

    agent = sessions[session_id]

    try:
        # Run agent (non-streaming)
        response = agent.run(request.message, stream=False)

        return ChatResponse(
            session_id=session_id,
            response=response.content if hasattr(response, 'content') else str(response),
            tool_calls=[],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions", response_model=SessionInfo)
async def create_session(workspace: str | None = None):
    """Create a new agent session."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = CodingAgent(
        session_id=session_id,
        workspace=workspace,
    )

    return SessionInfo(
        session_id=session_id,
        workspace=workspace,
    )


@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session information."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = sessions[session_id]
    history = agent.get_history()

    return SessionInfo(
        session_id=session_id,
        message_count=len(history),
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return {"status": "deleted", "session_id": session_id}


@app.get("/sessions/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = sessions[session_id]
    return {"history": agent.get_history()}


@app.delete("/sessions/{session_id}/history")
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = sessions[session_id]
    agent.clear_history()
    return {"status": "cleared", "session_id": session_id}


# WebSocket endpoint for streaming
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming agent responses.

    Protocol:
    - Client sends: {"type": "message", "content": "user message"}
    - Server sends: {"type": "chunk", "content": "response chunk"}
    - Server sends: {"type": "tool_call", "name": "tool", "args": {...}}
    - Server sends: {"type": "done"}
    - Server sends: {"type": "error", "message": "error details"}
    """
    await websocket.accept()

    # Get or create agent for this session
    if session_id not in sessions:
        sessions[session_id] = CodingAgent(session_id=session_id)

    agent = sessions[session_id]

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("content", "")

                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message",
                    })
                    continue

                # Set workspace if provided
                if workspace := data.get("workspace"):
                    from src.tools.terminal import set_working_dir
                    from pathlib import Path
                    set_working_dir(Path(workspace).resolve())

                try:
                    # Stream response
                    for chunk in agent.run(content, stream=True):
                        if hasattr(chunk, 'content') and chunk.content:
                            await websocket.send_json({
                                "type": "chunk",
                                "content": chunk.content,
                            })

                        # Check for tool calls
                        if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                            for tool_call in chunk.tool_calls:
                                await websocket.send_json({
                                    "type": "tool_call",
                                    "name": tool_call.get("name", "unknown"),
                                    "args": tool_call.get("arguments", {}),
                                })

                    await websocket.send_json({"type": "done"})

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            elif data.get("type") == "clear_history":
                agent.clear_history()
                await websocket.send_json({
                    "type": "history_cleared",
                })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass


def run_server():
    """Run the server (for direct execution)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.api.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
    )


if __name__ == "__main__":
    run_server()
