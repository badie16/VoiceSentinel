import asyncio
import base64
from typing import Dict, Any, Optional
import logging
import requests
import os
import time
from config import settings

logger = logging.getLogger(__name__)

class TTSAlerts:
    def __init__(self):
        # ElevenLabs API configuration
        self.api_key = settings.ELEVENLABS_API_KEY
        self.api_url = "https://api.elevenlabs.io/v1/text-to-speech"
        
        # Voice IDs for different languages (ElevenLabs)
        self.voice_ids = {
            "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel (English)
            "es": "VR6AewLTigWG4xSOukaG",  # Esperanza (Spanish)
            "fr": "ThT5KcBeYPX3keUQqHPh",  # Charlotte (French)
            "de": "8WbGz6jt9vfj6pAAq5XK",  # Giselle (German)
            "it": "XB0fDUnXU5powFXDhCwa",  # Matilda (Italian)
        }
        
        # Enhanced alert messages by language and risk level
        self.alert_messages = {
            "en": {
                "high_risk": "URGENT WARNING: This call appears to be fraudulent. Do not share personal information or send money.",
                "medium_risk": "CAUTION: Suspicious activity detected. Be very careful with this caller.",
                "voice_spoofing": "ALERT: Synthetic or cloned voice detected. This may be a deepfake scam.",
                "personal_info": "WARNING: The caller is requesting personal information. Legitimate companies don't ask for this over the phone.",
                "pressure_tactics": "NOTICE: High-pressure tactics detected. Take time to think before acting.",
                "scam_patterns": "ALERT: Known scam patterns detected in this conversation."
            },
            "es": {
                "high_risk": "ADVERTENCIA URGENTE: Esta llamada parece ser fraudulenta. No comparta información personal ni envíe dinero.",
                "medium_risk": "PRECAUCIÓN: Actividad sospechosa detectada. Tenga mucho cuidado con esta persona.",
                "voice_spoofing": "ALERTA: Voz sintética o clonada detectada. Esto puede ser una estafa deepfake.",
                "personal_info": "ADVERTENCIA: La persona solicita información personal. Las empresas legítimas no piden esto por teléfono.",
                "pressure_tactics": "AVISO: Tácticas de alta presión detectadas. Tómese tiempo para pensar antes de actuar.",
                "scam_patterns": "ALERTA: Patrones de estafa conocidos detectados en esta conversación."
            },
            "fr": {
                "high_risk": "AVERTISSEMENT URGENT: Cet appel semble être frauduleux. Ne partagez pas d'informations personnelles.",
                "medium_risk": "PRUDENCE: Activité suspecte détectée. Soyez très prudent avec cet appelant.",
                "voice_spoofing": "ALERTE: Voix synthétique ou clonée détectée. Ceci peut être une arnaque deepfake.",
                "personal_info": "AVERTISSEMENT: L'appelant demande des informations personnelles. Les entreprises légitimes ne demandent pas cela par téléphone.",
                "pressure_tactics": "AVIS: Tactiques de haute pression détectées. Prenez le temps de réfléchir avant d'agir.",
                "scam_patterns": "ALERTE: Modèles d'arnaque connus détectés dans cette conversation."
            },
            "de": {
                "high_risk": "DRINGENDE WARNUNG: Dieser Anruf scheint betrügerisch zu sein. Teilen Sie keine persönlichen Informationen.",
                "medium_risk": "VORSICHT: Verdächtige Aktivität erkannt. Seien Sie sehr vorsichtig mit diesem Anrufer.",
                "voice_spoofing": "ALARM: Synthetische oder geklonte Stimme erkannt. Dies könnte ein Deepfake-Betrug sein.",
                "personal_info": "WARNUNG: Der Anrufer fordert persönliche Informationen. Seriöse Unternehmen fragen nicht telefonisch danach.",
                "pressure_tactics": "HINWEIS: Hochdruck-Taktiken erkannt. Nehmen Sie sich Zeit zum Nachdenken.",
                "scam_patterns": "ALARM: Bekannte Betrugsmuster in diesem Gespräch erkannt."
            },
            "it": {
                "high_risk": "AVVISO URGENTE: Questa chiamata sembra essere fraudolenta. Non condividere informazioni personali.",
                "medium_risk": "ATTENZIONE: Attività sospetta rilevata. Sii molto cauto con questo chiamante.",
                "voice_spoofing": "ALLARME: Voce sintetica o clonata rilevata. Potrebbe essere una truffa deepfake.",
                "personal_info": "AVVERTIMENTO: Il chiamante richiede informazioni personali. Le aziende legittime non le chiedono al telefono.",
                "pressure_tactics": "AVVISO: Tattiche ad alta pressione rilevate. Prenditi tempo per pensare prima di agire.",
                "scam_patterns": "ALLARME: Modelli di truffa noti rilevati in questa conversazione."
            }
        }
        
        # Initialize local TTS fallback
        self.local_tts = None
        try:
            import pyttsx3
            self.local_tts = pyttsx3.init()
            self.local_tts.setProperty('rate', 150)  # Speed
            self.local_tts.setProperty('volume', 0.8)  # Volume
            logger.info("Local TTS initialized as fallback")
        except ImportError:
            logger.warning("pyttsx3 not available, no local TTS fallback")
        
        logger.info("TTSAlerts initialized")

    async def generate_alert(self, risk_score: float, language: str = "en", 
                           alert_type: Optional[str] = None, 
                           indicators: Optional[list] = None) -> Optional[str]:
        """Enhanced TTS alert generation with context awareness"""
        try:
            # Determine alert type based on risk score and indicators
            if alert_type is None:
                alert_type = self._determine_alert_type(risk_score, indicators or [])
            
            # Get message in appropriate language
            messages = self.alert_messages.get(language, self.alert_messages["en"])
            message = messages.get(alert_type, messages["medium_risk"])
            
            # Try ElevenLabs first, then fallback to local TTS
            if self.api_key:
                audio_data = await self._generate_elevenlabs_tts(message, language)
                if audio_data:
                    return audio_data
            
            # Fallback to local TTS
            return await self._generate_local_tts(message, language)
            
        except Exception as e:
            logger.error(f"TTS alert generation error: {str(e)}")
            return None

    def _determine_alert_type(self, risk_score: float, indicators: list) -> str:
        """Determine the most appropriate alert type"""
        # Check for specific indicator types
        indicator_types = [ind.get("type", "") for ind in indicators if isinstance(ind, dict)]
        
        if "personal_info_request" in indicator_types:
            return "personal_info"
        elif "pressure_tactic" in indicator_types:
            return "pressure_tactics"
        elif any("voice" in ind_type for ind_type in indicator_types):
            return "voice_spoofing"
        elif len(indicators) >= 3:
            return "scam_patterns"
        elif risk_score >= 80:
            return "high_risk"
        else:
            return "medium_risk"

    async def _generate_elevenlabs_tts(self, text: str, language: str) -> Optional[str]:
        """Generate TTS using ElevenLabs API with enhanced error handling"""
        try:
            voice_id = self.voice_ids.get(language, self.voice_ids["en"])
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Enhanced voice settings for alert clarity
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.7,  # Higher stability for alerts
                    "similarity_boost": 0.8,  # Higher similarity
                    "style": 0.2,  # Slight style for urgency
                    "use_speaker_boost":_boost": 0.8,  # Higher similarity
                    "style": 0.2,  # Slight style for urgency
                    "use_speaker_boost": True
                }
            }
            
            # Make request with timeout
            response = requests.post(
                f"{self.api_url}/{voice_id}",
                json=data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                # Encode audio data as base64
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                logger.info(f"ElevenLabs TTS generated successfully for language: {language}")
                return audio_base64
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("ElevenLabs API timeout")
            return None
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {str(e)}")
            return None

    async def _generate_local_tts(self, text: str, language: str = "en") -> Optional[str]:
        """Generate TTS using local pyttsx3 as fallback"""
        try:
            if not self.local_tts:
                return None
            
            # Set voice based on language (if available)
            voices = self.local_tts.getProperty('voices')
            if voices:
                for voice in voices:
                    if language in voice.id.lower() or language in voice.name.lower():
                        self.local_tts.setProperty('voice', voice.id)
                        break
            
            # Generate speech to temporary file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            self.local_tts.save_to_file(text, temp_path)
            self.local_tts.runAndWait()
            
            # Read and encode the audio file
            if os.path.exists(temp_path):
                with open(temp_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Clean up temporary file
                os.unlink(temp_path)
                
                logger.info(f"Local TTS generated successfully for language: {language}")
                return audio_base64
            
            return None
            
        except Exception as e:
            logger.error(f"Local TTS error: {str(e)}")
            return None

    def get_alert_message(self, alert_type: str, language: str = "en") -> str:
        """Get alert message for given type and language"""
        messages = self.alert_messages.get(language, self.alert_messages["en"])
        return messages.get(alert_type, messages["medium_risk"])

    async def generate_custom_alert(self, message: str, language: str = "en") -> Optional[str]:
        """Generate custom TTS alert with user-provided message"""
        try:
            if self.api_key:
                audio_data = await self._generate_elevenlabs_tts(message, language)
                if audio_data:
                    return audio_data
            
            return await self._generate_local_tts(message, language)
            
        except Exception as e:
            logger.error(f"Custom alert generation error: {str(e)}")
            return None
