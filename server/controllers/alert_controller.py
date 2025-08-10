import logging
from models.analysis_models import AnalysisResult
from services.elevenlabs_service import ElevenLabsService

logger = logging.getLogger(__name__)

class AlertController:
    def __init__(self):
        self.elevenlabs_service = ElevenLabsService()
        logger.info("AlertController initialized.")

    async def generate_and_send_alert(self, analysis_result: AnalysisResult) -> bytes | None:
        """
        Generates a discreet TTS alert based on the scam detection label.

        Args:
            analysis_result (AnalysisResult): The analysis result for a speech segment.

        Returns:
            bytes | None: The MP3 audio data for the alert, or None if no alert is needed/generated.
        """
        alert_text = ""
        if analysis_result.scam_detection.label == "Scam":
            alert_text = "Attention. Cet appel pourrait être une arnaque. Ne partagez aucune information personnelle."
        elif analysis_result.scam_detection.label == "Suspicious":
            alert_text = "Prudence. Cet appel semble suspect. Vérifiez l'identité de l'appelant."
        
        if analysis_result.anti_spoofing.is_synthetic and analysis_result.anti_spoofing.confidence > 0.8:
            if alert_text:
                alert_text += " Une voix synthétique a été détectée."
            else:
                alert_text = "Une voix synthétique a été détectée. Soyez vigilant."

        if alert_text:
            logger.info(f"Generating TTS alert: '{alert_text}' for segment {analysis_result.start_time:.2f}s.")
            # Use the language detected by Whisper for the alert if available, otherwise default to English/French
            alert_audio = await self.elevenlabs_service.generate_tts_audio(
                alert_text,
                language=analysis_result.transcription.language # Use detected language for alert
            )
            return alert_audio
        
        return None
