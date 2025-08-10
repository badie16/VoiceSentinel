import torch
import numpy as np
import logging

logger = logging.getLogger(__name__)

class VADService:
    def __init__(self):
        self.model, self.utils = self._load_silero_vad_model()
        self.get_speech_timestamps, self.save_audio, self.read_audio, self.VADIterator, self.collect_chunks = self.utils
        logger.info("VADService initialized with Silero VAD.")

    def _load_silero_vad_model(self):
        """Loads the Silero VAD model."""
        try:
            model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                          model='silero_vad',
                                          force_reload=False, # Set to True to always download latest
                                          onnx=False) # Use PyTorch model
            return model, utils
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise RuntimeError("Silero VAD model could not be loaded. Check internet connection or dependencies.")

    def detect_speech_segments(self, audio_data: np.ndarray, sample_rate: int) -> list[tuple[int, int]]:
        """
        Detects speech segments in an audio array using Silero VAD.

        Args:
            audio_data (np.ndarray): Mono audio data (float array, typically -1.0 to 1.0).
            sample_rate (int): Sample rate of the audio.

        Returns:
            list[tuple[int, int]]: List of (start_sample, end_sample) for speech segments.
        """
        # Silero VAD expects 16kHz audio. Resample if necessary.
        if sample_rate != 16000:
            # For simplicity, we'll use a basic resampling here.
            # For production, consider torchaudio.transforms.Resample
            num_samples_16k = int(len(audio_data) * 16000 / sample_rate)
            audio_data_16k = np.interp(
                np.linspace(0, len(audio_data) - 1, num_samples_16k),
                np.arange(len(audio_data)),
                audio_data
            ).astype(np.float32)
            logger.debug(f"Resampled audio from {sample_rate}Hz to 16000Hz for VAD.")
            input_audio = torch.from_numpy(audio_data_16k)
        else:
            input_audio = torch.from_numpy(audio_data)

        try:
            # Get speech timestamps
            speech_timestamps = self.get_speech_timestamps(input_audio, self.model, sampling_rate=16000)
            
            # Convert timestamps back to original sample rate
            original_speech_timestamps = []
            for ts in speech_timestamps:
                start_orig = int(ts['start'] * sample_rate / 16000)
                end_orig = int(ts['end'] * sample_rate / 16000)
                original_speech_timestamps.append((start_orig, end_orig))

            logger.debug(f"Silero VAD detected {len(original_speech_timestamps)} speech segments.")
            return original_speech_timestamps
        except Exception as e:
            logger.error(f"Error during Silero VAD processing: {e}")
            return []
