import logging
from typing import List
from models.analysis_models import AnalysisResult, IncidentReport
import time

logger = logging.getLogger(__name__)

class ReportController:
    def __init__(self):
        logger.info("ReportController initialized.")

    async def generate_incident_report(self, all_analysis_results: List[AnalysisResult], call_start_time: float) -> IncidentReport:
        """
        Generates a summary report after a call.

        Args:
            all_analysis_results (List[AnalysisResult]): All analysis results collected during the call.
            call_start_time (float): The timestamp when the call started.

        Returns:
            IncidentReport: A comprehensive report of the call.
        """
        call_duration_seconds = 0
        if all_analysis_results:
            # Assuming results are ordered by time, duration is from first start to last end
            call_duration_seconds = all_analysis_results[-1].end_time - all_analysis_results[0].start_time
            if call_duration_seconds < 0: # Handle edge case if only one segment or misordered
                call_duration_seconds = all_analysis_results[0].end_time - all_analysis_results[0].start_time

        scam_segments = [r for r in all_analysis_results if r.scam_detection.label == "Scam"]
        suspicious_segments = [r for r in all_analysis_results if r.scam_detection.label == "Suspicious"]
        
        flagged_segments = scam_segments + suspicious_segments # Combine for flagged

        summary_text = f"Call lasted approximately {call_duration_seconds:.1f} seconds. "
        summary_text += f"Analyzed {len(all_analysis_results)} speech segments. "
        
        if scam_segments:
            summary_text += f"Detected {len(scam_segments)} scam segments. "
        if suspicious_segments:
            summary_text += f"Detected {len(suspicious_segments)} suspicious segments. "
        
        if not flagged_segments:
            summary_text += "No suspicious or scam activity detected."
        else:
            summary_text += "Key flagged segments are detailed below."

        recommended_steps = "Based on the analysis:\n"
        if scam_segments:
            recommended_steps += "- Immediately block the caller's number.\n"
            recommended_steps += "- Report the incident to relevant authorities (e.g., police, consumer protection).\n"
            recommended_steps += "- Do not share any personal or financial information with unknown callers.\n"
        elif suspicious_segments:
            recommended_steps += "- Be cautious of similar calls in the future.\n"
            recommended_steps += "- Verify the identity of callers independently (e.g., call back on an official number).\n"
        else:
            recommended_steps += "- Continue to be vigilant against potential scam attempts.\n"
        
        report = IncidentReport(
            call_duration_seconds=call_duration_seconds,
            total_segments_analyzed=len(all_analysis_results),
            scam_segments_count=len(scam_segments),
            suspicious_segments_count=len(suspicious_segments),
            flagged_segments=flagged_segments,
            summary=summary_text,
            recommended_next_steps=recommended_steps
        )
        
        logger.info(f"Generated incident report for call starting at {call_start_time}.")
        return report
