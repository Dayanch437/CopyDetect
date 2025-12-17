"""
CopyDetect Backend - Plagiarism Detection API
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ai import check_authorship_async
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate configuration
try:
    settings.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Store results in memory (use Redis for production)
results_store: Dict[str, dict] = {}

# Initialize FastAPI app
app = FastAPI(
    title="CopyDetect API",
    description="Plagiarism detection for Turkmen language texts",
    version="1.0.0"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_plagiarism_check_task(task_id: str, original_text: str, suspect_text: str):
    """Background task to process plagiarism check"""
    try:
        logger.info(f"Task {task_id} starting...")
        logger.debug(f"Original text length: {len(original_text)}, Suspect text length: {len(suspect_text)}")
        
        result = await check_authorship_async(original_text, suspect_text)
        
        logger.debug(f"Task {task_id} got result: {result[:100]}...")
        results_store[task_id] = {
            "status": "completed",
            "message": result,
            "created_at": datetime.now()
        }
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} ERROR: {e}", exc_info=True)
        
        # Store generic completion message on error
        results_store[task_id] = {
            "status": "completed",
            "message": settings.MESSAGES["analysis_complete"],
            "created_at": datetime.now()
        }
        logger.info(f"Task {task_id} error handled gracefully")


def validate_text_input(text: str, field_name: str) -> None:
    """Validate text input length"""
    if len(text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=settings.MESSAGES["text_too_long"].format(max_length=settings.MAX_TEXT_LENGTH)
        )


def validate_file_size(file: UploadFile) -> None:
    """Validate file size"""
    # Note: This is a basic check; for production, stream file and check size during read
    if file.size and file.size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=settings.MESSAGES["file_too_large"].format(max_size=settings.MAX_FILE_SIZE_MB)
        )


async def cleanup_old_tasks():
    """Clean up tasks older than TASK_CLEANUP_HOURS"""
    cutoff_time = datetime.now() - timedelta(hours=settings.TASK_CLEANUP_HOURS)
    tasks_to_delete = [
        task_id for task_id, task_data in results_store.items()
        if task_data.get("created_at", datetime.now()) < cutoff_time
    ]
    
    for task_id in tasks_to_delete:
        del results_store[task_id]
    
    if tasks_to_delete:
        logger.info(f"Cleaned up {len(tasks_to_delete)} old tasks")


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("CopyDetect API starting up...")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("CopyDetect API shutting down...")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "CopyDetect API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tasks_in_store": len(results_store),
        "api_configured": bool(settings.GEMINI_API_KEY)
    }


@app.post("/plagiarism-check/")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def plagiarism_check(
    request: Request,
    background_tasks: BackgroundTasks,
    original_text: str = Form(None),
    suspect_text: str = Form(None),
    original_file: UploadFile = File(None),
    suspect_file: UploadFile = File(None)
):
    """
    Submit a plagiarism check request
    
    Args:
        original_text: Original Turkmen text (optional if file provided)
        suspect_text: Suspect Turkmen text (optional if file provided)
        original_file: Original text file (optional if text provided)
        suspect_file: Suspect text file (optional if text provided)
        
    Returns:
        Task ID for checking results later
    """
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    logger.info(f"New plagiarism check request: {task_id}")
    
    # Mark task as processing
    results_store[task_id] = {
        "status": "processing",
        "message": settings.MESSAGES["processing"],
        "created_at": datetime.now()
    }
    
    try:
        # Extract text from files if provided
        if original_file and suspect_file:
            logger.debug(f"Task {task_id}: Processing files")
            
            # Validate file sizes
            validate_file_size(original_file)
            validate_file_size(suspect_file)
            
            original_content = await original_file.read()
            suspect_content = await suspect_file.read()
            original_text = original_content.decode('utf-8', errors='ignore')
            suspect_text = suspect_content.decode('utf-8', errors='ignore')
        
        # Validate input
        if not original_text or not suspect_text:
            logger.warning(f"Task {task_id}: No valid input provided")
            results_store[task_id] = {
                "status": "completed",
                "message": settings.MESSAGES["no_input"],
                "created_at": datetime.now()
            }
            return {
                "task_id": task_id,
                "status": "success",
                "message": settings.MESSAGES["accepted"]
            }
        
        # Validate text lengths
        validate_text_input(original_text, "original_text")
        validate_text_input(suspect_text, "suspect_text")
        
        # Add background task
        background_tasks.add_task(
            process_plagiarism_check_task,
            task_id,
            original_text,
            suspect_text
        )
        
        # Schedule cleanup task
        background_tasks.add_task(cleanup_old_tasks)
        
        logger.info(f"Task {task_id}: Accepted and queued for processing")
        
        # Return success immediately
        return {
            "task_id": task_id,
            "status": "success",
            "message": settings.MESSAGES["accepted"]
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    
    except Exception as e:
        # Log unexpected errors but return success to user
        logger.error(f"Task {task_id}: Unexpected error: {e}", exc_info=True)
        return {
            "task_id": task_id,
            "status": "success",
            "message": settings.MESSAGES["accepted"]
        }


@app.get("/result/{task_id}")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE * 2}/minute")  # Higher limit for result checks
async def get_result(request: Request, task_id: str):
    """
    Get the result of a plagiarism check task
    
    Args:
        task_id: The unique task ID returned by /plagiarism-check/
        
    Returns:
        Task status and results (if completed)
    """
    logger.debug(f"Result request for task: {task_id}")
    
    if task_id not in results_store:
        logger.warning(f"Task {task_id}: Not found")
        return {
            "status": "not_found",
            "message": settings.MESSAGES["not_found"]
        }
    
    task_result = results_store[task_id]
    
    return {
        "status": task_result["status"],
        "message": task_result["message"]
    }


@app.delete("/admin/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of old tasks (admin endpoint)"""
    await cleanup_old_tasks()
    return {
        "status": "success",
        "message": "Cleanup completed",
        "remaining_tasks": len(results_store)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )
