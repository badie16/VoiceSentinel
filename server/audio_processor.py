import asyncio
import numpy as np
import torch
import whisper
from typing import Dict, Any, Optional
import librosa
import webrtcvad
import base64
import io
import wave
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        # Load Whisper model for transcription
        self.whisper_model = whisper.load_model("base")
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        
        # Audio parameters
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        logger.info("AudioProcessor initialized")

    async def process_vad(self, audio_data: str) -> Dict[str, Any]:
        """Voice Activity Detection and basic speaker diarization"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Resample to 16kHz if needed
            if len(audio_array) > 0:
                audio_float = audio_array.astype(np.float32) / 32768.0
                
                # Check for speech activity
                has_speech = self._detect_speech_activity(audio_bytes)
                
                # Simple speaker detection (placeholder)
                speaker = self._detect_speaker(audio_float)
                
                return {
                    "has_speech": has_speech,
                    "speaker": speaker,
                    "audio_level": float(np.max(np.abs(audio_float))),
                    "duration": len(audio_array) / self.sample_rate
                }
            
            return {"has_speech": False, "speaker": "unknown", "audio_level": 0.0, "duration": 0.0}
            
        except Exception as e:
            logger.error(f"VAD processing error: {str(e)}")
            return {"has_speech": False, "speaker": "unknown", "audio_level": 0.0, "duration": 0.0}

    def _detect_speech_activity(self, audio_bytes: bytes) -> bool:
        """Detect if audio contains speech"""
        try:
            # Split audio into frames for VAD
            frame_size_bytes = self.frame_size * 2  # 16-bit audio
            
            for i in range(0, len(audio_bytes) - frame_size_bytes, frame_size_bytes):
                frame = audio_bytes[i:i + frame_size_bytes]
                if len(frame) == frame_size_bytes:
                    if self.vad.is_speech(frame, self.sample_rate):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Speech detection error: {str(e)}")
            return False

    def _detect_speaker(self, audio_array: np.ndarray) -> str:
        """Simple speaker detection (user vs caller)"""
        try:
            # Placeholder: In real implementation, use speaker embeddings
            # For now, alternate between user and caller based on audio characteristics
            
            # Simple heuristic based on audio energy and frequency
            energy = np.mean(audio_array ** 2)
            
            if energy > 0.01:  # Higher energy = likely user (closer to mic)
                return "user"
            else:
                return "caller"
                
        except Exception as e:
            logger.error(f"Speaker detection error: {str(e)}")
            return "unknown"

    async def transcribe_chunk(self, audio_data: str, language: str = "auto") -> Dict[str, Any]:
        """Real-time transcription using Whisper"""
        try:
            # Decode audio data
            audio_bytes = base64.b64decode(audio_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            if len(audio_array) == 0:
                return {"text": "", "language": "unknown", "confidence": 0.0}
            
            # Convert to float32 and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Ensure minimum length for Whisper
            if len(audio_float) < self.sample_rate:  # Less than 1 second
                # Pad with zeros
                audio_float = np.pad(audio_float, (0, self.sample_rate - len(audio_float)))
            
            # Run Whisper transcription
            result = self.whisper_model.transcribe(
                audio_float,
                language=None if language == "auto" else language,
                task="transcribe"
            )
            
            return {
                "text": result["text"].strip(),
                "language": result["language"],
                "confidence": self._calculate_confidence(result)
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return {"text": "", "language": "unknown", "confidence": 0.0}

    def _calculate_confidence(self, whisper_result: dict) -> float:
        """Calculate transcription confidence from Whisper result"""
        try:
            # Use average log probability as confidence measure
            if "segments" in whisper_result and whisper_result["segments"]:
                avg_logprob = np.mean([seg.get("avg_logprob", -1.0) for seg in whisper_result["segments"]])
                # Convert log probability to confidence (0-100)
                confidence = max(0, min(100, (avg_logprob + 1.0) * 100))
                return confidence
            
            return 50.0  # Default confidence
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {str(e)}")
            return 50.0
