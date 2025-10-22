from fastapi import FastAPI, File, UploadFile, Form, Request
from ai import check_authorship_async
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()  # Create an instance of FastAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/plagiarism-check/")
@limiter.limit("3/minute")  # Limit to 3 requests per minute to avoid overloading API
async def plagiarism_check(
    request: Request,
    original_text: str = Form(None),
    suspect_text: str = Form(None),
    original_file: UploadFile = File(None),
    suspect_file: UploadFile = File(None)):
    
    if original_text and suspect_text:
        message = await check_authorship_async(original_text, suspect_text)
        return {"message": message}
    elif original_file and suspect_file:
        original_content = await original_file.read()
        suspect_content = await suspect_file.read()
        original_text = original_content.decode('utf-8', errors='ignore')
        suspect_text = suspect_content.decode('utf-8', errors='ignore')
        message = await check_authorship_async(original_text, suspect_text)
        return {"message": message}
    else:
        return {"message": "Maglumat berilmedi. Tekst ýa-da faýl giriziň. (No valid input provided. Please provide text or files.)"}