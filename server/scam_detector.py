import asyncio
import openai
from typing import Dict, Any, List
import re
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

class ScamDetector:
    def __init__(self):
        # Initialize multilingual scam detection model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
            self.scam_classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                tokenizer="unitary/toxic-bert"
            )
        except Exception as e:
            logger.warning(f"Could not load transformer model: {e}")
            self.scam_classifier = None
        
        # Scam indicators by language
        self.scam_patterns = {
            "en": [
                r"verify your account",
                r"suspended.*account",
                r"click.*link.*immediately",
                r"urgent.*action.*required",
                r"social security.*suspended",
                r"IRS.*lawsuit",
                r"microsoft.*support",
                r"refund.*pending",
                r"gift card",
                r"wire transfer",
                r"bitcoin",
                r"cryptocurrency"
            ],
            "es": [
                r"verificar.*cuenta",
                r"cuenta.*suspendida",
                r"acción.*urgente",
                r"seguridad social",
                r"transferencia.*dinero",
                r"tarjeta.*regalo",
                r"soporte.*técnico",
                r"reembolso.*pendiente"
            ],
            "fr": [
                r"vérifier.*compte",
                r"compte.*suspendu",
                r"action.*urgente",
                r"sécurité sociale",
                r"transfert.*argent",
                r"carte.*cadeau",
                r"support.*technique",
                r"remboursement.*en.*attente"
            ]
        }
        
        # Pressure tactics indicators
        self.pressure_patterns = [
            r"act.*now",
            r"limited.*time",
            r"expires.*today",
            r"don't.*tell.*anyone",
            r"keep.*secret",
            r"immediately",
            r"urgent",
            r"emergency"
        ]
        
        logger.info("ScamDetector initialized")

    async def analyze_text(self, text: str, language: str) -> Dict[str, Any]:
        """Analyze text for scam indicators"""
        try:
            if not text.strip():
                return self._empty_result()
            
            # 1. Pattern-based detection
            pattern_score = self._detect_scam_patterns(text, language)
            
            # 2. Pressure tactics detection
            pressure_score = self._detect_pressure_tactics(text)
            
            # 3. ML-based classification (if available)
            ml_score = await self._ml_classification(text)
            
            # 4. LLM-based analysis (placeholder for GPT integration)
            llm_score = await self._llm_analysis(text, language)
            
            # Combine scores
            combined_score = self._combine_scores(pattern_score, pressure_score, ml_score, llm_score)
            
            # Get indicators
            indicators = self._get_indicators(text, language)
            
            return {
                "risk_score": combined_score,
                "indicators": indicators,
                "pattern_score": pattern_score,
                "pressure_score": pressure_score,
                "ml_score": ml_score,
                "llm_score": llm_score
            }
            
        except Exception as e:
            logger.error(f"Scam analysis error: {str(e)}")
            return self._empty_result()

    def _detect_scam_patterns(self, text: str, language: str) -> float:
        """Detect scam patterns in text"""
        text_lower = text.lower()
        patterns = self.scam_patterns.get(language, self.scam_patterns["en"])
        
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches += 1
        
        # Score based on number of matches
        score = min(100.0, (matches / len(patterns)) * 100 * 2)  # Amplify score
        return score

    def _detect_pressure_tactics(self, text: str) -> float:
        """Detect pressure tactics in text"""
        text_lower = text.lower()
        matches = 0
        
        for pattern in self.pressure_patterns:
            if re.search(pattern, text_lower):
                matches += 1
        
        score = min(100.0, (matches / len(self.pressure_patterns)) * 100 * 3)
        return score

    async def _ml_classification(self, text: str) -> float:
        """ML-based scam classification"""
        try:
            if not self.scam_classifier:
                return 0.0
            
            # Use toxic classifier as proxy for suspicious content
            result = self.scam_classifier(text)
            
            if isinstance(result, list) and len(result) > 0:
                # Get toxicity score as scam indicator
                toxic_score = result[0].get("score", 0.0) if result[0].get("label") == "TOXIC" else 0.0
                return toxic_score * 100
            
            return 0.0
            
        except Exception as e:
            logger.error(f"ML classification error: {str(e)}")
            return 0.0

    async def _llm_analysis(self, text: str, language: str) -> float:
        """LLM-based scam analysis (placeholder)"""
        try:
            # Placeholder for GPT/Claude integration
            # In real implementation, send text to LLM with scam detection prompt
            
            # Simple heuristic for now
            suspicious_words = ["verify", "account", "suspended", "urgent", "immediately", "click", "link"]
            word_count = sum(1 for word in suspicious_words if word.lower() in text.lower())
            
            score = min(100.0, (word_count / len(suspicious_words)) * 100)
            return score
            
        except Exception as e:
            logger.error(f"LLM analysis error: {str(e)}")
            return 0.0

    def _combine_scores(self, pattern: float, pressure: float, ml: float, llm: float) -> float:
        """Combine different analysis scores"""
        # Weighted combination
        weights = {"pattern": 0.3, "pressure": 0.2, "ml": 0.3, "llm": 0.2}
        
        combined = (
            pattern * weights["pattern"] +
            pressure * weights["pressure"] +
            ml * weights["ml"] +
            llm * weights["llm"]
        )
        
        return min(100.0, max(0.0, combined))

    def _get_indicators(self, text: str, language: str) -> List[str]:
        """Get list of detected scam indicators"""
        indicators = []
        text_lower = text.lower()
        
        # Check scam patterns
        patterns = self.scam_patterns.get(language, self.scam_patterns["en"])
        for pattern in patterns:
            if re.search(pattern, text_lower):
                indicators.append(f"Scam pattern: {pattern}")
        
        # Check pressure tactics
        for pattern in self.pressure_patterns:
            if re.search(pattern, text_lower):
                indicators.append(f"Pressure tactic: {pattern}")
        
        return indicators[:5]  # Limit to top 5 indicators

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty analysis result"""
        return {
            "risk_score": 0.0,
            "indicators": [],
            "pattern_score": 0.0,
            "pressure_score": 0.0,
            "ml_score": 0.0,
            "llm_score": 0.0
        }
