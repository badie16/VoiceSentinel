import asyncio
import openai
from typing import Dict, Any, List
import re
import logging
import json
import time
from functools import lru_cache
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from config import settings
from database import db_manager

logger = logging.getLogger(__name__)

class ScamDetector:
    def __init__(self):
        # Initialize OpenAI if API key is available
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.use_openai = True
            logger.info("OpenAI integration enabled")
        else:
            self.use_openai = False
            logger.warning("OpenAI API key not found, using fallback detection")
        
        # Initialize multilingual transformer model
        try:
            self.scam_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                tokenizer="microsoft/DialoGPT-medium"
            )
            logger.info("Loaded transformer model for scam detection")
        except Exception as e:
            logger.warning(f"Could not load transformer model: {e}")
            self.scam_classifier = None
        
        # Enhanced scam patterns by language
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
                r"cryptocurrency",
                r"bank.*security.*department",
                r"account.*compromised",
                r"unauthorized.*transaction",
                r"confirm.*identity",
                r"provide.*ssn",
                r"credit card.*expired",
                r"tech.*support.*virus",
                r"computer.*infected"
            ],
            "es": [
                r"verificar.*cuenta",
                r"cuenta.*suspendida",
                r"acción.*urgente",
                r"seguridad social",
                r"transferencia.*dinero",
                r"tarjeta.*regalo",
                r"soporte.*técnico",
                r"reembolso.*pendiente",
                r"banco.*seguridad",
                r"cuenta.*comprometida",
                r"transacción.*no.*autorizada",
                r"confirmar.*identidad",
                r"proporcionar.*número",
                r"tarjeta.*crédito.*vencida"
            ],
            "fr": [
                r"vérifier.*compte",
                r"compte.*suspendu",
                r"action.*urgente",
                r"sécurité sociale",
                r"transfert.*argent",
                r"carte.*cadeau",
                r"support.*technique",
                r"remboursement.*en.*attente",
                r"banque.*sécurité",
                r"compte.*compromis",
                r"transaction.*non.*autorisée",
                r"confirmer.*identité",
                r"fournir.*numéro",
                r"carte.*crédit.*expirée"
            ],
            "de": [
                r"konto.*verifizieren",
                r"konto.*gesperrt",
                r"sofortige.*aktion",
                r"sicherheit.*problem",
                r"geld.*überweisen",
                r"geschenkkarte",
                r"technischer.*support",
                r"rückerstattung.*ausstehend",
                r"bank.*sicherheit",
                r"konto.*kompromittiert"
            ],
            "it": [
                r"verificare.*conto",
                r"conto.*sospeso",
                r"azione.*immediata",
                r"problema.*sicurezza",
                r"trasferire.*denaro",
                r"carta.*regalo",
                r"supporto.*tecnico",
                r"rimborso.*in.*sospeso",
                r"banca.*sicurezza",
                r"conto.*compromesso"
            ]
        }
        
        # Enhanced pressure tactics indicators
        self.pressure_patterns = [
            r"act.*now",
            r"limited.*time",
            r"expires.*today",
            r"don't.*tell.*anyone",
            r"keep.*secret",
            r"immediately",
            r"urgent",
            r"emergency",
            r"right.*now",
            r"before.*it's.*too.*late",
            r"last.*chance",
            r"final.*notice",
            r"within.*24.*hours",
            r"call.*back.*immediately"
        ]
        
        # Personal information request patterns
        self.personal_info_patterns = [
            r"social.*security.*number",
            r"ssn",
            r"credit.*card.*number",
            r"bank.*account.*number",
            r"routing.*number",
            r"pin.*number",
            r"password",
            r"date.*of.*birth",
            r"mother.*maiden.*name",
            r"full.*name",
            r"address",
            r"phone.*number"
        ]
        
        logger.info("ScamDetector initialized")

    async def analyze_text(self, text: str, language: str) -> Dict[str, Any]:
        """Enhanced text analysis for scam detection"""
        try:
            if not text.strip():
                return self._empty_result()
            
            start_time = time.time()
            
            # 1. Pattern-based detection
            pattern_score = self._detect_scam_patterns(text, language)
            
            # 2. Pressure tactics detection
            pressure_score = self._detect_pressure_tactics(text)
            
            # 3. Personal information requests
            personal_info_score = self._detect_personal_info_requests(text)
            
            # 4. ML-based classification
            ml_score = await self._ml_classification(text)
            
            # 5. OpenAI GPT-4 analysis (if available)
            llm_score = await self._openai_analysis(text, language)
            
            # 6. Context-aware analysis
            context_score = self._analyze_context(text, language)
            
            # Combine scores with weights
            combined_score = self._combine_scores({
                "pattern": pattern_score,
                "pressure": pressure_score,
                "personal_info": personal_info_score,
                "ml": ml_score,
                "llm": llm_score,
                "context": context_score
            })
            
            # Get detailed indicators
            indicators = self._get_detailed_indicators(text, language)
            
            processing_time = time.time() - start_time
            
            return {
                "risk_score": combined_score,
                "indicators": indicators,
                "scores": {
                    "pattern_score": pattern_score,
                    "pressure_score": pressure_score,
                    "personal_info_score": personal_info_score,
                    "ml_score": ml_score,
                    "llm_score": llm_score,
                    "context_score": context_score
                },
                "processing_time": processing_time,
                "confidence": self._calculate_detection_confidence(combined_score, indicators)
            }
            
        except Exception as e:
            logger.error(f"Scam analysis error: {str(e)}")
            return self._empty_result()

    def _detect_scam_patterns(self, text: str, language: str) -> float:
        """Enhanced pattern detection with database patterns"""
        text_lower = text.lower()
        
        # Get patterns from database
        db_patterns = db_manager.get_scam_patterns(language)
        
        # Combine with built-in patterns
        patterns = self.scam_patterns.get(language, self.scam_patterns["en"])
        
        matches = 0
        weighted_score = 0.0
        
        # Check built-in patterns
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches += 1
                weighted_score += 1.0
        
        # Check database patterns with weights
        for db_pattern in db_patterns:
            if re.search(db_pattern.pattern.lower(), text_lower):
                matches += 1
                weighted_score += db_pattern.weight
        
        total_patterns = len(patterns) + len(db_patterns)
        if total_patterns == 0:
            return 0.0
        
        # Calculate score with amplification for multiple matches
        base_score = (weighted_score / total_patterns) * 100
        amplified_score = min(100.0, base_score * (1 + matches * 0.2))
        
        return amplified_score

    def _detect_pressure_tactics(self, text: str) -> float:
        """Enhanced pressure tactics detection"""
        text_lower = text.lower()
        matches = 0
        intensity_multiplier = 1.0
        
        for pattern in self.pressure_patterns:
            if re.search(pattern, text_lower):
                matches += 1
                
                # Increase intensity for certain high-pressure words
                if any(word in pattern for word in ["immediately", "urgent", "emergency"]):
                    intensity_multiplier += 0.3
        
        base_score = (matches / len(self.pressure_patterns)) * 100
        final_score = min(100.0, base_score * intensity_multiplier * 2.5)
        
        return final_score

    def _detect_personal_info_requests(self, text: str) -> float:
        """Detect requests for personal information"""
        text_lower = text.lower()
        matches = 0
        
        for pattern in self.personal_info_patterns:
            if re.search(pattern, text_lower):
                matches += 1
        
        # Personal info requests are highly suspicious
        score = min(100.0, (matches / len(self.personal_info_patterns)) * 100 * 4)
        return score

    async def _ml_classification(self, text: str) -> float:
        """Enhanced ML-based scam classification"""
        try:
            if not self.scam_classifier:
                return 0.0
            
            # Use the classifier to detect suspicious content
            result = self.scam_classifier(text)
            
            if isinstance(result, list) and len(result) > 0:
                # Extract confidence score
                confidence = result[0].get("score", 0.0)
                label = result[0].get("label", "")
                
                # Map labels to scam probability
                if "TOXIC" in label.upper() or "NEGATIVE" in label.upper():
                    return confidence * 100
                
            return 0.0
            
        except Exception as e:
            logger.error(f"ML classification error: {str(e)}")
            return 0.0

    async def _openai_analysis(self, text: str, language: str) -> float:
        """Advanced OpenAI GPT-4 analysis for scam detection"""
        try:
            if not self.use_openai:
                return 0.0
            
            # Create comprehensive prompt
            prompt = f"""
            Analyze this phone call transcript for scam indicators. Be very precise.
            
            Language: {language}
            Transcript: "{text}"
            
            Evaluate for:
            1. Urgency and pressure tactics
            2. Requests for personal/financial information
            3. Impersonation of legitimate organizations
            4. Suspicious payment methods (gift cards, wire transfers, crypto)
            5. Threats or fear-inducing language
            6. Technical support scam indicators
            7. Romance/relationship scam patterns
            
            Rate the scam probability from 0-100 and provide reasoning.
            Format: SCORE: [number] REASON: [brief explanation]
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert scam detection analyst. Provide accurate, concise assessments."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1,
                timeout=10
            )
            
            result_text = response.choices[0].message.content
            
            # Extract score from response
            score_match = re.search(r"SCORE:\s*(\d+)", result_text)
            if score_match:
                score = float(score_match.group(1))
                return min(100.0, max(0.0, score))
            
            return 0.0
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {str(e)}")
            return 0.0

    def _analyze_context(self, text: str, language: str) -> float:
        """Context-aware analysis based on conversation flow"""
        text_lower = text.lower()
        context_score = 0.0
        
        # Check for conversation flow indicators
        if re.search(r"hello.*this.*is.*from", text_lower):
            context_score += 20  # Cold call introduction
        
        if re.search(r"we.*detected.*problem", text_lower):
            context_score += 30  # Problem notification
        
        if re.search(r"need.*to.*verify", text_lower):
            context_score += 25  # Verification request
        
        if re.search(r"account.*will.*be.*closed", text_lower):
            context_score += 35  # Threat of account closure
        
        # Check for legitimate business patterns (reduce score)
        if re.search(r"appointment.*confirmation", text_lower):
            context_score -= 20
        
        if re.search(r"thank.*you.*for.*calling", text_lower):
            context_score -= 15
        
        return min(100.0, max(0.0, context_score))

    def _combine_scores(self, scores: Dict[str, float]) -> float:
        """Enhanced score combination with dynamic weights"""
        # Dynamic weights based on score reliability
        weights = {
            "pattern": 0.25,
            "pressure": 0.20,
            "personal_info": 0.25,
            "ml": 0.10,
            "llm": 0.15 if self.use_openai else 0.0,
            "context": 0.15
        }
        
        # Redistribute weights if OpenAI is not available
        if not self.use_openai:
            weights["pattern"] += 0.05
            weights["pressure"] += 0.05
            weights["personal_info"] += 0.05
        
        # Calculate weighted score
        combined = sum(scores[key] * weights[key] for key in weights.keys())
        
        # Apply amplification for high-confidence detections
        high_scores = [score for score in scores.values() if score > 70]
        if len(high_scores) >= 2:
            combined *= 1.2  # Amplify if multiple high scores
        
        return min(100.0, max(0.0, combined))

    def _get_detailed_indicators(self, text: str, language: str) -> List[Dict[str, Any]]:
        """Get detailed list of detected scam indicators"""
        indicators = []
        text_lower = text.lower()
        
        # Check scam patterns
        patterns = self.scam_patterns.get(language, self.scam_patterns["en"])
        for pattern in patterns:
            if re.search(pattern, text_lower):
                indicators.append({
                    "type": "scam_pattern",
                    "pattern": pattern,
                    "severity": "high",
                    "description": f"Detected scam pattern: {pattern}"
                })
        
        # Check pressure tactics
        for pattern in self.pressure_patterns:
            if re.search(pattern, text_lower):
                indicators.append({
                    "type": "pressure_tactic",
                    "pattern": pattern,
                    "severity": "medium",
                    "description": f"Pressure tactic detected: {pattern}"
                })
        
        # Check personal info requests
        for pattern in self.personal_info_patterns:
            if re.search(pattern, text_lower):
                indicators.append({
                    "type": "personal_info_request",
                    "pattern": pattern,
                    "severity": "high",
                    "description": f"Personal information request: {pattern}"
                })
        
        return indicators[:10]  # Limit to top 10 indicators

    def _calculate_detection_confidence(self, risk_score: float, indicators: List[Dict]) -> float:
        """Calculate confidence in the detection result"""
        base_confidence = 50.0
        
        # Increase confidence based on risk score
        if risk_score > 80:
            base_confidence += 30
        elif risk_score > 60:
            base_confidence += 20
        elif risk_score > 40:
            base_confidence += 10
        
        # Increase confidence based on number of indicators
        indicator_bonus = min(20, len(indicators) * 3)
        base_confidence += indicator_bonus
        
        # Increase confidence if using OpenAI
        if self.use_openai:
            base_confidence += 10
        
        return min(100.0, base_confidence)

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty analysis result"""
        return {
            "risk_score": 0.0,
            "indicators": [],
            "scores": {
                "pattern_score": 0.0,
                "pressure_score": 0.0,
                "personal_info_score": 0.0,
                "ml_score": 0.0,
                "llm_score": 0.0,
                "context_score": 0.0
            },
            "processing_time": 0.0,
            "confidence": 0.0
        }
