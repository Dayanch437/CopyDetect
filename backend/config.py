import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:

    API_KEY: str = os.getenv("API_KEY", os.getenv("GEMINI_API_KEY", ""))

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://localhost,http://213.21.235.119:8000,http://213.21.235.119:8001"
    ).split(",")

    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "50000"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    TASK_CLEANUP_HOURS: int = int(os.getenv("TASK_CLEANUP_HOURS", "24"))

    AI_MODEL: str = "gemma-3-27b-it"

    MAX_RETRIES: int = 3
    RETRY_DELAYS: List[int] = [3, 7, 15]

    MESSAGES = {
        "processing": "Barlag geçirilýär...",
        "no_input": "Maglumat girizilmedi. Tekst ýazyň ýa-da faýl saýlaň.",
        "accepted": "Haýyşnamaňyz kabul edildi. Netijäni görmek üçin ID belgiňizi saklaň.",
        "not_found": "Netije tapylmady.",
        "text_too_long": "Tekst örän uzyn. Iň köp rugsat edilen: {max_length} harp.",
        "file_too_large": "Faýl örän uly. Iň uly rugsat edilen ölçeg: {max_size}MB.",
        "system_busy": "Ulgam häzir gaty köp haýyşnama alýar. Biraz wagtdan gaýtadan synanyşyň.",
        "system_unavailable": "Ulgamda näsazlyk ýüze çykdy. Biraz wagtdan soňra gaýtadan synanyşyň.",
        "analysis_complete": "Barlag tamamlandy.",
    }

    @classmethod
    def validate(cls):
        if not cls.API_KEY:
            raise ValueError("API_KEY (or GEMINI_API_KEY) is not set in environment variables")
        return True

settings = Settings()
