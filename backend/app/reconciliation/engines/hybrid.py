"""
TRACE - Hybrid Reconciliation Engine
Combines deterministic rules, semantic vector matching, and LLM reasoning.
- Step 1: Deterministic rules for strict Decimal arithmetic & compliance.
- Step 2: Semantic vector embeddings (FAISS) for fuzzy item & entity alignment.
- Step 3: LLM reasoning for edge case interpretation and contextual anomaly detection.
- Multi-Source Fusion: Integrates findings across all 3 layers with distinct provenance:
  'hybrid' (fused rule + LLM), 'semantic' (embedding matcher), 'rule' (math only), 'llm' (reasoning only).
"""

import time
import re
from typing import Dict, Any, List
from decimal import Decimal

from app.reconciliation.engines.base import (
    BaseReconciliationEngine,
    EngineResult,
    EngineFinding,
    EngineEvidence
)
from app.reconciliation.engines.rule_based import rule_based_engine
from app.reconciliation.engines.ai_llm import ai_llm_engine
from app.semantic.matcher import semantic_matcher
from app.ai.offline_provider import OfflineProvider
from app.ai import get_llm_provider
from app.extraction.normalizer import clean_entity_name

class HybridReconciliationEngine(BaseReconciliationEngine):
    """
    Synergistic hybrid reconciliation engine with multi-source provenance tracking.
    """

    @property
    def approach_name(self) -> str:
        return "HYBRID"

    def reconcile(self, transaction_data: Dict[str, Any]) -> EngineResult:
        start_time = time.perf_counter()
        findings: List[EngineFinding] = []
        cost_usd = 0.0

        # -------------------------------------------------------------
        # Step 1: Deterministic Mathematical Rules (Math & Hard Logic)
        # -------------------------------------------------------------
        rule_result = rule_based_engine.reconcile(transaction_data)
        rule_findings = rule_result.findings

        # -------------------------------------------------------------
        # Step 2: Semantic Vector Embedding Analysis (Fuzzy Entities & Items)
        # -------------------------------------------------------------
        semantic_findings: List[EngineFinding] = []
        docs = transaction_data.get("documents", [])
        docs_by_type = {}
        for d in docs:
            dt = d.get("document_type") or d.get("doc_type", "OTHER")
            docs_by_type[dt] = d

        po_doc = docs_by_type.get("PURCHASE_ORDER", {})
        inv_doc = docs_by_type.get("INVOICE", {})
        dn_doc = docs_by_type.get("DELIVERY_NOTE", {})

        # 2a. Check Semantic Supplier Entity Variance
        po_supp = po_doc.get("parsed_data", {}).get("supplier_name", "")
        inv_supp = inv_doc.get("parsed_data", {}).get("supplier_name", "")
        if po_supp and inv_supp and po_supp.strip().lower() != inv_supp.strip().lower():
            sim, is_match = semantic_matcher.match_supplier(po_supp, inv_supp)
            if not is_match or sim < 0.85:
                semantic_findings.append(EngineFinding(
                    discrepancy_type="SUPPLIER_MISMATCH",
                    severity="HIGH",
                    expected_value=po_supp,
                    actual_value=inv_supp,
                    difference_value=f"Semantic similarity: {sim:.2%}",
                    explanation=(
                        f"Semantic entity mismatch: Purchase Order supplier '{po_supp}' differs from "
                        f"Invoice supplier '{inv_supp}' (Embedding similarity: {sim:.2%}, below 85% threshold)."
                    ),
                    confidence=round(1.0 - sim, 2),
                    evidence=[
                        EngineEvidence(
                            document_id=po_doc.get("id", "PO"),
                            document_name=po_doc.get("filename", "PO.pdf"),
                            field_name="supplier_name",
                            exact_value=po_supp,
                            snippet=f"PO Supplier: {po_supp}"
                        ),
                        EngineEvidence(
                            document_id=inv_doc.get("id", "INV"),
                            document_name=inv_doc.get("filename", "Invoice.pdf"),
                            field_name="supplier_name",
                            exact_value=inv_supp,
                            snippet=f"Invoice Supplier: {inv_supp}"
                        )
                    ],
                    source_documents=[po_doc.get("id", "PO"), inv_doc.get("id", "INV")],
                    provenance="semantic",
                    title="Semantic Supplier Entity Variance"
                ))

        # 2b. Check Semantic Line Item Discrepancies
        po_items = po_doc.get("parsed_data", {}).get("items", []) or []
        inv_items = inv_doc.get("parsed_data", {}).get("items", []) or []
        aligned = semantic_matcher.align_line_items(po_items, inv_items)

        for al in aligned:
            p_it = al.get("po_item")
            i_it = al.get("invoice_item")
            if p_it and i_it:
                score = al.get("match_score", 1.0)
                if 0.50 <= score < 0.85:
                    semantic_findings.append(EngineFinding(
                        discrepancy_type="ITEM_MISMATCH",
                        severity="MEDIUM",
                        expected_value=p_it.get("description", ""),
                        actual_value=i_it.get("description", ""),
                        difference_value=f"Match score: {score:.2%}",
                        explanation=(
                            f"Fuzzy item description divergence between PO ('{p_it.get('description')}') and "
                            f"Invoice ('{i_it.get('description')}'). Semantic similarity {score:.2%} indicates potential specification deviation."
                        ),
                        confidence=round(score, 2),
                        evidence=[
                            EngineEvidence(
                                document_id=po_doc.get("id", "PO"),
                                document_name=po_doc.get("filename", "PO.pdf"),
                                field_name="item_description",
                                exact_value=p_it.get("description", ""),
                                snippet=p_it.get("description", "")
                            ),
                            EngineEvidence(
                                document_id=inv_doc.get("id", "INV"),
                                document_name=inv_doc.get("filename", "Invoice.pdf"),
                                field_name="item_description",
                                exact_value=i_it.get("description", ""),
                                snippet=i_it.get("description", "")
                            )
                        ],
                        source_documents=[po_doc.get("id", "PO"), inv_doc.get("id", "INV")],
                        provenance="semantic",
                        title=f"Semantic Item Divergence: {p_it.get('description', 'Item')}"
                    ))

        # -------------------------------------------------------------
        # Step 3: AI / LLM Contextual Reasoning
        # -------------------------------------------------------------
        ai_result = ai_llm_engine.reconcile(transaction_data)
        ai_findings = ai_result.findings
        cost_usd += ai_result.cost_usd

        # -------------------------------------------------------------
        # Step 4: Multi-Source Synergistic Fusion
        # -------------------------------------------------------------
        offline_auditor = OfflineProvider()
        active_llm = get_llm_provider()

        # Map findings by discrepancy_type
        ai_findings_by_type: Dict[str, List[EngineFinding]] = {}
        for af in ai_findings:
            ai_findings_by_type.setdefault(af.discrepancy_type, []).append(af)

        used_ai_types = set()

        # 4a. Process Rule Findings & Fuse with Matching AI Discoveries
        for rf in rule_findings:
            matching_ai = ai_findings_by_type.get(rf.discrepancy_type)
            if matching_ai:
                # FUSED HYBRID DISCOVERY (Rule math + AI contextual reasoning)
                used_ai_types.add(rf.discrepancy_type)
                ai_match = matching_ai[0]

                # Synthesize explanation safely
                fused_expl = ai_match.explanation or rf.explanation
                if "error" in fused_expl.lower() or "openai api" in fused_expl.lower():
                    disc_dict = {
                        "rule_code": rf.rule_code or rf.discrepancy_type,
                        "title": rf.title or rf.discrepancy_type,
                        "description": rf.explanation,
                        "difference_amount": getattr(rf, "difference_amount", 0.0),
                        "severity": rf.severity,
                        "expected_value": rf.expected_value,
                        "actual_value": rf.actual_value,
                        "difference_value": rf.difference_value,
                        "metadata": {}
                    }
                    ev_dicts = [e.to_dict() for e in rf.evidence]
                    fused_expl = offline_auditor.generate_explanation(disc_dict, ev_dicts, transaction_data) or rf.explanation

                # Combine evidence citations
                combined_ev = list(rf.evidence)
                for a_ev in ai_match.evidence:
                    if not any(e.field_name == a_ev.field_name and e.exact_value == a_ev.exact_value for e in combined_ev):
                        combined_ev.append(a_ev)

                findings.append(EngineFinding(
                    rule_code=rf.rule_code,
                    discrepancy_type=rf.discrepancy_type,
                    severity=rf.severity,
                    confidence=max(rf.confidence, ai_match.confidence),
                    expected_value=rf.expected_value or ai_match.expected_value,
                    actual_value=rf.actual_value or ai_match.actual_value,
                    difference_value=rf.difference_value or ai_match.difference_value,
                    difference_amount=getattr(rf, "difference_amount", 0.0),
                    explanation=fused_expl,
                    evidence=combined_ev,
                    source_documents=list(set(rf.source_documents + ai_match.source_documents)),
                    provenance="hybrid",
                    title=f"Hybrid Consensus: {rf.discrepancy_type.replace('_', ' ').title()}"
                ))
            else:
                # Pure Rule finding (safe explanation)
                safe_expl = rf.explanation
                if "error" in safe_expl.lower() or "openai api" in safe_expl.lower():
                    disc_dict = {
                        "rule_code": rf.rule_code or rf.discrepancy_type,
                        "title": rf.title or rf.discrepancy_type,
                        "description": "",
                        "difference_amount": getattr(rf, "difference_amount", 0.0),
                        "severity": rf.severity,
                        "expected_value": rf.expected_value,
                        "actual_value": rf.actual_value,
                        "difference_value": rf.difference_value,
                        "metadata": {}
                    }
                    ev_dicts = [e.to_dict() for e in rf.evidence]
                    safe_expl = offline_auditor.generate_explanation(disc_dict, ev_dicts, transaction_data) or rf.explanation
                rf.explanation = safe_expl
                findings.append(rf)

        # 4b. Add Semantic Embeddings Discoveries
        for sf in semantic_findings:
            if not any(f.discrepancy_type == sf.discrepancy_type and f.expected_value == sf.expected_value for f in findings):
                findings.append(sf)

        # 4c. Add Unique AI / LLM Reasoning Discoveries (not captured by rules)
        for af in ai_findings:
            if af.discrepancy_type not in used_ai_types and not any(f.discrepancy_type == af.discrepancy_type for f in findings):
                safe_af_expl = af.explanation
                if "error" in safe_af_expl.lower() or "openai api" in safe_af_expl.lower():
                    disc_dict = {
                        "rule_code": af.discrepancy_type,
                        "title": af.title,
                        "description": "",
                        "difference_amount": 0.0,
                        "severity": af.severity,
                        "expected_value": af.expected_value,
                        "actual_value": af.actual_value,
                        "difference_value": af.difference_value,
                        "metadata": {}
                    }
                    ev_dicts = [e.to_dict() for e in af.evidence]
                    safe_af_expl = offline_auditor.generate_explanation(disc_dict, ev_dicts, transaction_data) or "AI identified document discrepancy."
                af.explanation = safe_af_expl
                findings.append(af)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        overall_result = "DISCREPANCIES_FOUND" if findings else "RECONCILED"

        hybrid_count = sum(1 for f in findings if f.provenance == "hybrid")
        rule_count = sum(1 for f in findings if f.provenance == "rule")
        sem_count = sum(1 for f in findings if f.provenance == "semantic")
        llm_count = sum(1 for f in findings if f.provenance == "llm")

        summary_text = (
            f"Hybrid reconciliation completed in {elapsed_ms:.2f}ms (Total cost: ${cost_usd:.6f}). "
            f"Synthesized {len(findings)} findings across engines "
            f"(Hybrid Fused: {hybrid_count}, Rules: {rule_count}, Semantic: {sem_count}, LLM: {llm_count})."
        )

        return EngineResult(
            approach=self.approach_name,
            overall_result=overall_result,
            execution_time_ms=round(elapsed_ms, 2),
            cost_usd=round(cost_usd, 6),
            findings=findings,
            model_version="hybrid-v1.0.0",
            configuration={
                "rule_engine": "deterministic_v1",
                "semantic_matcher": "sentence_transformers_faiss",
                "llm_provider": active_llm.provider_name
            },
            summary_text=summary_text
        )

hybrid_engine = HybridReconciliationEngine()
