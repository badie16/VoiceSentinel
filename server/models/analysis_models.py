from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict

class SpeechSegment(BaseModel):
    """Represents a detected speech segment."""
    speaker: str # Changed from Literal to str for dynamic speaker IDs
    start_time: float
    end_time: float
    # audio_segment: Optional[bytes] # Not for Pydantic, handled internally as np.ndarray

class TranscriptionResult(BaseModel):
    """Result of the ASR transcription."""
    text: str
    language: str = "en" # Default language

class AntiSpoofingResult(BaseModel):
    """Result of synthetic voice detection."""
    is_synthetic: bool
    confidence: float

class ScamDetectionResult(BaseModel):
    """Result of scam intent detection."""
    label: Literal["Safe", "Suspicious", "Scam", "Error"]
    rationale: str

class AnalysisResult(BaseModel):
    """Comprehensive analysis result for a speech segment."""
    speaker: str # Changed from Literal to str for dynamic speaker IDs
    start_time: float
    end_time: float
    transcription: TranscriptionResult
    anti_spoofing: AntiSpoofingResult
    scam_detection: ScamDetectionResult
    alert_triggered: bool = False # Indicates if an alert was generated for this segment
    caller_verification_matches: Optional[Dict[str, float]] = None # New field for verification results
    audio_segment_bytes: Optional[bytes] = Field(None, exclude=True) # Store audio bytes, but exclude from JSON output

class IncidentReport(BaseModel):
    """Summary report after a call."""
    call_duration_seconds: float
    total_segments_analyzed: int
    scam_segments_count: int
    suspicious_segments_count: int
    flagged_segments: List[AnalysisResult]
    summary: str
    recommended_next_steps: str
