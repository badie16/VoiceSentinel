import numpy as np
import logging
from models.analysis_models import AntiSpoofingResult

logger = logging.getLogger(__name__)

class AntiSpoofingService:
    def __init__(self):
        logger.info("AntiSpoofingService initialized (intelligent mock).")

    def detect_synthetic_voice(self, audio_segment: np.ndarray, sample_rate: int) -> AntiSpoofingResult:
        """
        Intelligent mock for synthetic voice (deepfake) detection.
        Simulates detection based on simple audio features that might differ in synthetic speech.
        This is NOT a real anti-spoofing model.

        Args:
            audio_segment (np.ndarray): Audio data for the segment.
            sample_rate (int): Sample rate of the audio.

        Returns:
            AntiSpoofingResult: A dictionary indicating if the voice is synthetic and a confidence score.
        """
        if len(audio_segment) < sample_rate * 0.1: # Need at least 100ms of audio
            return AntiSpoofingResult(is_synthetic=False, confidence=0.5)

        # Feature 1: Zero-crossing rate (can be higher/lower for synthetic)
        # A very simple proxy for noisiness/periodicity
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_segment)))) / (2 * len(audio_segment))

        # Feature 2: Energy variation (synthetic voices might have less natural variation)
        frame_size = int(0.02 * sample_rate)
        energies = [np.sum(audio_segment[i:i+frame_size]**2) for i in range(0, len(audio_segment) - frame_size, frame_size)]
        energy_std = np.std(energies) if energies else 0

        # Feature 3: Spectral flatness (can differ for synthetic speech)
        # Requires FFT, let's keep it simple for a mock.
        # For a real implementation, you'd compute MFCCs or other spectral features.

        # Simple heuristic for mock detection
        is_synthetic = False
        confidence = 0.5 # Default confidence

        # Example heuristics (highly simplified and not scientifically accurate):
        # - Very low energy variation might suggest synthetic
        if energy_std < 0.0001 and len(energies) > 10: # Arbitrary threshold
            is_synthetic = True
            confidence = min(0.9, 0.7 + (0.0001 - energy_std) * 1000) # Higher confidence for lower std

        # - Very high or very low zero-crossing rate might suggest synthetic
        if zero_crossings > 0.2 or zero_crossings < 0.01: # Arbitrary thresholds
            if not is_synthetic: # Only set if not already synthetic
                is_synthetic = True
                confidence = min(0.9, 0.6 + abs(zero_crossings - 0.1) * 2) # Higher confidence for extremes

        # Add some randomness to make it less predictable, but biased by features
        if np.random.rand() < 0.05: # Small chance to flip outcome
            is_synthetic = not is_synthetic
            confidence = np.random.rand() * 0.2 + 0.7 # Random high confidence

        logger.debug(f"Anti-spoofing (mock): ZCR={zero_crossings:.3f}, Energy_STD={energy_std:.5f}, Synthetic={is_synthetic}, Confidence={confidence:.2f}")
        
        return AntiSpoofingResult(is_synthetic=is_synthetic, confidence=float(confidence))
