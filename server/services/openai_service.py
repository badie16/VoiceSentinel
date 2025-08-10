import os
import json
import logging
from openai import OpenAI
from models.analysis_models import ScamDetectionResult

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        # Initialiser le client OpenAI avec la clé API depuis les variables d'environnement
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY environment variable not set. Scam detection will fail.")
        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAIService initialized.")

    async def detect_scam_intent(self, text: str, language: str = "en") -> ScamDetectionResult:
        """
        Detects scam intent in the given text using OpenAI's GPT model.

        Args:
            text (str): The transcribed text to analyze.
            language (str): The language of the text (e.g., "en", "es", "fr").

        Returns:
            ScamDetectionResult: Contains the detected label (Safe, Suspicious, Scam) and rationale.
        """
        if not text.strip():
            return ScamDetectionResult(label="Safe", rationale="No speech detected or transcribed.")

        if not os.getenv("OPENAI_API_KEY"):
            return ScamDetectionResult(label="Error", rationale="OPENAI_API_KEY not set.")

        prompt = f"""
        You are an AI assistant specialized in detecting scam attempts in phone call transcripts.
        Analyze the following conversation segment and determine if it indicates a 'Safe', 'Suspicious', or 'Scam' intent.
        Provide a brief rationale for your classification.

        Consider the following characteristics for each label:
        - **Safe**: Normal conversation, no unusual requests, no pressure.
        - **Suspicious**: Unusual questions, requests for personal information (but not direct financial), slight pressure, urgent tone without clear reason, mention of unexpected problems (e.g., "your account has been compromised").
        - **Scam**: Direct requests for money, gift cards, bank details, passwords, remote access to computer, threats, impersonation of authority (bank, police, tech support), urgent demands for action, social engineering tactics (e.g., "your grandchild is in trouble").

        The conversation is in {language}. Respond in English.

        Conversation Segment:
        "{text}"

        Output format (JSON):
        {{
            "label": "Safe" | "Suspicious" | "Scam",
            "rationale": "Brief explanation of why this label was chosen."
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # modèle rapide et économique
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}  # force un JSON valide
            )

            result_text = response.choices[0].message.content

            try:
                parsed_response = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from LLM: {result_text}")
                return ScamDetectionResult(label="Error", rationale=f"Invalid JSON: {e}")

            label = parsed_response.get("label", "Error")
            rationale = parsed_response.get("rationale", "No rationale provided.")

            if label not in ["Safe", "Suspicious", "Scam", "Error"]:
                label = "Error"
                rationale = f"LLM returned invalid label: {parsed_response.get('label')}. Original rationale: {rationale}"

            logger.debug(f"Scam Detection Result: Label='{label}', Rationale='{rationale}'")
            return ScamDetectionResult(label=label, rationale=rationale)

        except Exception as e:
            logger.error(f"Error detecting scam intent with OpenAI: {e}")
            return ScamDetectionResult(label="Error", rationale=f"LLM processing failed: {e}")
