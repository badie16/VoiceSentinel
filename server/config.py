import os
from typing import Optional
from pydantic import BaseSettings
import logging

class Settings(BaseSettings):
    # API Keys
    ELEVENLABS_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./voicesentinel.db"
    
    # Audio Processing
    SAMPLE_RATE: int = 16000
    CHUNK_DURATION: float = 1.0  # seconds
    MAX_AUDIO_BUFFER: int = 10   # seconds
    
    # AI Models
    WHISPER_MODEL: str = "base"
    SCAM_DETECTION_THRESHOLD: float = 0.6
    VOICE_SPOOFING_THRESHOLD: float = 0.5
    
    # Performance
    MAX_CONCURRENT_CONNECTIONS: int = 50
    PROCESSING_TIMEOUT: float = 30.0
    CACHE_SIZE: int = 1000
    
    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("voicesentinel.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
