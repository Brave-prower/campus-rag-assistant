from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import time

from app.config import UPLOAD_DIR, MAX_UPLOAD_MB
from app.services.rag import index_document, count_documents

router = APIRouter()


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未收到文件")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 .pdf 格式")

    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"文件不能超过 {MAX_UPLOAD_MB}MB")

    safe_name = f"{int(time.time())}_{file.filename}"
    save_path: Path = UPLOAD_DIR / safe_name
    save_path.write_bytes(content)

    try:
        pages = index_document(save_path, file.filename, len(content))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 解析失败：{str(e)}")

    kb_info = count_documents()

    return {
        "name": file.filename,
        "size": len(content),
        "path": str(save_path),
        "pages": pages,
        "message": f"上传成功，已解析 {pages} 页并加入知识库",
        "kb_status": kb_info,
    }


@router.get("/documents")
async def list_documents():
    files = list(UPLOAD_DIR.glob("*"))
    kb_info = count_documents()
    return {
        "uploaded_count": len(files),
        "documents": [f.name for f in files],
        "knowledge_base": kb_info,
    }