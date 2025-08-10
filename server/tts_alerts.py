import asyncio
import base64
from typing import Dict, Any, Optional
import logging
import requests
import os

logger = logging.getLogger(__name__)

class TTSAlerts:
    def __init__(self):
        # ElevenLabs API configuration
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.api_url = "https://api.elevenlabs.io/v1/text-to-speech"
        
        # Voice IDs for different languages
        self.voice_ids = {
            "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel (English)
            "es": "VR6AewLTigWG4xSOukaG",  # Esperanza (Spanish)
            "fr": "ThT5KcBeYPX3keUQqHPh",  # Charlotte (French)
        }
        
        # Alert messages by language
        self.alert_messages = {
            "en": {
                "high_risk": "Warning: This call may be fraudulent. Do not share personal information.",
                "medium_risk": "Caution: Suspicious activity detected in this call.",
                "voice_spoofing": "Alert: Synthetic voice detected. This may be a deepfake."
            },
            "es": {
                "high_risk": "Advertencia: Esta llamada puede ser fraudulenta. No comparta información personal.",
                "medium_risk": "Precaución: Actividad sospechosa detectada en esta llamada.",
                "voice_spoofing": "Alerta: Voz sintética detectada. Esto puede ser un deepfake."
            },
            "fr": {
                "high_risk": "Attention: Cet appel peut être frauduleux. Ne partagez pas d'informations personnelles.",
                "medium_risk": "Prudence: Activité suspecte détectée dans cet appel.",
                "voice_spoofing": "Alerte: Voix synthétique détectée. Ceci peut être un deepfake."
            }
        }
        
        logger.info("TTSAlerts initialized")

    async def generate_alert(self, risk_score: float, language: str = "en") -> Optional[str]:
        """Generate TTS alert based on risk score and language"""
        try:
            # Determine alert type
            if risk_score >= 80:
                alert_type = "high_risk"
            elif risk_score >= 60:
                alert_type = "voice_spoofing"
            else:
                alert_type = "medium_risk"
            
            # Get message in appropriate language
            messages = self.alert_messages.get(language, self.alert_messages["en"])
            message = messages.get(alert_type, messages["medium_risk"])
            
            # Generate TTS audio
            if self.api_key:
                audio_data = await self._generate_elevenlabs_tts(message, language)
            else:
                # Fallback to simple text alert
                audio_data = await self._generate_fallback_alert(message)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS alert generation error: {str(e)}")
            return None

    async def _generate_elevenlabs_tts(self, text: str, language: str) -> Optional[str]:
        """Generate TTS using ElevenLabs API"""
        try:
            voice_id = self.voice_ids.get(language, self.voice_ids["en"])
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            # Make async request
            response = requests.post(
                f"{self.api_url}/{voice_id}",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Encode audio data as base64
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                return audio_base64
            else:
                logger.error(f"ElevenLabs API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {str(e)}")
            return None

    async def _generate_fallback_alert(self, message: str) -> str:
        """Generate fallback alert (text-based)"""
        try:
            # Return message as base64 encoded text (placeholder)
            # In real implementation, could use local TTS or simple beep
            return base64.b64encode(message.encode('utf-8')).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Fallback alert error: {str(e)}")
            return ""

    def get_alert_message(self, alert_type: str, language: str = "en") -> str:
        """Get alert message for given type and language"""
        messages = self.alert_messages.get(language, self.alert_messages["en"])
        return messages.get(alert_type, messages["medium_risk"])
