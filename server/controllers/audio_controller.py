import numpy as np
import logging
from typing import List
import asyncio
import io
import soundfile as sf # To convert numpy array to bytes (e.g., WAV)

from models.analysis_models import AnalysisResult, SpeechSegment, TranscriptionResult, AntiSpoofingResult, ScamDetectionResult
from services.vad_service import VADService
from services.diarization_service import DiarizationService
from services.whisper_service import WhisperService
from services.anti_spoofing_service import AntiSpoofingService
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class AudioController:
    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self.vad_service = VADService()
        self.diarization_service = DiarizationService()
        self.whisper_service = WhisperService()
        self.anti_spoofing_service = AntiSpoofingService()
        self.openai_service = OpenAIService()
        logger.info("AudioController initialized.")

    async def process_audio_chunk(self, audio_data_np: np.ndarray, current_time_offset: float) -> List[AnalysisResult]:
        """
        Processes a chunk of audio data through the full pipeline.

        Args:
            audio_data_np (np.ndarray): The audio chunk as a numpy array (float32).
            current_time_offset (float): The start time of this audio chunk relative to the call start.

        Returns:
            List[AnalysisResult]: A list of analysis results for detected speech segments.
        """
        results: List[AnalysisResult] = []

        # 1. VAD
        speech_segments_raw = self.vad_service.detect_speech_segments(audio_data_np, self.sample_rate)
        
        if not speech_segments_raw:
            logger.debug("No speech segments detected in this chunk.")
            return results

        # 2. Diarization (now uses speaker embeddings)
        diarized_segments_meta: List[SpeechSegment] = self.diarization_service.diarize_segments(
            speech_segments_raw, audio_data_np, self.sample_rate
        )

        # Process each diarized segment
        for i, segment_meta in enumerate(diarized_segments_meta):
            # Extract audio for the current segment
            start_sample = int(segment_meta.start_time * self.sample_rate)
            end_sample = int(segment_meta.end_time * self.sample_rate)
            segment_audio = audio_data_np[start_sample:end_sample]

            # Convert segment_audio (numpy array) to bytes (WAV format) for storage/passing
            audio_bytes_io = io.BytesIO()
            sf.write(audio_bytes_io, segment_audio, self.sample_rate, format='WAV', subtype='PCM_16')
            segment_audio_bytes = audio_bytes_io.getvalue()

            # Run tasks concurrently for efficiency
            transcription_task = self.whisper_service.transcribe_audio(segment_audio, self.sample_rate)
            spoofing_task = self.anti_spoofing_service.detect_synthetic_voice(segment_audio, self.sample_rate)

            transcription_result, spoofing_result = await asyncio.gather(
                transcription_task,
                spoofing_task
            )

            # 4. Scam Intent Detection (LLM) - depends on transcription
            scam_detection_result = await self.openai_service.detect_scam_intent(
                transcription_result.text, transcription_result.language
            )

            # Combine results
            full_analysis = AnalysisResult(
                speaker=segment_meta.speaker,
                start_time=current_time_offset + segment_meta.start_time, # Adjust to global call time
                end_time=current_time_offset + segment_meta.end_time,     # Adjust to global call time
                transcription=transcription_result,
                anti_spoofing=spoofing_result,
                scam_detection=scam_detection_result,
                alert_triggered=False, # Will be set by AlertController
                audio_segment_bytes=segment_audio_bytes # Store the actual audio segment bytes
            )
            results.append(full_analysis)
        
        logger.info(f"Processed {len(results)} speech segments in chunk starting at {current_time_offset:.2f}s.")
        return results
