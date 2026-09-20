"""
TRACE - Reconciliation Master Orchestrator
Coordinates multi-document alignment, rule evaluation, evidence retrieval, and AI explanation generation.
Supports all 3 configurations: RULE_BASED, AI_ONLY, and HYBRID.
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.discrepancy.engine import discrepancy_engine
from app.semantic.matcher import semantic_matcher
from app.ai import get_llm_provider
from app.extraction.normalizer import normalize_decimal

class ReconciliationOrchestrator:
    @staticmethod
    def reconcile_transaction(
        transaction_ref: str,
        documents: List[Dict[str, Any]],
        mode: str = "HYBRID",
        llm_provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full reconciliation over a transaction document cluster.
        Modes:
        - RULE_BASED: Deterministic rules only, no semantic item match or LLM summaries.
        - AI_ONLY: Semantic similarity matching + LLM reasoning only, no strict Decimal rules.
        - HYBRID: Combined Decimal rules + FAISS/Semantic item alignment + traceable evidence + LLM explanation.
        """
        # Step 1: Map documents by type
        docs_by_type: Dict[str, Dict[str, Any]] = {}
        for doc in documents:
            d_type = doc.get("doc_type")
            if d_type and d_type != "UNKNOWN":
                docs_by_type[d_type] = doc

        # Extract transaction-level metadata
        supplier_name = ""
        customer_name = ""
        for doc in documents:
            p_data = doc.get("parsed_data", {})
            if not supplier_name and p_data.get("supplier_name"):
                supplier_name = p_data.get("supplier_name")
            if not customer_name and p_data.get("customer_name"):
                customer_name = p_data.get("customer_name")

        transaction_context = {
            "transaction_ref": transaction_ref,
            "supplier_name": supplier_name,
            "customer_name": customer_name,
            "documents_by_type": docs_by_type,
            "all_documents": documents
        }

        mode_upper = mode.upper()
        discrepancies: List[Dict[str, Any]] = []

        if mode_upper == "RULE_BASED":
            # Deterministic rules without semantic item tolerance
            raw_discrepancies = discrepancy_engine.run_reconciliation(transaction_context)
            for d in raw_discrepancies:
                d_dict = d.model_dump()
                d_dict["llm_explanation"] = d_dict["description"]  # Pure rule text
                discrepancies.append(d_dict)

        elif mode_upper == "AI_ONLY":
            # AI reasoning without strict mathematical Decimal checks
            # Simulates purely prompt/embedding-based discrepancy detection
            provider = get_llm_provider(llm_provider_name or "offline")
            # We check high-level semantic mismatches
            po_doc = docs_by_type.get("PURCHASE_ORDER")
            inv_doc = docs_by_type.get("INVOICE")
            if po_doc and inv_doc:
                po_data = po_doc.get("parsed_data", {})
                inv_data = inv_doc.get("parsed_data", {})
                po_supp = po_data.get("supplier_name", "")
                inv_supp = inv_data.get("supplier_name", "")
                sim, is_m = semantic_matcher.match_supplier(po_supp, inv_supp)
                if not is_m and po_supp and inv_supp:
                    discrepancies.append({
                        "rule_code": "SUPPLIER_MISMATCH",
                        "discrepancy_type": "UNMATCHED_SUPPLIER",
                        "title": f"Supplier Mismatch: '{po_supp}' vs '{inv_supp}'",
                        "description": f"AI detected semantic divergence between supplier names ({sim:.2f}).",
                        "severity": "CRITICAL",
                        "confidence": 0.85,
                        "difference_amount": 0.0,
                        "evidences": [],
                        "llm_explanation": f"AI Reasoning: Supplier identity discrepancy between '{po_supp}' and '{inv_supp}'."
                    })

        else:  # HYBRID (Default & Recommended)
            # Full pipeline: Decimal Rules + Semantic Item Matching + Evidence + Grounded LLM
            raw_discrepancies = discrepancy_engine.run_reconciliation(transaction_context)
            provider = get_llm_provider(llm_provider_name or "offline")

            for d in raw_discrepancies:
                d_dict = d.model_dump()
                # Generate grounded explanation from evidence snippets
                ev_items = [ev.model_dump() if hasattr(ev, 'model_dump') else ev for ev in d.evidences]
                explanation = provider.generate_explanation(
                    discrepancy=d_dict,
                    evidence_items=ev_items,
                    transaction_context=transaction_context
                )
                d_dict["llm_explanation"] = explanation
                d_dict["difference_amount"] = float(d.difference_amount)
                discrepancies.append(d_dict)

        # Calculate Financial Variance and Status
        total_variance = sum(float(d.get("difference_amount", 0.0)) for d in discrepancies)
        
        # Determine Status
        if not discrepancies:
            reconciliation_status = "RECONCILED"
        else:
            has_critical = any(d.get("severity") == "CRITICAL" for d in discrepancies)
            has_high = any(d.get("severity") == "HIGH" for d in discrepancies)
            if has_critical or has_high:
                reconciliation_status = "DISCREPANCY_FOUND"
            else:
                reconciliation_status = "MINOR_VARIANCE"

        # Check document completeness
        essential_types = {"PURCHASE_ORDER", "INVOICE", "DELIVERY_NOTE"}
        present_types = set(docs_by_type.keys())
        if not essential_types.issubset(present_types) and reconciliation_status == "RECONCILED":
            reconciliation_status = "INCOMPLETE"

        # Generate Executive Summary
        provider = get_llm_provider(llm_provider_name or "offline")
        docs_summary = [
            {"filename": d.get("filename", "Doc"), "doc_type": d.get("doc_type", "UNKNOWN"), "status": "Processed"}
            for d in documents
        ]
        exec_summary = provider.generate_reconciliation_summary(
            transaction_ref=transaction_ref,
            discrepancies=discrepancies,
            documents_summary=docs_summary,
            financial_variance=total_variance
        )

        return {
            "transaction_ref": transaction_ref,
            "reconciliation_status": reconciliation_status,
            "mode_used": mode_upper,
            "supplier_name": supplier_name,
            "customer_name": customer_name,
            "total_documents": len(documents),
            "documents_summary": docs_summary,
            "total_discrepancies": len(discrepancies),
            "discrepancies_by_severity": {
                "CRITICAL": sum(1 for d in discrepancies if d.get("severity") == "CRITICAL"),
                "HIGH": sum(1 for d in discrepancies if d.get("severity") == "HIGH"),
                "MEDIUM": sum(1 for d in discrepancies if d.get("severity") == "MEDIUM"),
                "LOW": sum(1 for d in discrepancies if d.get("severity") == "LOW")
            },
            "financial_variance_amount": round(total_variance, 2),
            "discrepancies": discrepancies,
            "ai_grounded_explanation": exec_summary,
            "reconciled_at": datetime.utcnow().isoformat()
        }

reconciliation_orchestrator = ReconciliationOrchestrator()
