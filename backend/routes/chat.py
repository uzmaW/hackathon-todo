"""Chat and conversation routes."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from pydantic import BaseModel

from db import get_session
from auth import get_current_user
from models.user import User
from models.conversation import Conversation, ConversationCreate, ConversationRead
from models.message import Message, MessageCreate, MessageRead, MessageRole
from models.prompt import Prompt, PromptRead, PromptType
from utils.permissions import check_user_permission
from agent import run_task_agent
from config import get_settings

settings = get_settings()

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request schema."""
    conversation_id: Optional[int] = None
    message: str


class ChatResponse(BaseModel):
    """Chat response schema."""
    conversation_id: int
    response: str
    tool_calls: Optional[List[dict]] = None


class ConversationWithMessages(ConversationRead):
    """Conversation with messages."""
    messages: List[MessageRead] = []


# Conversation endpoints

@router.get("/conversations", response_model=List[ConversationRead])
async def list_conversations(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List conversations for the authenticated user."""
    query = select(Conversation).where(Conversation.user_id == current_user.id)

    if project_id:
        # Check user has access to project
        if not check_user_permission(session, current_user.id, project_id, "viewer"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )
        query = query.where(Conversation.project_id == project_id)

    query = query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
    conversations = session.exec(query).all()

    return [
        ConversationRead(
            id=c.id,
            title=c.title,
            user_id=c.user_id,
            project_id=c.project_id,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in conversations
    ]


@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    # Check project access if specified
    if data.project_id:
        if not check_user_permission(session, current_user.id, data.project_id, "viewer"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )

    conversation = Conversation(
        title=data.title,
        user_id=current_user.id,
        project_id=data.project_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    return ConversationRead(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        project_id=conversation.project_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a conversation with its messages."""
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Check ownership or project access
    if conversation.user_id != current_user.id:
        if conversation.project_id:
            if not check_user_permission(session, current_user.id, conversation.project_id, "viewer"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this conversation"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )

    # Get messages
    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    messages = session.exec(stmt).all()

    return ConversationWithMessages(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        project_id=conversation.project_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageRead(
                id=m.id,
                conversation_id=m.conversation_id,
                user_id=m.user_id,
                role=m.role,
                content=m.content,
                message_metadata=m.message_metadata,
                created_at=m.created_at
            )
            for m in messages
        ]
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageRead])
async def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a conversation (paginated)."""
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Check access
    if conversation.user_id != current_user.id:
        if conversation.project_id:
            if not check_user_permission(session, current_user.id, conversation.project_id, "viewer"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this conversation"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    messages = session.exec(stmt).all()

    return [
        MessageRead(
            id=m.id,
            conversation_id=m.conversation_id,
            user_id=m.user_id,
            role=m.role,
            content=m.content,
            message_metadata=m.message_metadata,
            created_at=m.created_at
        )
        for m in reversed(messages)  # Return in chronological order
    ]


# Chat endpoint

@router.post("/{user_id}/chat", response_model=ChatResponse)
async def chat(
    user_id: str,
    request: ChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the AI chat agent.

    The agent can call MCP tools to manage tasks.
    """
    # Verify user_id matches current user
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only chat as yourself"
        )

    # Get or create conversation
    if request.conversation_id:
        conversation = session.get(Conversation, request.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            title=request.message[:50] + ("..." if len(request.message) > 50 else ""),
            user_id=current_user.id,
            project_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    # Store user message
    user_message = Message(
        conversation_id=conversation.id,
        user_id=current_user.id,
        role=MessageRole.USER,
        content=request.message,
        created_at=datetime.utcnow()
    )
    session.add(user_message)

    # Get conversation history for context
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .limit(20)  # Last 20 messages for context
    )
    history_messages = session.exec(stmt).all()

    # Format history for the agent
    history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in history_messages
    ]

    # Run the AI agent
    if settings.openai_api_key:
        try:
            ai_response_text, tool_calls = await run_task_agent(
                session=session,
                user_id=current_user.id,
                message=request.message,
                project_id=conversation.project_id,
                history=history
            )
        except Exception as e:
            # Fallback if agent fails
            ai_response_text = f"I'm having trouble processing your request right now. Error: {str(e)}"
            tool_calls = []
    else:
        # No API key configured
        ai_response_text = "AI chat is not configured. Please set the OPENAI_API_KEY environment variable."
        tool_calls = []

    # Store AI response
    ai_message = Message(
        conversation_id=conversation.id,
        user_id=current_user.id,
        role=MessageRole.ASSISTANT,
        content=ai_response_text,
        message_metadata={"tool_calls": tool_calls} if tool_calls else None,
        created_at=datetime.utcnow()
    )
    session.add(ai_message)

    # Create prompt record
    prompt = Prompt(
        conversation_id=conversation.id,
        user_id=current_user.id,
        prompt_text=request.message,
        prompt_type=PromptType.GENERAL,
        ai_response=ai_response_text,
        tool_calls={"calls": tool_calls} if tool_calls else None,
        created_at=datetime.utcnow(),
        processed_at=datetime.utcnow()
    )
    session.add(prompt)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)

    session.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        response=ai_response_text,
        tool_calls=tool_calls if tool_calls else None
    )


# Prompt endpoints

@router.get("/prompts", response_model=List[PromptRead])
async def list_prompts(
    conversation_id: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List prompts for the authenticated user or conversation."""
    query = select(Prompt).where(Prompt.user_id == current_user.id)

    if conversation_id:
        # Verify conversation access
        conversation = session.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
        query = query.where(Prompt.conversation_id == conversation_id)

    query = query.order_by(Prompt.created_at.desc()).offset(offset).limit(limit)
    prompts = session.exec(query).all()

    return [
        PromptRead(
            id=p.id,
            conversation_id=p.conversation_id,
            user_id=p.user_id,
            prompt_text=p.prompt_text,
            prompt_type=p.prompt_type,
            ai_response=p.ai_response,
            tool_calls=p.tool_calls,
            created_at=p.created_at,
            processed_at=p.processed_at
        )
        for p in prompts
    ]


@router.get("/prompts/{prompt_id}", response_model=PromptRead)
async def get_prompt(
    prompt_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific prompt."""
    prompt = session.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )

    if prompt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this prompt"
        )

    return PromptRead(
        id=prompt.id,
        conversation_id=prompt.conversation_id,
        user_id=prompt.user_id,
        prompt_text=prompt.prompt_text,
        prompt_type=prompt.prompt_type,
        ai_response=prompt.ai_response,
        tool_calls=prompt.tool_calls,
        created_at=prompt.created_at,
        processed_at=prompt.processed_at
    )
