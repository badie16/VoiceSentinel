import asyncio
import numpy as np
import torch
import whisper
from typing import Dict, Any, Optional, List
import librosa
import webrtcvad
import base64
import io
import wave
import logging
from functools import lru_cache
import hashlib
from collections import deque
import time
from config import settings

logger = logging.getLogger(__name__)

class AudioBuffer:
    def __init__(self, max_duration: float = 10.0, sample_rate: int = 16000):
        self.max_duration = max_duration
        self.sample_rate = sample_rate
        self.max_samples = int(max_duration * sample_rate)
        self.buffer = deque(maxlen=self.max_samples)
        self.timestamps = deque()
    
    def add_chunk(self, audio_chunk: np.ndarray):
        current_time = time.time()
        
        # Add audio samples
        for sample in audio_chunk:
            self.buffer.append(sample)
            self.timestamps.append(current_time)
        
        # Remove old timestamps
        cutoff_time = current_time - self.max_duration
        while self.timestamps and self.timestamps[0] < cutoff_time:
            self.timestamps.popleft()
    
    def get_recent_audio(self, duration: float = 3.0) -> np.ndarray:
        """Get recent audio for processing"""
        if not self.buffer:
            return np.array([])
        
        samples_needed = int(duration * self.sample_rate)
        recent_samples = list(self.buffer)[-samples_needed:]
        return np.array(recent_samples, dtype=np.float32)
    
    def get_full_buffer(self) -> np.ndarray:
        return np.array(list(self.buffer), dtype=np.float32)

