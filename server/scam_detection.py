import os
from ai import generate_text
from ai.models import openai
import logging

logger = logging.getLogger(__name__)

# Ensure OPENAI_API_KEY is set in your environment variables
# For local testing, you can set it like: export OPENAI_API_KEY="your_key_here"
# In Vercel, it will be automatically available if you link the integration.

async def detect_scam_intent(text: str, language: str = "en") -> dict:
    """
    Detects scam intent in the given text using an LLM.

    Args:
        text (str): The transcribed text to analyze.
        language (str): The language of the text (e.g., "en", "es", "fr").

    Returns:
        dict: A dictionary containing the detected label (Safe, Suspicious, Scam)
              and a rationale.
    """
    if not text.strip():
        return {"label": "Safe", "rationale": "No speech detected or transcribed."}

    # Define the prompt for the LLM
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
        # Use a smaller, faster model for real-time if available, e.g., "gpt-4o-mini"
        # Ensure OPENAI_API_KEY is configured in your environment
        result = await generate_text(
            model=openai("gpt-4o-mini"), # Using gpt-4o-mini for speed and cost-effectiveness
            prompt=prompt,
            temperature=0.0, # Keep temperature low for consistent classifications
            response_format={"type": "json_object"} # Request JSON output
        )
        
        # Parse the JSON response
        response_json = result.text
        import json
        parsed_response = json.loads(response_json)
        
        label = parsed_response.get("label", "Unknown")
        rationale = parsed_response.get("rationale", "No rationale provided.")
        
        logger.info(f"Scam Detection Result: Label='{label}', Rationale='{rationale}'")
        return {"label": label, "rationale": rationale}

    except Exception as e:
        logger.error(f"Error detecting scam intent with LLM: {e}")
        return {"label": "Error", "rationale": f"LLM processing failed: {e}"}
