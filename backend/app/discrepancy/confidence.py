"""
TRACE - Confidence Calculator
Deterministic confidence scoring (0.0 to 1.0) based on extraction quality,
exact identifier match, semantic similarity, evidence presence, and rule agreement.
The LLM does NOT invent confidence.
"""

from typing import Dict, Any, List

class ConfidenceCalculator:
    @staticmethod
    def calculate_confidence(
        extraction_confidence: float,
        has_exact_identifier_match: bool,
        semantic_similarity: float,
        evidence_count: int,
        rule_agreement: bool = True
    ) -> float:
        """
        Calculates normalized confidence:
        w1 * extraction_conf + w2 * id_match + w3 * semantic_sim + w4 * evidence_presence + w5 * agreement
        """
        # Weights
        w_ext = 0.25
        w_id = 0.25
        w_sem = 0.20
        w_ev = 0.20
        w_agr = 0.10

        id_score = 1.0 if has_exact_identifier_match else 0.5
        ev_score = min(1.0, evidence_count / 2.0)  # Max score if >= 2 pieces of evidence
        agr_score = 1.0 if rule_agreement else 0.5

        raw_conf = (
            w_ext * extraction_confidence +
            w_id * id_score +
            w_sem * semantic_similarity +
            w_ev * ev_score +
            w_agr * agr_score
        )

        return round(float(max(0.0, min(1.0, raw_conf))), 2)
