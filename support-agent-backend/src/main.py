from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env.local"  # User .env.local for local development

# Explicitly load the .env file from the root folder
load_dotenv(dotenv_path=dotenv_path)

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent.graph import init_agent
from schemas import ChatRequest, ChatResponse, Token, UserCreate, UserLogin, UserResponse
from core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from db.database import get_db, init_db
from db.models import Conversation, Message, User
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    agent_graph, pool, checkpointer = await init_agent()
    
    # Store references on app state for endpoint handlers
    app.state.agent_graph = agent_graph
    app.state.pool = pool
    app.state.checkpointer = checkpointer
    yield
    
    # App Shutdown
    await app.state.pool.close()

app = FastAPI(title="AI Customer Support Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-support-agent-swart-xi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows Authorization, Content-Type, etc.
)

security = HTTPBearer()

@app.get("/api/health", status_code=status.HTTP_200_OK)
async def root():
    return {
        "message": "Welcome to the AI Customer Support API",
        "status": "online",
        "docs_url": "/docs"
    }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    db_user = User(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@app.post("/api/auth/login", response_model=Token)
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()

    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=db_user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/messages", response_model=list)
async def get_user_messages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        }
        for msg in messages
    ]


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat_req: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    thread_id = f"user-{current_user.id}"
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == current_user.id,
            Conversation.thread_id == thread_id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if conversation is None:
        # Create default conversation
        conversation = Conversation(
            user_id=current_user.id,
            thread_id=f"user-{current_user.id}",
            title="Chat History"
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_req.message
    )
    db.add(user_message)
    await db.commit()
    
    # Get AI response
    inputs = {
        "messages": [HumanMessage(content=chat_req.message)],
        "user_id": current_user.id,
    }
    config = {"configurable": {"thread_id": conversation.thread_id}}
    
    agent_graph = request.app.state.agent_graph
    result = await agent_graph.ainvoke(inputs, config=config)
    
    raw_content = result["messages"][-1].content
    
    if isinstance(raw_content, list):
        final_message = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in raw_content
        )
    else:
        final_message = str(raw_content)
    
    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=final_message
    )
    db.add(assistant_message)
    await db.commit()

    return ChatResponse(
        response=final_message,
        thread_id=conversation.thread_id
    )