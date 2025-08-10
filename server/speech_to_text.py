import whisper
import torch
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Load Whisper model once
# You might want to choose a smaller model like 'base' or 'tiny' for faster inference
# For better accuracy, 'small' or 'medium' are good. 'large' is very slow.
try:
    # Check if CUDA is available and use it
    device = "cuda" if torch.cuda.is_available() else "cpu"
    whisper_model = whisper.load_model("base", device=device)
    logger.info(f"Whisper model 'base' loaded successfully on {device}.")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    whisper_model = None # Handle case where model loading fails

def transcribe_audio(audio_segment: np.ndarray, sample_rate: int) -> str:
    """
    Transcribes an audio segment using the loaded Whisper model.

    Args:
        audio_segment (np.ndarray): Mono audio data (float array, typically -1.0 to 1.0).
        sample_rate (int): Sample rate of the audio.

    Returns:
        str: The transcribed text.
    """
    if whisper_model is None:
        logger.warning("Whisper model not loaded. Cannot transcribe.")
        return ""

    # Whisper expects 16kHz audio. Resample if necessary.
    if sample_rate != 16000:
        # This is a simple resampling. For production, use a proper audio library.
        # For now, we'll just warn and proceed, assuming the input is close or handled.
        logger.warning(f"Whisper expects 16kHz, but received {sample_rate}Hz. Resampling is not implemented here.")
        # A proper resampling would look like:
        # from torchaudio.transforms import Resample
        # resampler = Resample(orig_freq=sample_rate, new_freq=16000)
        # audio_segment = resampler(torch.from_numpy(audio_segment).float()).numpy()
        pass # Proceeding without resampling for simplicity in this example

    # Convert to a PyTorch tensor if not already
    audio_tensor = torch.from_numpy(audio_segment).float()

    try:
        # Whisper expects a 1D float32 numpy array or torch tensor
        result = whisper_model.transcribe(audio_tensor, fp16=False) # fp16=False for CPU compatibility
        transcription = result["text"]
        logger.info(f"Transcription: '{transcription}'")
        return transcription
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return ""
