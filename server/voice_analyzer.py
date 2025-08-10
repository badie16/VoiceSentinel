import asyncio
import numpy as np
import torch
import torch.nn as nn
import librosa
import base64
from typing import Dict, Any, Optional
import logging
from functools import lru_cache
import time
from config import settings

logger = logging.getLogger(__name__)

class VoiceAnalyzer:
    def __init__(self):
        # Initialize advanced anti-spoofing model
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            # Try to load a pre-trained model for voice spoofing detection
            # In production, use AASIST or similar model
            self.model = self._load_antispoofing_model()
            logger.info(f"Voice analyzer initialized on {self.device}")
        except Exception as e:
            logger.warning(f"Could not load advanced model, using fallback: {e}")
        
        self.sample_rate = settings.SAMPLE_RATE
        self.spoofing_threshold = settings.VOICE_SPOOFING_THRESHOLD
        
        # Feature extraction parameters
        self.n_mfcc = 13
        self.n_fft = 2048
        self.hop_length = 512
        
        logger.info("VoiceAnalyzer initialized")

    def _load_antispoofing_model(self):
        """Load pre-trained anti-spoofing model"""
        try:
            # Try to load WavLM or similar model for voice analysis
            from transformers import AutoModel, AutoProcessor
            
            model_name = "microsoft/wavlm-base-plus"
            model = AutoModel.from_pretrained(model_name)
            processor = AutoProcessor.from_pretrained(model_name)
            
            model.to(self.device)
            model.eval()
            
            self.processor = processor
            return model
            
        except Exception as e:
            logger.warning(f"Could not load WavLM model: {e}")
            
            # Fallback: Create a simple neural network for demonstration
            return self._create_simple_model()

    def _create_simple_model(self):
        """Create a simple neural network for spoofing detection"""
        class SimpleSpoofingDetector(nn.Module):
            def __init__(self, input_size=13):  # MFCC features
                super().__init__()
                self.network = nn.Sequential(
                    nn.Linear(input_size, 64),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(32, 1),
                    nn.Sigmoid()
                )
            
            def forward(self, x):
                return self.network(x)
        
        model = SimpleSpoofingDetector()
        model.to(self.device)
        model.eval()
        
        # Initialize with random weights (in production, load trained weights)
        return model

    async def detect_spoofing(self, audio_data: str) -> Dict[str, Any]:
        """Enhanced voice spoofing detection using advanced models"""
        try:
            start_time = time.time()
            
            # Decode audio data
            audio_bytes = base64.b64decode(audio_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            if len(audio_array) == 0:
                return self._empty_result()
            
            # Convert to float32
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Extract comprehensive features
            features = self._extract_comprehensive_features(audio_float)
            
            # Advanced spoofing analysis
            spoofing_score = await self._analyze_with_model(audio_float, features)
            
            # Traditional feature-based analysis
            traditional_score = self._analyze_traditional_features(features)
            
            # Combine scores
            combined_score = (spoofing_score * 0.7) + (traditional_score * 0.3)
            
            is_spoofed = combined_score > self.spoofing_threshold
            confidence = self._calculate_confidence(combined_score, features)
            
            processing_time = time.time() - start_time
            
            return {
                "is_spoofed": is_spoofed,
                "spoofing_score": combined_score * 100,
                "confidence": confidence * 100,
                "processing_time": processing_time,
                "features": {
                    "spectral_centroid": features.get("spectral_centroid", 0.0),
                    "zero_crossing_rate": features.get("zero_crossing_rate", 0.0),
                    "mfcc_variance": features.get("mfcc_variance", 0.0),
                    "spectral_rolloff": features.get("spectral_rolloff", 0.0),
                    "chroma_variance": features.get("chroma_variance", 0.0),
                    "spectral_bandwidth": features.get("spectral_bandwidth", 0.0),
                    "tempo": features.get("tempo", 0.0)
                },
                "analysis": {
                    "model_score": spoofing_score,
                    "traditional_score": traditional_score,
                    "combined_score": combined_score
                }
            }
            
        except Exception as e:
            logger.error(f"Voice spoofing detection error: {str(e)}")
            return self._empty_result()

    def _extract_comprehensive_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract comprehensive audio features for spoofing detection"""
        try:
            # Ensure minimum length
            if len(audio) < self.sample_rate:
                audio = np.pad(audio, (0, self.sample_rate - len(audio)))
            
            features = {}
            
            # 1. Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)[0]
            features["spectral_centroid"] = float(np.mean(spectral_centroids))
            features["spectral_centroid_std"] = float(np.std(spectral_centroids))
            
            # 2. Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            features["zero_crossing_rate"] = float(np.mean(zcr))
            features["zero_crossing_rate_std"] = float(np.std(zcr))
            
            # 3. MFCC features (critical for spoofing detection)
            mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=self.n_mfcc)
            features["mfcc_mean"] = float(np.mean(mfccs))
            features["mfcc_variance"] = float(np.var(mfccs))
            features["mfcc_std"] = float(np.std(mfccs))
            
            # 4. Spectral Rolloff
            rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate)[0]
            features["spectral_rolloff"] = float(np.mean(rolloff))
            features["spectral_rolloff_std"] = float(np.std(rolloff))
            
            # 5. Chroma features
            chroma = librosa.feature.chroma_stft(y=audio, sr=self.sample_rate)
            features["chroma_mean"] = float(np.mean(chroma))
            features["chroma_variance"] = float(np.var(chroma))
            
            # 6. Spectral Bandwidth
            bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.sample_rate)[0]
            features["spectral_bandwidth"] = float(np.mean(bandwidth))
            
            # 7. Tempo and rhythm features
            tempo, _ = librosa.beat.beat_track(y=audio, sr=self.sample_rate)
            features["tempo"] = float(tempo)
            
            # 8. Harmonic and percussive components
            harmonic, percussive = librosa.effects.hpss(audio)
            features["harmonic_ratio"] = float(np.mean(harmonic ** 2) / (np.mean(audio ** 2) + 1e-8))
            features["percussive_ratio"] = float(np.mean(percussive ** 2) / (np.mean(audio ** 2) + 1e-8))
            
            # 9. Spectral contrast
            contrast = librosa.feature.spectral_contrast(y=audio, sr=self.sample_rate)
            features["spectral_contrast"] = float(np.mean(contrast))
            
            # 10. Tonnetz (tonal centroid features)
            tonnetz = librosa.feature.tonnetz(y=audio, sr=self.sample_rate)
            features["tonnetz_mean"] = float(np.mean(tonnetz))
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error: {str(e)}")
            return {}

    async def _analyze_with_model(self, audio: np.ndarray, features: Dict[str, float]) -> float:
        """Analyze audio using the loaded model"""
        try:
            if self.model is None:
                return 0.0
            
            # If using WavLM or similar transformer model
            if hasattr(self, 'processor'):
                return await self._analyze_with_transformer(audio)
            else:
                return self._analyze_with_simple_model(features)
                
        except Exception as e:
            logger.error(f"Model analysis error: {str(e)}")
            return 0.0

    async def _analyze_with_transformer(self, audio: np.ndarray) -> float:
        """Analyze using transformer model (WavLM, etc.)"""
        try:
            # Prepare input for transformer
            inputs = self.processor(audio, sampling_rate=self.sample_rate, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Extract features and compute spoofing score
                # This is a simplified approach - in production, use trained classifier head
                hidden_states = outputs.last_hidden_state
                pooled = torch.mean(hidden_states, dim=1)
                
                # Simple heuristic based on feature variance
                variance = torch.var(pooled, dim=1)
                score = torch.sigmoid(variance * 10).item()  # Scale and normalize
                
                return score
                
        except Exception as e:
            logger.error(f"Transformer analysis error: {str(e)}")
            return 0.0

    def _analyze_with_simple_model(self, features: Dict[str, float]) -> float:
        """Analyze using simple neural network"""
        try:
            # Prepare feature vector
            feature_vector = np.array([
                features.get("mfcc_mean", 0),
                features.get("mfcc_variance", 0),
                features.get("spectral_centroid", 0),
                features.get("zero_crossing_rate", 0),
                features.get("spectral_rolloff", 0),
                features.get("chroma_variance", 0),
                features.get("spectral_bandwidth", 0),
                features.get("tempo", 0),
                features.get("harmonic_ratio", 0),
                features.get("percussive_ratio", 0),
                features.get("spectral_contrast", 0),
                features.get("tonnetz_mean", 0),
                features.get("spectral_centroid_std", 0)
            ], dtype=np.float32)
            
            # Normalize features
            feature_vector = (feature_vector - np.mean(feature_vector)) / (np.std(feature_vector) + 1e-8)
            
            # Convert to tensor
            input_tensor = torch.FloatTensor(feature_vector).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                output = self.model(input_tensor)
                score = output.item()
                
            return score
            
        except Exception as e:
            logger.error(f"Simple model analysis error: {str(e)}")
            return 0.0

    def _analyze_traditional_features(self, features: Dict[str, float]) -> float:
        """Traditional heuristic-based spoofing detection"""
        try:
            if not features:
                return 0.0
            
            score = 0.0
            
            # Check spectral centroid (synthetic voices often have different spectral characteristics)
            spectral_centroid = features.get("spectral_centroid", 0.0)
            if spectral_centroid > 4000 or spectral_centroid < 800:  # Unusual range
                score += 0.25
            
            # Check zero crossing rate
            zcr = features.get("zero_crossing_rate", 0.0)
            if zcr > 0.2 or zcr < 0.03:  # Unusual range
                score += 0.15
            
            # Check MFCC variance (synthetic voices may have different variance patterns)
            mfcc_var = features.get("mfcc_variance", 0.0)
            if mfcc_var < 5.0 or mfcc_var > 50.0:  # Unusual variance
                score += 0.25
            
            # Check spectral rolloff
            rolloff = features.get("spectral_rolloff", 0.0)
            if rolloff > 10000 or rolloff < 1500:  # Unusual range
                score += 0.15
            
            # Check harmonic ratio (synthetic voices may have different harmonic structure)
            harmonic_ratio = features.get("harmonic_ratio", 0.5)
            if harmonic_ratio > 0.9 or harmonic_ratio < 0.1:  # Too harmonic or too noisy
                score += 0.2
            
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"Traditional analysis error: {str(e)}")
            return 0.0

    def _calculate_confidence(self, spoofing_score: float, features: Dict[str, float]) -> float:
        """Calculate confidence in spoofing detection"""
        try:
            base_confidence = 0.5
            
            # Increase confidence for extreme scores
            if spoofing_score > 0.8 or spoofing_score < 0.2:
                base_confidence += 0.3
            elif spoofing_score > 0.6 or spoofing_score < 0.4:
                base_confidence += 0.2
            
            # Increase confidence based on feature quality
            if features:
                feature_count = len([v for v in features.values() if v != 0.0])
                feature_bonus = min(0.2, feature_count * 0.02)
                base_confidence += feature_bonus
            
            # Increase confidence if using advanced model
            if self.model is not None:
                base_confidence += 0.1
            
            return min(1.0, base_confidence)
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {str(e)}")
            return 0.5

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty spoofing detection result"""
        return {
            "is_spoofed": False,
            "spoofing_score": 0.0,
            "confidence": 0.0,
            "processing_time": 0.0,
            "features": {},
            "analysis": {
                "model_score": 0.0,
                "traditional_score": 0.0,
                "combined_score": 0.0
            }
        }
