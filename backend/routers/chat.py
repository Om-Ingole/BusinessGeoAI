"""
Chat API router — POST /api/chat/session and POST /api/chat/message.
All Google ADK / Gemini calls happen here; credentials never reach the frontend.
"""
import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    ToolCallSummary,
)
from agents import session_store

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_TOOL_CALLS = int(os.getenv("ADK_MAX_TOOL_CALLS", "8"))
MAX_CHARS = int(os.getenv("ADK_MAX_CONTEXT_REPORT_CHARS", "30000"))

SUGGESTED_ACTIONS = [
    "Is this good for retail?",
    "Find competitors",
    "Explain the score",
    "Compare another area",
    "Run 2 km radius",
    "Top risks",
    "Best business here?",
]


def _get_runner_or_503():
    try:
        from agents.location_agent import get_runner
        return get_runner()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ── Session management ────────────────────────────────────────────────────────

@router.post("/chat/session", response_model=CreateSessionResponse)
async def create_chat_session(
    req: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    import uuid
    _get_runner_or_503()  # validates ADK is available; raises 503 if not
    from agents.location_agent import get_session_service
    session_service = get_session_service()

    session_id = str(uuid.uuid4())

    # create_session is async in ADK 2.x
    try:
        await session_service.create_session(
            app_name="location_intel",
            user_id=req.user_id or "anonymous",
            session_id=session_id,
        )
    except Exception as e:
        logger.warning(f"ADK session creation failed: {e}")

    # Persist metadata in SQLite
    await session_store.create_session(
        db,
        user_id=req.user_id or "anonymous",
        analysis_id=req.analysis_id,
    )
    # Use the ADK session_id as the record primary key by re-saving
    # (session_store.create_session generates its own UUID; we use the ADK one)
    from models import ChatSession
    existing = await session_store.get_session(db, session_id)
    if not existing:
        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as fresh_db:
            s = ChatSession(
                id=session_id,
                user_id=req.user_id or "anonymous",
                analysis_id=req.analysis_id,
            )
            fresh_db.add(s)
            await fresh_db.commit()

    return CreateSessionResponse(session_id=session_id, analysis_id=req.analysis_id)


# ── Message ───────────────────────────────────────────────────────────────────

@router.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    req: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    runner = _get_runner_or_503()

    # Validate session exists
    session = await session_store.get_session(db, req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build context prefix from current report if provided
    context_prefix = ""
    if req.current_report:
        from services.agent_service import summarize_report_for_agent
        context_prefix = (
            "CURRENT REPORT CONTEXT (use this as ground truth for this conversation):\n"
            + summarize_report_for_agent(req.current_report, max_chars=MAX_CHARS)
            + "\n\nUSER QUESTION:\n"
        )

    full_message = context_prefix + req.message

    # Save user message
    await session_store.save_message(db, req.session_id, "user", req.message)

    # Run ADK agent
    response_text = ""
    tool_calls: list[ToolCallSummary] = []
    updated_report: dict | None = None
    warnings: list[str] = []
    tool_call_count = 0

    try:
        try:
            from google.genai import types as genai_types
        except ImportError:
            from google.ai import types as genai_types  # older SDK path

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=full_message)],
        )

        async for event in runner.run_async(
            user_id=req.user_id or "anonymous",
            session_id=req.session_id,
            new_message=content,
        ):
            # Collect tool use events
            if hasattr(event, "tool_use") and event.tool_use:
                tu = event.tool_use
                tool_name = getattr(tu, "name", "unknown")
                tool_call_count += 1
                if tool_call_count > MAX_TOOL_CALLS:
                    warnings.append("Tool call limit reached; some lookups were skipped")
                    break

                status = "success"
                try:
                    # Check if this tool returned a new analysis
                    tool_result = getattr(event, "tool_result", None)
                    if tool_result and tool_name in ("analyze_location_tool", "compare_locations_tool"):
                        result_data = getattr(tool_result, "output", None)
                        if isinstance(result_data, dict) and "viability_score" in result_data:
                            updated_report = result_data
                            # Update session with new analysis_id
                            aid = result_data.get("_analysis_id")
                            if aid:
                                await session_store.update_session(db, req.session_id, analysis_id=aid)
                except Exception:
                    pass

                tool_calls.append(ToolCallSummary(name=tool_name, status=status))

            # Collect final text response
            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text

    except Exception as e:
        logger.error(f"ADK run_async error: {e}")
        response_text = "I encountered an error processing your request. Please try again."
        warnings.append(str(e))

    if not response_text:
        response_text = "I couldn't generate a response. Please rephrase your question."

    # Save assistant message
    await session_store.save_message(db, req.session_id, "assistant", response_text)

    return ChatMessageResponse(
        message=response_text,
        tool_calls=tool_calls,
        updated_report=updated_report,
        suggested_actions=SUGGESTED_ACTIONS[:5],
        warnings=warnings,
    )


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/chat/session/{session_id}/history")
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await session_store.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    history = await session_store.get_session_history(db, session_id)
    return {"session_id": session_id, "messages": history}
