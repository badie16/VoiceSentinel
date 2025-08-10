from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Dict, List
import uuid
from datetime import datetime

from audio_processor import AudioProcessor
from scam_detector import ScamDetector
from voice_analyzer import VoiceAnalyzer
from tts_alerts import TTSAlerts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VoiceSentinel API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI components
audio_processor = AudioProcessor()
scam_detector = ScamDetector()
voice_analyzer = VoiceAnalyzer()
tts_alerts = TTSAlerts()

# Active connections
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "VoiceSentinel API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "audio_processor": "ready",
            "scam_detector": "ready",
            "voice_analyzer": "ready",
            "tts_alerts": "ready"
        }
    }

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio_chunk":
                # Process audio chunk
                await process_audio_chunk(message["data"], client_id)
            
            elif message["type"] == "start_analysis":
                await manager.send_personal_message({
                    "type": "analysis_started",
                    "message": "Voice analysis started"
                }, client_id)
            
            elif message["type"] == "stop_analysis":
                await manager.send_personal_message({
                    "type": "analysis_stopped",
                    "message": "Voice analysis stopped"
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        manager.disconnect(client_id)

async def process_audio_chunk(audio_data: str, client_id: str):
    """Process incoming audio chunk and perform real-time analysis"""
    try:
        # 1. Voice Activity Detection + Speaker Diarization
        vad_result = await audio_processor.process_vad(audio_data)
        
        if not vad_result["has_speech"]:
            return
        
        # 2. Real-time Transcription (Whisper)
        transcript_result = await audio_processor.transcribe_chunk(
            audio_data, 
            language="auto"
        )
        
        if not transcript_result["text"]:
            return
        
        # 3. Scam Detection (LLM + Classifier)
        scam_result = await scam_detector.analyze_text(
            transcript_result["text"],
            transcript_result["language"]
        )
        
        # 4. Voice Anti-Spoofing (AASIST)
        voice_result = await voice_analyzer.detect_spoofing(audio_data)
        
        # 5. Calculate combined risk score
        risk_score = calculate_risk_score(scam_result, voice_result)
        
        # 6. Send results to client
        response = {
            "type": "analysis_result",
            "timestamp": datetime.now().isoformat(),
            "transcript": {
                "text": transcript_result["text"],
                "speaker": vad_result["speaker"],
                "language": transcript_result["language"],
                "confidence": transcript_result["confidence"]
            },
            "risk_assessment": {
                "score": risk_score,
                "level": get_risk_level(risk_score),
                "scam_indicators": scam_result["indicators"],
                "voice_spoofing": voice_result["is_spoofed"],
                "spoofing_confidence": voice_result["confidence"]
            }
        }
        
        await manager.send_personal_message(response, client_id)
        
        # 7. Generate TTS alert if high risk
        if risk_score > 70:
            alert_audio = await tts_alerts.generate_alert(
                risk_score, 
                transcript_result["language"]
            )
            
            await manager.send_personal_message({
                "type": "audio_alert",
                "audio_data": alert_audio,
                "message": "High risk detected"
            }, client_id)
            
    except Exception as e:
        logger.error(f"Error processing audio chunk: {str(e)}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Processing error: {str(e)}"
        }, client_id)

def calculate_risk_score(scam_result: dict, voice_result: dict) -> float:
    """Calculate combined risk score from scam and voice analysis"""
    scam_score = scam_result["risk_score"]
    voice_score = voice_result["spoofing_score"]
    
    # Weighted combination
    combined_score = (scam_score * 0.7) + (voice_score * 0.3)
    return min(100.0, max(0.0, combined_score))

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
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
