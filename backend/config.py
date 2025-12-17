"""
Configuration management for CopyDetect backend
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://213.21.235.119:8000"
    ).split(",")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    
    # Text Processing Limits
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "50000"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Task Management
    TASK_CLEANUP_HOURS: int = int(os.getenv("TASK_CLEANUP_HOURS", "24"))
    
    # AI Models
    AI_MODELS: List[str] = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAYS: List[int] = [3, 7, 15]  # seconds
    
    # Messages (Turkmen/English)
    MESSAGES = {
        "processing": "Barlanýar...",
        "no_input": "Maglumat berilmedi. Tekst ýa-da faýl giriziň.\n\n(No valid input provided. Please provide text or files.)",
        "accepted": "Barlagynyz kabul edildi. Netijeler üçin ID nömeriňizi alyp galiň.\n\n(Your request has been accepted. Please use this ID to check results.)",
        "not_found": "Tapylmady.\n\n(Not found.)",
        "text_too_long": "Tekst gaty uzyn. Maksimum: {max_length} simwol.\n\n(Text too long. Maximum: {max_length} characters.)",
        "file_too_large": "Faýl gaty uly. Maksimum: {max_size}MB.\n\n(File too large. Maximum: {max_size}MB.)",
        "system_busy": "Ulgam häzirki wagtda işjeň ulanylyp dur. Birazdan täzeden synanyşyň.\n\n(The system is currently busy. Please try again in a few moments.)",
        "system_unavailable": "Ulgam häzirki wagtda elýeterli däl. Biraz wagtdan soň täzeden synanyşyň.\n\n(System is currently unavailable. Please try again in a few moments.)",
        "analysis_complete": "Barlag tamamlandi.\n\n(Analysis completed.)",
        "rate_limit": "Aşa köp haýyş. Birazdan täzeden synanyşyň.\n\n(Too many requests. Please try again in a few moments.)"
    }
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        return True

# Create settings instance
settings = Settings()