class AudioProcessor:
    def __init__(self):
        # Load Whisper model for transcription
        try:
            self.whisper_model = whisper.load_model(settings.WHISPER_MODEL)
            logger.info(f"Loaded Whisper model: {settings.WHISPER_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        
        # Audio parameters
        self.sample_rate = settings.SAMPLE_RATE
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        # Audio buffers for each client
        self.client_buffers: Dict[str, AudioBuffer] = {}
        
        # Transcription cache
        self.transcription_cache = {}
        
        logger.info("AudioProcessor initialized")

    def get_or_create_buffer(self, client_id: str) -> AudioBuffer:
        if client_id not in self.client_buffers:
            self.client_buffers[client_id] = AudioBuffer(
                max_duration=settings.MAX_AUDIO_BUFFER,
                sample_rate=self.sample_rate
            )
        return self.client_buffers[client_id]

    async def process_vad(self, audio_data: str, client_id: str) -> Dict[str, Any]:
        """Enhanced Voice Activity Detection with speaker diarization"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            if len(audio_array) == 0:
                return self._empty_vad_result()
            
            # Convert to float32 and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Add to buffer
            buffer = self.get_or_create_buffer(client_id)
            buffer.add_chunk(audio_float)
            
            # Check for speech activity
            has_speech = self._detect_speech_activity(audio_bytes)
            
            # Enhanced speaker detection using recent audio context
            recent_audio = buffer.get_recent_audio(duration=2.0)
            speaker = self._detect_speaker_enhanced(recent_audio)
            
            # Calculate audio quality metrics
            audio_quality = self._calculate_audio_quality(audio_float)
            
            return {
                "has_speech": has_speech,
                "speaker": speaker,
                "audio_level": float(np.max(np.abs(audio_float))),
                "duration": len(audio_array) / self.sample_rate,
                "quality_score": audio_quality,
                "buffer_duration": len(buffer.buffer) / self.sample_rate
            }
            
        except Exception as e:
            logger.error(f"VAD processing error: {str(e)}")
            return self._empty_vad_result()

    def _detect_speech_activity(self, audio_bytes: bytes) -> bool:
        """Enhanced speech activity detection"""
        try:
            frame_size_bytes = self.frame_size * 2  # 16-bit audio
            speech_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_bytes) - frame_size_bytes, frame_size_bytes):
                frame = audio_bytes[i:i + frame_size_bytes]
                if len(frame) > 0:
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

    async def transcribe_chunk(self, audio_data: str, client_id: str, language: str = "auto") -> Dict[str, Any]:
        """Enhanced real-time transcription with caching and optimization"""
        try:
            if not self.whisper_model:
                return {"text": "", "language": "unknown", "confidence": 0.0}
            
            # Decode audio data
            audio_bytes = base64.b64decode(audio_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            if len(audio_array) == 0:
                return {"text": "", "language": "unknown", "confidence": 0.0}
            
            # Convert to float32 and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Get buffer for context
            buffer = self.get_or_create_buffer(client_id)
            
            # Use recent audio context for better transcription
            context_audio = buffer.get_recent_audio(duration=5.0)
            if len(context_audio) > len(audio_float):
                audio_for_transcription = context_audio
            else:
                audio_for_transcription = audio_float
            
            # Create hash for caching
            audio_hash = hashlib.md5(audio_for_transcription.tobytes()).hexdigest()
            
            # Check cache first
            cached_result = self._get_cached_transcription(audio_hash, language)
            if cached_result:
                return cached_result
            
            # Ensure minimum length for Whisper
            if len(audio_for_transcription) < self.sample_rate * 0.5:  # Less than 0.5 seconds
                # Pad with zeros
                padding_needed = int(self.sample_rate * 0.5) - len(audio_for_transcription)
                audio_for_transcription = np.pad(audio_for_transcription, (0, padding_needed))
            
            # Run Whisper transcription with optimizations
            result = self.whisper_model.transcribe(
                audio_for_transcription,
                language=None if language == "auto" else language,
                task="transcribe",
                fp16=torch.cuda.is_available(),  # Use FP16 if GPU available
                condition_on_previous_text=False,  # Faster processing
                temperature=0.0,  # Deterministic output
                no_speech_threshold=0.6,
                logprob_threshold=-1.0
            )
            
            transcription_result = {
                "text": result["text"].strip(),
                "language": result["language"],
                "confidence": self._calculate_confidence(result),
                "processing_time": time.time()
            }
            
            # Cache the result
            self._cache_transcription(audio_hash, language, transcription_result)
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return {"text": "", "language": "unknown", "confidence": 0.0}

    def _calculate_confidence(self, whisper_result: dict) -> float:
        """Enhanced confidence calculation from Whisper result"""
        try:
            if "segments" in whisper_result and whisper_result["segments"]:
                # Use average log probability and no-speech probability
                avg_logprob = np.mean([seg.get("avg_logprob", -1.0) for seg in whisper_result["segments"]])
                no_speech_prob = whisper_result.get("no_speech_prob", 0.5)
                
                # Convert to confidence score
                logprob_confidence = max(0, min(100, (avg_logprob + 1.0) * 100))
                speech_confidence = (1.0 - no_speech_prob) * 100
                
                # Weighted combination
                confidence = (logprob_confidence * 0.7) + (speech_confidence * 0.3)
                return confidence
            
            return 50.0  # Default confidence
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {str(e)}")
            return 50.0

    def cleanup_client_buffer(self, client_id: str):
        """Clean up client buffer when connection closes"""
        if client_id in self.client_buffers:
            del self.client_buffers[client_id]
            logger.info(f"Cleaned up buffer for client {client_id}")

    def _empty_vad_result(self) -> Dict[str, Any]:
        return {
            "has_speech": False,
            "speaker": "unknown",
            "audio_level": 0.0,
            "duration": 0.0,
            "quality_score": 0.0,
            "buffer_duration": 0.0
        }

    def _detect_speaker_enhanced(self, audio_array: np.ndarray) -> str:
        """Enhanced speaker detection using audio features"""
        try:
            if len(audio_array) == 0:
                return "unknown"
            
            # Calculate spectral features
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_array, sr=self.sample_rate))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio_array))
            energy = np.mean(audio_array ** 2)
            
            # Simple heuristic based on audio characteristics
            # In production, use trained speaker embedding model
            if energy > 0.01 and spectral_centroid > 2000:
                return "user"  # Closer to microphone, higher energy
            elif energy > 0.005:
                return "caller"  # Phone audio, different characteristics
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"Enhanced speaker detection error: {str(e)}")
            return "unknown"

    def _calculate_audio_quality(self, audio_array: np.ndarray) -> float:
        """Calculate audio quality score (0-100)"""
        try:
            if len(audio_array) == 0:
                return 0.0
            
            # Signal-to-noise ratio estimation
            signal_power = np.mean(audio_array ** 2)
            noise_floor = np.percentile(np.abs(audio_array), 10) ** 2
            
            if noise_floor > 0:
                snr = 10 * np.log10(signal_power / noise_floor)
                quality = min(100, max(0, (snr + 10) * 2))  # Map SNR to 0-100
            else:
                quality = 50.0  # Default quality
            
            return quality
            
        except Exception as e:
            logger.error(f"Audio quality calculation error: {str(e)}")
            return 50.0

    @lru_cache(maxsize=settings.CACHE_SIZE)
    def _get_cached_transcription(self, audio_hash: str, language: str) -> Optional[Dict[str, Any]]:
        """Cache transcriptions to avoid reprocessing"""
        return self.transcription_cache.get(f"{audio_hash}_{language}")

    def _cache_transcription(self, audio_hash: str, language: str, result: Dict[str, Any]):
        """Cache transcription result"""
        cache_key = f"{audio_hash}_{language}"
        self.transcription_cache[cache_key] = result
        
        # Limit cache size
        if len(self.transcription_cache) > settings.CACHE_SIZE:
            # Remove oldest entries
            oldest_key = next(iter(self.transcription_cache))
            del self.transcription_cache[oldest_key]
