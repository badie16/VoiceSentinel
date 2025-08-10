import whisper
import torch
import numpy as np
import logging
from models.analysis_models import TranscriptionResult

logger = logging.getLogger(__name__)

class WhisperService:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.whisper_model = None
        self._load_model()

    def _load_model(self):
        """Loads the Whisper model."""
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.whisper_model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"Whisper model '{self.model_name}' loaded successfully on {self.device}.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model '{self.model_name}': {e}")
            self.whisper_model = None # Handle case where model loading fails

    def transcribe_audio(self, audio_segment: np.ndarray, sample_rate: int) -> TranscriptionResult:
        """
        Transcribes an audio segment using the loaded Whisper model.

        Args:
            audio_segment (np.ndarray): Mono audio data (float array, typically -1.0 to 1.0).
            sample_rate (int): Sample rate of the audio.

        Returns:
            TranscriptionResult: The transcribed text and detected language.
        """
        if self.whisper_model is None:
            logger.warning("Whisper model not loaded. Cannot transcribe.")
            return TranscriptionResult(text="", language="en")

        # Whisper expects 16kHz audio. Resample if necessary.
        # For simplicity, we'll assume input is 16kHz or close enough for 'base' model.
        # Proper resampling would use torchaudio.transforms.Resample
        if sample_rate != 16000:
            logger.warning(f"Whisper expects 16kHz, but received {sample_rate}Hz. Resampling is not implemented here.")
            # Example of proper resampling (requires torchaudio):
            # from torchaudio.transforms import Resample
            # resampler = Resample(orig_freq=sample_rate, new_freq=16000)
            # audio_segment = resampler(torch.from_numpy(audio_segment).float()).numpy()

        audio_tensor = torch.from_numpy(audio_segment).float()

        try:
            result = self.whisper_model.transcribe(audio_tensor, fp16=False) # fp16=False for CPU compatibility
            transcription_text = result["text"]
            detected_language = result.get("language", "en") # Whisper can detect language
            logger.debug(f"Transcription: '{transcription_text}' (Lang: {detected_language})")
            return TranscriptionResult(text=transcription_text, language=detected_language)
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return TranscriptionResult(text="", language="en")
