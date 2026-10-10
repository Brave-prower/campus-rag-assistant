from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload, chat

app = FastAPI(
    title="校园教务 RAG 问答助手",
    description="湖南科技职业学院 · 基于规章制度 PDF 的智能问答后端",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "campus-rag-backend"}