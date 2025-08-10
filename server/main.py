from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import asyncio
import json
import logging
from typing import Dict, List
import uuid
from datetime import datetime
import time

from config import settings, logger
from audio_processor import AudioProcessor
from scam_detector import ScamDetector
from voice_analyzer import VoiceAnalyzer
from tts_alerts import TTSAlerts
from database import db_manager, CallRecord
from monitoring import performance_monitor, monitor_performance

app = FastAPI(
    title="VoiceSentinel API", 
    version="2.0.0",
    description="Advanced AI-powered voice scam detection system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize AI components
audio_processor = AudioProcessor()
scam_detector = ScamDetector()
voice_analyzer = VoiceAnalyzer()
tts_alerts = TTSAlerts()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_sessions: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_sessions[client_id] = {
            "start_time": datetime.utcnow(),
            "transcript_segments": [],
            "risk_scores": [],
            "total_chunks": 0
        }
        performance_monitor.track_connection(True)
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
            # Save session data to database
            if client_id in self.client_sessions:
                self._save_session_data(client_id)
                del self.client_sessions[client_id]
            
            # Cleanup audio buffer
            audio_processor.cleanup_client_buffer(client_id)
            
            performance_monitor.track_connection(False)
            logger.info(f"Client {client_id} disconnected")

    def _save_session_data(self, client_id: str):
        """Save session data to database"""
        try:
            session = self.client_sessions[client_id]
            
            if session["total_chunks"] > 0:  # Only save if there was activity
                call_data = {
                    "client_id": client_id,
                    "duration": (datetime.utcnow() - session["start_time"]).total_seconds(),
                    "risk_score": max(session["risk_scores"]) if session["risk_scores"] else 0,
                    "risk_level": self._get_risk_level(max(session["risk_scores"]) if session["risk_scores"] else 0),
                    "transcript": " ".join([seg.get("text", "") for seg in session["transcript_segments"]]),
                    "caller_info": "Unknown",
                    "scam_indicators": [seg.get("indicators", []) for seg in session["transcript_segments"]],
                    "voice_spoofing_detected": any(seg.get("voice_spoofing", False) for seg in session["transcript_segments"]),
                    "spoofing_confidence": max([seg.get("spoofing_confidence", 0) for seg in session["transcript_segments"]] or [0]),
                    "language_detected": session["transcript_segments"][-1].get("language", "unknown") if session["transcript_segments"] else "unknown"
                }
                
                db_manager.save_call_record(call_data)
                logger.info(f"Saved session data for client {client_id}")
                
        except Exception as e:
            logger.error(f"Error saving session data for {client_id}: {e}")

    def _get_risk_level(self, score: float) -> str:
        if score >= 70:
            return "scam"
        elif score >= 40:
            return "suspicious"
        else:
            return "safe"

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

@app.get("/")
async def root():
    performance_monitor.track_api_request("/", "GET")
    return {
        "message": "VoiceSentinel API v2.0",
        "status": "operational",
        "features": [
            "Real-time voice analysis",
            "Multi-language scam detection", 
            "Voice spoofing detection",
            "TTS alerts",
            "Call history tracking"
        ]
    }

@app.get("/health")
async def health_check():
    performance_monitor.track_api_request("/health", "GET")
    
    # Check component health
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time() - performance_monitor.start_time,
        "active_connections": len(manager.active_connections),
        "components": {
            "audio_processor": "ready",
            "scam_detector": "ready", 
            "voice_analyzer": "ready",
            "tts_alerts": "ready",
            "database": "ready"
        },
        "configuration": {
            "whisper_model": settings.WHISPER_MODEL,
            "sample_rate": settings.SAMPLE_RATE,
            "max_connections": settings.MAX_CONCURRENT_CONNECTIONS,
            "openai_enabled": bool(settings.OPENAI_API_KEY),
            "elevenlabs_enabled": bool(settings.ELEVENLABS_API_KEY)
        }
    }
    
    return health_status

