from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json
from typing import List, Optional
from config import settings

Base = declarative_base()

class CallRecord(Base):
    __tablename__ = "call_records"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float)
    risk_score = Column(Float)
    risk_level = Column(String)  # safe, suspicious, scam
    transcript = Column(Text)
    caller_info = Column(String)
    scam_indicators = Column(Text)  # JSON string
    voice_spoofing_detected = Column(Boolean, default=False)
    spoofing_confidence = Column(Float)
    language_detected = Column(String)
    audio_file_path = Column(String, nullable=True)

class ScamPattern(Base):
    __tablename__ = "scam_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    language = Column(String, index=True)
    pattern = Column(String)
    category = Column(String)  # urgency, personal_info, pressure, etc.
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class VoicePrint(Base):
    __tablename__ = "voice_prints"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    contact_name = Column(String)
    voice_embedding = Column(Text)  # JSON string of voice features
    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime)

# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseManager:
    def __init__(self):
        create_tables()
    
    def save_call_record(self, call_data: dict) -> CallRecord:
        db = SessionLocal()
        try:
            record = CallRecord(
                client_id=call_data.get("client_id"),
                duration=call_data.get("duration", 0),
                risk_score=call_data.get("risk_score", 0),
                risk_level=call_data.get("risk_level", "safe"),
                transcript=call_data.get("transcript", ""),
                caller_info=call_data.get("caller_info", "Unknown"),
                scam_indicators=json.dumps(call_data.get("scam_indicators", [])),
                voice_spoofing_detected=call_data.get("voice_spoofing_detected", False),
                spoofing_confidence=call_data.get("spoofing_confidence", 0),
                language_detected=call_data.get("language_detected", "unknown"),
                audio_file_path=call_data.get("audio_file_path")
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        finally:
            db.close()
    
    def get_call_history(self, client_id: str, limit: int = 50) -> List[CallRecord]:
        db = SessionLocal()
        try:
            return db.query(CallRecord).filter(
                CallRecord.client_id == client_id
            ).order_by(CallRecord.timestamp.desc()).limit(limit).all()
        finally:
            db.close()
    
    def add_scam_pattern(self, language: str, pattern: str, category: str, weight: float = 1.0):
        db = SessionLocal()
        try:
            scam_pattern = ScamPattern(
                language=language,
                pattern=pattern,
                category=category,
                weight=weight
            )
            db.add(scam_pattern)
            db.commit()
        finally:
            db.close()
    
    def get_scam_patterns(self, language: str) -> List[ScamPattern]:
        db = SessionLocal()
        try:
            return db.query(ScamPattern).filter(
                ScamPattern.language == language
            ).all()
        finally:
            db.close()

# Global database manager
db_manager = DatabaseManager()
