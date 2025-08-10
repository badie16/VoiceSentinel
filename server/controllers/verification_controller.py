import logging
from typing import List, Dict
import numpy as np
import torch
from services.diarization_service import DiarizationService # Re-use speaker encoder

logger = logging.getLogger(__name__)

class VerificationController:
    def __init__(self):
        self.diarization_service = DiarizationService() # Use its speaker encoder
        self.safe_list_voice_prints: Dict[str, torch.Tensor] = {} # {name: voice_embedding}
        logger.info("VerificationController initialized for caller verification.")

    def enroll_voice(self, name: str, audio_segment: np.ndarray, sample_rate: int):
        """
        Enrolls a voice print for a known contact by extracting a speaker embedding.
        """
        if len(audio_segment) == 0:
            logger.warning(f"Cannot enroll voice for {name}: empty audio segment.")
            return

        try:
            embedding = self.diarization_service.get_speaker_embedding(audio_segment, sample_rate)
            self.safe_list_voice_prints[name] = embedding
            logger.info(f"Voice for {name} enrolled successfully.")
        except Exception as e:
            logger.error(f"Error enrolling voice for {name}: {e}")

    def verify_caller_voice(self, audio_segment: np.ndarray, sample_rate: int, similarity_threshold: float = 0.7) -> Dict[str, float]:
        """
        Verifies the caller's voice against a safe list using speaker embeddings.

        Args:
            audio_segment (np.ndarray): Audio data for the segment.
            sample_rate (int): Sample rate of the audio.
            similarity_threshold (float): Minimum cosine similarity to consider a match.

        Returns:
            Dict[str, float]: A dictionary of {name: similarity_score} for matches.
        """
        if not self.safe_list_voice_prints:
            logger.debug("Safe list is empty. No verification performed.")
            return {}
        
        if len(audio_segment) == 0:
            logger.warning("Cannot verify voice: empty audio segment.")
            return {}

        try:
            current_embedding = self.diarization_service.get_speaker_embedding(audio_segment, sample_rate)
        except Exception as e:
            logger.error(f"Error getting embedding for verification: {e}")
            return {}

        matches = {}
        for name, enrolled_embedding in self.safe_list_voice_prints.items():
            similarity = torch.nn.functional.cosine_similarity(current_embedding, enrolled_embedding, dim=0).item()
            if similarity > similarity_threshold:
                matches[name] = similarity
        
        logger.debug(f"Caller verification results: {matches}")
        return matches
