from fastapi import FastAPI, File, UploadFile, Form
from ai import check_authorship
app = FastAPI()  # Create an instance of FastAPI

@app.post("/plagiarism-check/")
async def plagiarism_check(
    original_text: str = Form(None),
    suspect_text: str = Form(None),
    original_file: UploadFile = File(None),
    suspect_file: UploadFile = File(None)):
    
    if original_text and suspect_text:
        message = check_authorship(original_text,suspect_text)
        return {"message": message}
    elif original_file and suspect_file:
        original_content = await original_file.read()
        suspect_content = await suspect_file.read()
        original_text = original_content.decode('utf-8', errors='ignore')
        suspect_text = suspect_content.decode('utf-8', errors='ignore')
        message = check_authorship(original_text, suspect_text)
        return {"message": message}
    else:
        return {"message": "No valid input provided."}
        