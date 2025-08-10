import os
import logging
from dotenv import load_dotenv
from elevenlabs import play
from elevenlabs.client import ElevenLabs

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ElevenLabsService:
    def __init__(self, default_voice_name: str = "Rachel"):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.client = None
        self.default_voice = None

        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY non défini. Le service TTS est désactivé.")
            return

        try:
            # Instanciation correcte du client pour la v1.x.x
            self.client = ElevenLabs(api_key=self.api_key)
            # Pré-chargement de la voix pour l'efficacité
            self.default_voice = self.client.voices.by_name(default_voice_name)
            logger.info(f"Service ElevenLabs initialisé. Voix par défaut '{default_voice_name}' chargée.")
        except Exception as e:
            logger.error(f"Échec de l'initialisation ou de la recherche de la voix '{default_voice_name}': {e}")
            self.client = None

    def generate_audio(self, text: str, voice_name: str | None = None, model: str = "eleven_multilingual_v2") -> bytes | None:
        if not self.client:
            logger.error("Client ElevenLabs non initialisé. Impossible de générer l'audio.")
            return None
        
        try:
            voice_to_use = self.default_voice
            if voice_name:
                voice_to_use = self.client.voices.by_name(voice_name)
            
            if not voice_to_use:
                logger.error(f"La voix demandée ('{voice_name or self.default_voice.name}') est introuvable.")
                return None

            # Appel de la méthode de génération correcte pour la v1.x.x
            audio_bytes = self.client.generate(
                text=text,
                voice=voice_to_use,
                model=model
            )
            return audio_bytes
        except Exception as e:
            logger.error(f"Erreur lors de la génération audio avec ElevenLabs: {e}")
            return None

    @staticmethod
    def play_audio(audio_bytes: bytes):
        if not audio_bytes:
            logger.error("Impossible de jouer l'audio : aucune donnée audio fournie.")
            return
        
        try:
            # Appel de la fonction de lecture correcte pour la v1.x.x
            play(audio_bytes)
            logger.info("Audio TTS joué avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'audio TTS : {e}")