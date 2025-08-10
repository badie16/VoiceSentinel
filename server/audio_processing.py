import numpy as np
import logging

logger = logging.getLogger(__name__)

def detect_speech_segments(audio_data: np.ndarray, sample_rate: int, threshold: float = 0.01, min_speech_duration: float = 0.1):
    """
    Detects speech segments in an audio array based on energy.
    This is a very basic VAD. For production, consider a more robust VAD like Silero VAD.

    Args:
        audio_data (np.ndarray): Mono audio data (float array, typically -1.0 to 1.0).
        sample_rate (int): Sample rate of the audio.
        threshold (float): Energy threshold to consider a frame as speech.
        min_speech_duration (float): Minimum duration of a speech segment in seconds.

    Returns:
        list[tuple[int, int]]: List of (start_sample, end_sample) for speech segments.
    """
    frame_size = int(0.02 * sample_rate) # 20ms frames
    hop_size = int(0.01 * sample_rate)   # 10ms hop
    
    speech_segments = []
    in_speech = False
    current_segment_start = 0

    for i in range(0, len(audio_data) - frame_size, hop_size):
        frame = audio_data[i : i + frame_size]
        energy = np.sum(frame**2) / frame_size

        if energy > threshold:
            if not in_speech:
                current_segment_start = i
                in_speech = True
        else:
            if in_speech:
                segment_duration = (i - current_segment_start) / sample_rate
                if segment_duration >= min_speech_duration:
                    speech_segments.append((current_segment_start, i))
                in_speech = False
    
    # Handle case where speech extends to the end of the audio
    if in_speech:
        segment_duration = (len(audio_data) - current_segment_start) / sample_rate
        if segment_duration >= min_speech_duration:
            speech_segments.append((current_segment_start, len(audio_data)))

    return speech_segments

def simple_diarization(speech_segments: list[tuple[int, int]], audio_data: np.ndarray, sample_rate: int):
    """
    A very simplified diarization placeholder.
    In a real scenario, this would involve speaker embedding extraction and clustering.
    For this MVP, we'll just assume all detected speech is from the 'caller' for scam detection.
    """
    # In a real application, you'd use speaker recognition models here.
    # For now, we'll just return the segments as if they are from the 'caller'.
    logger.info(f"Simplified diarization: {len(speech_segments)} speech segments detected.")
    return [{"speaker": "caller", "start": s / sample_rate, "end": e / sample_rate, "audio_segment": audio_data[s:e]} for s, e in speech_segments]
