"""
Chat session metadata store (SQLite).
Tracks session context: selected location, business type, analysis ID.
The LLM conversation state is managed by the ADK session service separately.
"""
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ChatSession, ChatMessage, ChatToolCall

logger = logging.getLogger(__name__)


async def create_session(
    db: AsyncSession,
    user_id: str = "anonymous",
    analysis_id: str | None = None,
) -> str:
    session_id = str(uuid.uuid4())
    session = ChatSession(
        id=session_id,
        user_id=user_id,
        analysis_id=analysis_id,
    )
    db.add(session)
    await db.commit()
    return session_id


async def get_session(db: AsyncSession, session_id: str) -> ChatSession | None:
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_session(
    db: AsyncSession,
    session_id: str,
    analysis_id: str | None = None,
    business_type: str | None = None,
    radius_km: float | None = None,
    location_query: str | None = None,
):
    session = await get_session(db, session_id)
    if not session:
        return
    if analysis_id is not None:
        session.analysis_id = analysis_id
    if business_type is not None:
        session.business_type = business_type
    if radius_km is not None:
        session.radius_km = radius_km
    if location_query is not None:
        session.location_query = location_query
    await db.commit()


async def save_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
) -> int:
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg.id


async def save_tool_call(
    db: AsyncSession,
    session_id: str,
    tool_name: str,
    tool_input: dict,
    tool_output: dict,
    status: str = "success",
):
    tc = ChatToolCall(
        session_id=session_id,
        tool_name=tool_name,
        tool_input_json=json.dumps(tool_input, default=str)[:4000],
        tool_output_json=json.dumps(tool_output, default=str)[:4000],
        status=status,
    )
    db.add(tc)
    await db.commit()


async def get_session_history(db: AsyncSession, session_id: str, limit: int = 50) -> list:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    msgs = result.scalars().all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None} for m in msgs]
