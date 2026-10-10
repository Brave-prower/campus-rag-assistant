from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag import ask

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    page: int
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        answer, sources = ask(req.question)
    except RuntimeError as e:
        return ChatResponse(
            answer=f"⚠️ 配置问题：{str(e)}",
            sources=[],
        )
    except Exception as e:
        return ChatResponse(
            answer=f"❌ 系统错误：{str(e)}",
            sources=[],
        )
    return ChatResponse(answer=answer, sources=sources)