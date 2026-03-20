import io
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from ai import check_authorship_async
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    settings.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

results_store: Dict[str, dict] = {}


async def extract_text_from_file(file: UploadFile) -> str:
    content = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith('.pdf'):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as e:
            logger.warning(f"PDF extraction failed: {e}, falling back to raw decode")

    elif filename.endswith('.docx'):
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            return "\n".join(para.text for para in doc.paragraphs).strip()
        except Exception as e:
            logger.warning(f"DOCX extraction failed: {e}, falling back to raw decode")

    return content.decode('utf-8', errors='ignore').strip()


async def process_plagiarism_check(task_id: str, original_text: str, suspect_text: str):
    try:
        logger.info(f"Task {task_id}: starting analysis")
        result = await check_authorship_async(original_text, suspect_text)
        results_store[task_id] = {
            "status": "completed",
            "message": result,
            "created_at": datetime.now()
        }
        logger.info(f"Task {task_id}: completed ({len(result)} chars)")
    except Exception as e:
        logger.error(f"Task {task_id}: error - {e}", exc_info=True)
        results_store[task_id] = {
            "status": "completed",
            "message": settings.MESSAGES["system_unavailable"],
            "created_at": datetime.now()
        }


async def cleanup_old_tasks():
    cutoff = datetime.now() - timedelta(hours=settings.TASK_CLEANUP_HOURS)
    to_delete = [
        tid for tid, data in results_store.items()
        if data.get("created_at", datetime.now()) < cutoff
    ]
    for tid in to_delete:
        del results_store[tid]
    if to_delete:
        logger.info(f"Cleaned up {len(to_delete)} old tasks")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"CopyDetect API starting — model: {settings.AI_MODEL}")
    yield
    logger.info("CopyDetect API shutting down")


app = FastAPI(
    title="CopyDetect API",
    description="Plagiarism detection for Turkmen language texts",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "CopyDetect API", "version": "2.0.0", "model": settings.AI_MODEL}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": settings.AI_MODEL,
        "tasks_in_store": len(results_store),
    }


@app.post("/plagiarism-check/")
async def plagiarism_check(
    background_tasks: BackgroundTasks,
    original_text: str = Form(None),
    suspect_text: str = Form(None),
    original_file: UploadFile = File(None),
    suspect_file: UploadFile = File(None)
):
    task_id = str(uuid.uuid4())
    logger.info(f"New request: {task_id}")

    results_store[task_id] = {
        "status": "processing",
        "message": settings.MESSAGES["processing"],
        "created_at": datetime.now()
    }

    try:
        # Extract text from files if provided
        if original_file and original_file.filename and suspect_file and suspect_file.filename:
            if original_file.size and original_file.size > settings.MAX_FILE_SIZE_BYTES:
                raise HTTPException(400, settings.MESSAGES["file_too_large"].format(max_size=settings.MAX_FILE_SIZE_MB))
            if suspect_file.size and suspect_file.size > settings.MAX_FILE_SIZE_BYTES:
                raise HTTPException(400, settings.MESSAGES["file_too_large"].format(max_size=settings.MAX_FILE_SIZE_MB))

            original_text = await extract_text_from_file(original_file)
            suspect_text = await extract_text_from_file(suspect_file)

        if not original_text or not suspect_text:
            results_store[task_id]["status"] = "completed"
            results_store[task_id]["message"] = settings.MESSAGES["no_input"]
            return {"task_id": task_id, "status": "success", "message": settings.MESSAGES["accepted"]}

        if len(original_text) > settings.MAX_TEXT_LENGTH or len(suspect_text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(400, settings.MESSAGES["text_too_long"].format(max_length=settings.MAX_TEXT_LENGTH))

        background_tasks.add_task(process_plagiarism_check, task_id, original_text, suspect_text)
        background_tasks.add_task(cleanup_old_tasks)

        return {"task_id": task_id, "status": "success", "message": settings.MESSAGES["accepted"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task {task_id}: unexpected error: {e}", exc_info=True)
        return {"task_id": task_id, "status": "success", "message": settings.MESSAGES["accepted"]}


@app.get("/result/{task_id}")
async def get_result(task_id: str):
    if task_id not in results_store:
        return {"status": "not_found", "message": settings.MESSAGES["not_found"]}

    task = results_store[task_id]
    return {"status": task["status"], "message": task["message"]}


@app.delete("/admin/cleanup")
async def manual_cleanup():
    await cleanup_old_tasks()
    return {"status": "success", "remaining_tasks": len(results_store)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True, log_level="info")
