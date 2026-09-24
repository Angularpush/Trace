"""
TRACE - Reconciliation Comparator
Runs all three approaches (RULE_BASED, AI_LLM, HYBRID) against the same transaction,
evaluates agreement and conflict rates, compares execution time and cost,
and persists ReconciliationRun & ReconciliationFinding records.
"""

import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.reconciliation.engines.base import EngineResult, EngineFinding
from app.reconciliation.engines.rule_based import rule_based_engine
from app.reconciliation.engines.ai_llm import ai_llm_engine
from app.reconciliation.engines.hybrid import hybrid_engine

class ReconciliationComparator:
    """
    Executes and benchmarks the 3 approaches on a single transaction.
    """

    @classmethod
    def compare_transaction(cls, transaction_data: Dict[str, Any], db=None) -> Dict[str, Any]:
        """
        Runs RULE_BASED, AI_LLM, and HYBRID engines on the same transaction data,
        aligns findings, and saves runs if db session is provided.
        """
        txn_id = transaction_data.get("id") or transaction_data.get("transaction_id", "txn_unknown")
        txn_ref = transaction_data.get("transaction_reference") or transaction_data.get("transaction_ref", "TXN")

        # 1. Execute All 3 Engines
        rule_result = rule_based_engine.reconcile(transaction_data)
        ai_result = ai_llm_engine.reconcile(transaction_data)
        hybrid_result = hybrid_engine.reconcile(transaction_data)

        # 2. Analyze Alignment & Agreement
        rule_types = {f.discrepancy_type for f in rule_result.findings}
        ai_types = {f.discrepancy_type for f in ai_result.findings}
        hybrid_types = {f.discrepancy_type for f in hybrid_result.findings}

        all_types = rule_types | ai_types | hybrid_types

        # Consensus: detected by at least 2 approaches
        consensus_types = []
        conflicting_types = []

        for dt in all_types:
            votes = sum([1 for st in [rule_types, ai_types, hybrid_types] if dt in st])
            if votes >= 2:
                consensus_types.append(dt)
            else:
                conflicting_types.append(dt)

        # Jaccard Agreement Score across 3 sets
        intersection = rule_types & ai_types & hybrid_types
        union = all_types
        if not union:
            agreement_score = 1.0  # Both agree fully that there are 0 discrepancies
        else:
            agreement_score = len(intersection) / len(union) if union else 1.0

        # Latency & Cost Comparison
        latency_comp = {
            "RULE_BASED": rule_result.execution_time_ms,
            "AI_LLM": ai_result.execution_time_ms,
            "HYBRID": hybrid_result.execution_time_ms
        }
        cost_comp = {
            "RULE_BASED": rule_result.cost_usd,
            "AI_LLM": ai_result.cost_usd,
            "HYBRID": hybrid_result.cost_usd
        }

        # Synthesize Explanation Summary
        summary = (
            f"3-Way Reconciliation Comparison for {txn_ref}: "
            f"Rule-Based detected {len(rule_result.findings)} issue(s) in {rule_result.execution_time_ms:.1f}ms ($0.00). "
            f"AI/LLM detected {len(ai_result.findings)} issue(s) in {ai_result.execution_time_ms:.1f}ms (${ai_result.cost_usd:.5f}). "
            f"Hybrid detected {len(hybrid_result.findings)} issue(s) in {hybrid_result.execution_time_ms:.1f}ms (${hybrid_result.cost_usd:.5f}). "
            f"Consensus overlap score: {agreement_score:.2%}."
        )

        def _format_run_payload(res: EngineResult) -> Dict[str, Any]:
            d = res.to_dict()
            run_uuid = f"run_{uuid.uuid4().hex[:10]}"
            d["id"] = run_uuid
            d["transaction_id"] = txn_id
            d["run_time"] = datetime.utcnow().isoformat()
            d["findings_count"] = len(res.findings)
            for f_dict in d.get("findings", []):
                if not f_dict.get("id"):
                    f_dict["id"] = f"fnd_{uuid.uuid4().hex[:10]}"
                if not f_dict.get("reconciliation_run_id"):
                    f_dict["reconciliation_run_id"] = run_uuid
            return d

        comparison_payload = {
            "transaction_id": txn_id,
            "transaction_reference": txn_ref,
            "rule_based_run": _format_run_payload(rule_result),
            "ai_llm_run": _format_run_payload(ai_result),
            "hybrid_run": _format_run_payload(hybrid_result),
            "agreement_score": round(agreement_score, 4),
            "consensus_discrepancies": consensus_types,
            "conflicting_discrepancies": conflicting_types,
            "latency_comparison": latency_comp,
            "cost_comparison": cost_comp,
            "explanation_summary": summary
        }

        # 3. Persist to Database if DB Session Provided
        if db is not None:
            cls._persist_runs_and_findings(txn_id, [rule_result, ai_result, hybrid_result], db)

        return comparison_payload

    @classmethod
    def _persist_runs_and_findings(cls, transaction_id: str, results: List[EngineResult], db):
        from app.models.reconciliation import ReconciliationRun, ReconciliationFinding
        from app.models.transaction import Transaction
        from app.models.discrepancy import Discrepancy, Evidence

        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()

        for res in results:
            run_id = f"run_{uuid.uuid4().hex[:10]}"
            db_run = ReconciliationRun(
                id=run_id,
                transaction_id=transaction_id,
                approach=res.approach,
                run_time=datetime.utcnow(),
                model_version=res.model_version,
                configuration=res.configuration,
                overall_result=res.overall_result,
                execution_time_ms=res.execution_time_ms,
                cost_usd=res.cost_usd,
                findings_count=len(res.findings)
            )
            db.add(db_run)
            db.flush()

            for f in res.findings:
                finding_id = f"fnd_{uuid.uuid4().hex[:10]}"
                db_finding = ReconciliationFinding(
                    id=finding_id,
                    reconciliation_run_id=run_id,
                    discrepancy_type=f.discrepancy_type,
                    severity=f.severity,
                    expected_value=f.expected_value,
                    actual_value=f.actual_value,
                    difference_value=f.difference_value,
                    explanation=f.explanation,
                    confidence=f.confidence,
                    evidence=[e.to_dict() for e in f.evidence],
                    source_documents=f.source_documents,
                    provenance=f.provenance
                )
                db.add(db_finding)

                # Also synchronize to legacy Discrepancy table for backwards compatibility
                if res.approach == "HYBRID" and txn:
                    disc_id = f"disc_{uuid.uuid4().hex[:10]}"
                    diff_amt = float(getattr(f, "difference_amount", 0.0) or 0.0)
                    if not diff_amt and f.difference_value:
                        try:
                            clean_str = re.sub(r"[^\d.-]", "", str(f.difference_value))
                            if clean_str:
                                diff_amt = abs(float(clean_str))
                        except Exception:
                            diff_amt = 0.0

                    db_disc = Discrepancy(
                        id=disc_id,
                        transaction_id=transaction_id,
                        rule_code=f.rule_code or f.discrepancy_type,
                        discrepancy_type=f.discrepancy_type,
                        severity=f.severity,
                        confidence=f.confidence,
                        title=f.title or f"Discrepancy: {f.discrepancy_type}",
                        description=f.explanation,
                        difference_amount=diff_amt,
                        expected_value=f.expected_value,
                        actual_value=f.actual_value,
                        difference_value=f.difference_value,
                        llm_explanation=f.explanation,
                        status="OPEN"
                    )
                    db.add(db_disc)
                    db.flush()

                    for ev in f.evidence:
                        db_ev = Evidence(
                            id=f"ev_{uuid.uuid4().hex[:10]}",
                            discrepancy_id=disc_id,
                            document_id=ev.document_id or "DOC",
                            document_name=ev.document_name or "Document",
                            page_number=ev.page_number,
                            field_name=ev.field_name or "discrepancy",
                            exact_value=ev.exact_value or "",
                            snippet=ev.snippet,
                            relevance_score=ev.relevance_score
                        )
                        db.add(db_ev)

        if txn:
            has_issues = any(len(r.findings) > 0 for r in results)
            txn.status = "DISCREPANCY_FOUND" if has_issues else "RECONCILED"
            txn.reconciliation_status = txn.status

        db.commit()

reconciliation_comparator = ReconciliationComparator()
