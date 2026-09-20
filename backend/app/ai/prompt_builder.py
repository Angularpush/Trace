"""
TRACE - Evidence Grounding Prompt Builder
Constructs strict, factual prompts containing ONLY verified evidence snippets.
Prevents financial calculation by the LLM and prevents hallucinations.
"""

from typing import Dict, List, Any

class GroundedPromptBuilder:
    @staticmethod
    def build_discrepancy_explanation_prompt(
        discrepancy: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        transaction_context: Dict[str, Any]
    ) -> str:
        evidence_text = ""
        for i, ev in enumerate(evidence_items, 1):
            evidence_text += (
                f"Evidence {i}:\n"
                f"  - Document: {ev.get('document_name', 'Unknown')}\n"
                f"  - Field: {ev.get('field_name', 'Unknown')}\n"
                f"  - Extracted Value: {ev.get('exact_value', '')}\n"
                f"  - Verbatim Snippet: \"{ev.get('snippet', '')}\"\n"
            )

        if not evidence_text.strip():
            evidence_text = "No direct source snippet available."

        prompt = f"""You are TRACE AI, an expert MSME financial reconciliation decision-support assistant.

CRITICAL INSTRUCTIONS:
1. Ground your explanation EXCLUSIVELY in the provided verified evidence.
2. Do NOT invent financial numbers, dates, or vendor names.
3. Do NOT re-calculate math; state the pre-calculated variance clearly.
4. If the provided evidence is empty or contradictory, output exactly: "Insufficient evidence to determine this discrepancy."
5. Provide a concise, professional explanation for human auditor review (2-4 sentences).

TRANSACTION CONTEXT:
- Transaction Reference: {transaction_context.get('transaction_ref', 'N/A')}
- Supplier: {transaction_context.get('supplier_name', 'N/A')}
- Buyer: {transaction_context.get('customer_name', 'N/A')}

DISCREPANCY DETAILS:
- Type: {discrepancy.get('rule_code')} ({discrepancy.get('discrepancy_type')})
- Title: {discrepancy.get('title')}
- Description: {discrepancy.get('description')}
- Calculated Variance: INR {discrepancy.get('difference_amount', 0.0)}
- Severity: {discrepancy.get('severity')} | Confidence: {discrepancy.get('confidence')}

VERIFIED SOURCE EVIDENCE:
{evidence_text}

Provide your grounded audit explanation:"""
        return prompt

    @staticmethod
    def build_reconciliation_summary_prompt(
        transaction_ref: str,
        discrepancies: List[Dict[str, Any]],
        documents_summary: List[Dict[str, Any]],
        financial_variance: float
    ) -> str:
        docs_text = "\n".join([
            f"- {d.get('doc_type')}: {d.get('filename')} (Status: {d.get('status', 'OK')})"
            for d in documents_summary
        ])

        discs_text = "\n".join([
            f"- [{d.get('severity')}] {d.get('title')} (Variance: INR {d.get('difference_amount', 0.0)})"
            for d in discrepancies
        ]) if discrepancies else "No discrepancies detected. All documents reconciled perfectly."

        prompt = f"""You are TRACE AI. Summarize this MSME multi-document financial reconciliation audit.

TRANSACTION REF: {transaction_ref}
DOCUMENTS INVOLVED:
{docs_text}

TOTAL NET FINANCIAL VARIANCE: INR {financial_variance:.2f}
DISCREPANCIES FOUND ({len(discrepancies)} total):
{discs_text}

INSTRUCTIONS:
- Provide an executive 1-paragraph summary highlighting key risks, unearned charges, or reconciliation status.
- Be factual and concise for business owners and accounts managers."""
        return prompt
