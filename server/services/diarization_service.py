import numpy as np
import logging
from models.analysis_models import SpeechSegment
from speechbrain.pretrained import EncoderClassifier
import torch

logger = logging.getLogger(__name__)

class DiarizationService:
    def __init__(self):
        self.speaker_encoder = self._load_speaker_encoder()
        self.speaker_embeddings = {} # Stores embeddings for active speakers {speaker_id: embedding}
        self.speaker_id_counter = 0 # Simple counter for new speakers
        logger.info("DiarizationService initialized with SpeechBrain speaker encoder.")

    def _load_speaker_encoder(self):
        """Loads the SpeechBrain speaker encoder model."""
        try:
            # Using ECAPA-TDNN for speaker embeddings
            # This model is good for speaker verification/identification
            model = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-tdnn", savedir="pretrained_models/spkrec-ecapa-tdnn")
            return model
        except Exception as e:
            logger.error(f"Failed to load SpeechBrain speaker encoder: {e}")
            raise RuntimeError("SpeechBrain speaker encoder could not be loaded. Check internet connection or dependencies.")

    def get_speaker_embedding(self, audio_segment: np.ndarray, sample_rate: int) -> torch.Tensor:
        """
        Extracts a speaker embedding from an audio segment.
        """
        # SpeechBrain expects 16kHz audio. Resample if necessary.
        if sample_rate != 16000:
            num_samples_16k = int(len(audio_segment) * 16000 / sample_rate)
            audio_segment_16k = np.interp(
                np.linspace(0, len(audio_segment) - 1, num_samples_16k),
                np.arange(len(audio_segment)),
                audio_segment
            ).astype(np.float32)
            logger.debug(f"Resampled audio from {sample_rate}Hz to 16000Hz for speaker embedding.")
            input_audio = torch.from_numpy(audio_segment_16k).unsqueeze(0) # Add batch dim
        else:
            input_audio = torch.from_numpy(audio_segment).unsqueeze(0) # Add batch dim

        # Compute embedding
        with torch.no_grad():
            embeddings = self.speaker_encoder.encode_batch(input_audio)
        return embeddings.squeeze(0) # Remove batch dim

    def assign_speaker(self, embedding: torch.Tensor, similarity_threshold: float = 0.25) -> str:
        """
        Assigns a speaker ID based on similarity to known speakers in the current session.
        """
        if not self.speaker_embeddings:
            # First speaker encountered in this session
            self.speaker_id_counter += 1
            speaker_id = f"speaker_{self.speaker_id_counter}"
            self.speaker_embeddings[speaker_id] = embedding
            logger.debug(f"Assigned new speaker: {speaker_id}")
            return speaker_id
        
        # Compare with existing speakers in the session
        max_similarity = -1
        best_match_id = None

        for speaker_id, known_embedding in self.speaker_embeddings.items():
            similarity = torch.nn.functional.cosine_similarity(embedding, known_embedding, dim=0).item()
            if similarity > max_similarity:
                max_similarity = similarity
                best_match_id = speaker_id
        
        if max_similarity > similarity_threshold: # If similarity is above threshold, it's a known speaker
            logger.debug(f"Matched speaker {best_match_id} with similarity {max_similarity:.2f}")
            # Update the stored embedding with a weighted average for better representation over time
            self.speaker_embeddings[best_match_id] = (self.speaker_embeddings[best_match_id] * 0.8 + embedding * 0.2)
            return best_match_id
        else: # Otherwise, it's a new speaker
            self.speaker_id_counter += 1
            new_speaker_id = f"speaker_{self.speaker_id_counter}"
            self.speaker_embeddings[new_speaker_id] = embedding
            logger.debug(f"Assigned new speaker: {new_speaker_id} (max similarity {max_similarity:.2f} below threshold)")
            return new_speaker_id

    def diarize_segments(self, speech_segments_raw: list[tuple[int, int]], audio_data: np.ndarray, sample_rate: int) -> list[SpeechSegment]:
        """
        Diarizes speech segments by assigning a speaker ID.
        """
        diarized_segments = []
        for s_start, s_end in speech_segments_raw:
            segment_audio = audio_data[s_start:s_end]
            if len(segment_audio) == 0:
                continue

            embedding = self.get_speaker_embedding(segment_audio, sample_rate)
            speaker_id = self.assign_speaker(embedding)

            diarized_segments.append(SpeechSegment(
                speaker=speaker_id,
                start_time=s_start / sample_rate,
                end_time=s_end / sample_rate,
            ))
        logger.debug(f"Diarized {len(diarized_segments)} speech segments.")
        return diarized_segments

    def reset_speakers(self):
        """Resets the known speakers for a new call session."""
        self.speaker_embeddings = {}
        self.speaker_id_counter = 0
        logger.info("DiarizationService speaker embeddings reset.")
