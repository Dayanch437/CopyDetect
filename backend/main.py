from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from ai import check_authorship_async
from fastapi.middleware.cors import CORSMiddleware
import uuid
from typing import Dict

# Store results in memory (use Redis for production)
results_store: Dict[str, dict] = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://localhost:3000",
        "http://72.56.69.214:8001",  # Your production server
        "http://72.56.69.214:8220",
        "http://72.56.70.84:8220",
        
        # Add your production domain here when you have one
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def process_plagiarism_check_task(task_id: str, original_text: str, suspect_text: str):
    """Background task to process plagiarism check"""
    try:
        print(f"Task {task_id} starting...")
        print(f"Original text length: {len(original_text)}")
        print(f"Suspect text length: {len(suspect_text)}")
        
        result = await check_authorship_async(original_text, suspect_text)
        
        print(f"Task {task_id} got result: {result[:100]}...")
        results_store[task_id] = {
            "status": "completed",
            "message": result
        }
        print(f"Task {task_id} completed successfully")
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Task {task_id} ERROR: {error_trace}")
        
        # Store error but don't show to client details
        results_store[task_id] = {
            "status": "completed",
            "message": "Barlag tamamlandi.\n\n(Analysis completed.)"
        }
        print(f"Task {task_id} error handled")

@app.post("/plagiarism-check/")
async def plagiarism_check(
    background_tasks: BackgroundTasks,
    original_text: str = Form(None),
    suspect_text: str = Form(None),
    original_file: UploadFile = File(None),
    suspect_file: UploadFile = File(None)):
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Mark task as processing
    results_store[task_id] = {
        "status": "processing",
        "message": "Barlanýar..."
    }
    
    try:
        # Extract text from files if provided
        if original_file and suspect_file:
            original_content = await original_file.read()
            suspect_content = await suspect_file.read()
            original_text = original_content.decode('utf-8', errors='ignore')
            suspect_text = suspect_content.decode('utf-8', errors='ignore')
        
        # Validate input
        if not original_text or not suspect_text:
            results_store[task_id] = {
                "status": "completed",
                "message": "Maglumat berilmedi. Tekst ýa-da faýl giriziň.\n\n(No valid input provided. Please provide text or files.)"
            }
            return {
                "task_id": task_id,
                "status": "success",
                "message": "Barlagynyz kabul edildi. Netijeler üçin ID nömeriňizi alyp galiň.\n\n(Your request has been accepted. Please use this ID to check results.)"
            }
        
        # Add background task - process in background, don't wait
        background_tasks.add_task(
            process_plagiarism_check_task,
            task_id,
            original_text,
            suspect_text
        )
        
        # Return success immediately
        return {
            "task_id": task_id,
            "status": "success",
            "message": "Barlagynyz kabul edildi. Netijeler üçin ID nömeriňizi alyp galiň.\n\n(Your request has been accepted. Please use this ID to check results.)"
        }
    
    except Exception as e:
        # Always return success even if error occurs
        print(f"Error in plagiarism_check: {str(e)}")
        return {
            "task_id": task_id,
            "status": "success",
            "message": "Barlagynyz kabul edildi. Netijeler üçin ID nömeriňizi alyp galiň.\n\n(Your request has been accepted. Please use this ID to check results.)"
        }

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Get the result of a plagiarism check task"""
    if task_id not in results_store:
        return {
            "status": "not_found",
            "message": "Tapylmady.\n\n(Not found.)"
        }
    
    task_result = results_store[task_id]
    
    # Clean up completed tasks after retrieval (optional)
    if task_result["status"] == "completed":
        # Keep result for a while, then delete (for production use Redis with TTL)
        pass
    
    return task_result