@app.get("/history/{client_id}")
async def get_call_history(client_id: str, limit: int = 50):
    """Get call history for a client"""
    performance_monitor.track_api_request("/history", "GET")
    
    try:
        records = db_manager.get_call_history(client_id, limit)
        return {
            "client_id": client_id,
            "total_calls": len(records),
            "calls": [
                {
                    "id": record.id,
                    "timestamp": record.timestamp.isoformat(),
                    "duration": record.duration,
                    "risk_score": record.risk_score,
                    "risk_level": record.risk_level,
                    "transcript": record.transcript[:200] + "..." if len(record.transcript) > 200 else record.transcript,
                    "caller_info": record.caller_info,
                    "language": record.language_detected,
                    "voice_spoofing": record.voice_spoofing_detected
                }
                for record in records
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving call history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve call history")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio_chunk":
                await process_audio_chunk(message["data"], client_id)
            
            elif message["type"] == "start_analysis":
                await manager.send_personal_message({
                    "type": "analysis_started",
                    "message": "Voice analysis started",
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
            
            elif message["type"] == "stop_analysis":
                await manager.send_personal_message({
                    "type": "analysis_stopped", 
                    "message": "Voice analysis stopped",
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        performance_monitor.track_error("websocket", type(e).__name__)
        manager.disconnect(client_id)

@monitor_performance("audio_processing")
async def process_audio_chunk(audio_data: str, client_id: str):
    """Enhanced audio processing with comprehensive analysis"""
    try:
        performance_monitor.track_audio_chunk()
        
        # Update session
        if client_id in manager.client_sessions:
            manager.client_sessions[client_id]["total_chunks"] += 1
        
        # 1. Voice Activity Detection + Speaker Diarization
        vad_result = await audio_processor.process_vad(audio_data, client_id)
        
        if not vad_result["has_speech"]:
            return
        
        # 2. Real-time Transcription
        transcript_result = await audio_processor.transcribe_chunk(
            audio_data, client_id, language="auto"
        )
        
        if not transcript_result["text"].strip():
            return
        
        # 3. Scam Detection
        scam_result = await scam_detector.analyze_text(
            transcript_result["text"],
            transcript_result["language"]
        )
        
        # 4. Voice Anti-Spoofing
        voice_result = await voice_analyzer.detect_spoofing(audio_data)
        
        # 5. Calculate combined risk score
        risk_score = calculate_risk_score(scam_result, voice_result)
        
        # Track metrics
        risk_level = get_risk_level(risk_score)
        performance_monitor.track_scam_detection(risk_level)
        
        if voice_result["is_spoofed"]:
            performance_monitor.track_voice_spoofing()
        
        # Update session data
        if client_id in manager.client_sessions:
            session = manager.client_sessions[client_id]
            session["transcript_segments"].append({
                "text": transcript_result["text"],
                "language": transcript_result["language"],
                "risk_score": risk_score,
                "indicators": scam_result["indicators"],
                "voice_spoofing": voice_result["is_spoofed"],
                "spoofing_confidence": voice_result["confidence"]
            })
            session["risk_scores"].append(risk_score)
        
        # 6. Send results to client
        response = {
            "type": "analysis_result",
            "timestamp": datetime.utcnow().isoformat(),
            "transcript": {
                "text": transcript_result["text"],
                "speaker": vad_result["speaker"],
                "language": transcript_result["language"],
                "confidence": transcript_result["confidence"]
            },
            "risk_assessment": {
                "score": risk_score,
                "level": risk_level,
                "scam_indicators": scam_result["indicators"][:5],  # Limit indicators
                "voice_spoofing": voice_result["is_spoofed"],
                "spoofing_confidence": voice_result["confidence"]
            },
            "audio_quality": {
                "level": vad_result["audio_level"],
                "quality_score": vad_result.get("quality_score", 0)
            },
            "processing_metrics": {
                "scam_confidence": scam_result.get("confidence", 0),
                "voice_confidence": voice_result["confidence"],
                "processing_time": scam_result.get("processing_time", 0) + voice_result.get("processing_time", 0)
            }
        }
        
        await manager.send_personal_message(response, client_id)
        
        # 7. Generate TTS alert if high risk
        if risk_score > 70:
            alert_audio = await tts_alerts.generate_alert(
                risk_score, 
                transcript_result["language"],
                indicators=scam_result["indicators"]
            )
            
            if alert_audio:
                performance_monitor.track_tts_alert(transcript_result["language"])
                await manager.send_personal_message({
                    "type": "audio_alert",
                    "audio_data": alert_audio,
                    "message": f"High risk detected: {risk_score:.0f}%",
                    "alert_level": risk_level
                }, client_id)
            
    except Exception as e:
        logger.error(f"Error processing audio chunk: {str(e)}")
        performance_monitor.track_error("audio_processing", type(e).__name__)
        await manager.send_personal_message({
            "type": "error",
            "message": f"Processing error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)

def calculate_risk_score(scam_result: dict, voice_result: dict) -> float:
    """Enhanced risk score calculation"""
    scam_score = scam_result["risk_score"]
    voice_score = voice_result["spoofing_score"]
    
    # Base weighted combination
    base_score = (scam_score * 0.7) + (voice_score * 0.3)
    
    # Amplify if both are high
    if scam_score > 60 and voice_score > 60:
        base_score *= 1.2
    
    # Consider confidence levels
    scam_confidence = scam_result.get("confidence", 50) / 100
    voice_confidence = voice_result["confidence"] / 100
    avg_confidence = (scam_confidence + voice_confidence) / 2
    
    # Adjust score based on confidence
    final_score = base_score * (0.7 + 0.3 * avg_confidence)
    
    return min(100.0, max(0.0, final_score))

def get_risk_level(score: float) -> str:
    """Convert risk score to level"""
    if score >= 70:
        return "scam"
    elif score >= 40:
        return "suspicious"
    else:
        return "safe"

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting VoiceSentinel API server...")
    logger.info(f"Configuration: Whisper={settings.WHISPER_MODEL}, OpenAI={'✓' if settings.OPENAI_API_KEY else '✗'}, ElevenLabs={'✓' if settings.ELEVENLABS_API_KEY else '✗'}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )
