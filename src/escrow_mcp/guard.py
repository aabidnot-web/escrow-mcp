"""Pre-execution policy checks for the Escrow MCP Action Gateway."""

import hashlib
import time
from typing import Dict, Any, Tuple
from .bank_env import ERP_MASTER_LEDGER


class EscrowDecision:
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class EscrowGuard:
    """
    In-flight execution gate that evaluates a proposed tool call before runtime execution.
    """
    def __init__(self):
        self.audit_log = []

    def evaluate_transfer_action(
        self,
        task_intent: str,
        source_doc_id: str,
        source_origin: str,
        recipient: str,
        account_number: str,
        amount: float,
        reason: str
    ) -> Tuple[str, Dict[str, Any]]:
        evidence_hash = hashlib.sha256(
            f"{task_intent}:{recipient}:{account_number}:{amount}".encode()
        ).hexdigest()[:12]

        # Invariant 1: Task Scope Verification
        is_payment_task = any(kw in task_intent.lower() for kw in ["pay", "bill", "invoice", "settle", "disburse", "transfer"])
        if not is_payment_task:
            verdict = EscrowDecision.BLOCK
            explanation = f"Task drift detected: Stated intent '{task_intent}' does not authorize wire transfer executions."
            return self._record(verdict, explanation, evidence_hash, recipient, account_number, amount)

        # Invariant 2: Channel Provenance Check
        if "public_web_chat" in source_origin.lower():
            verdict = EscrowDecision.BLOCK
            explanation = (
                f"Source Taint: Action was triggered by an unauthenticated channel ('{source_origin}'). "
                f"Financial payouts require authenticated enterprise credentials."
            )
            return self._record(verdict, explanation, evidence_hash, recipient, account_number, amount)

        # Invariant 3: Deterministic Ground-Truth Reconciliation
        if recipient not in ERP_MASTER_LEDGER:
            verdict = EscrowDecision.HUMAN_APPROVAL
            explanation = f"Unregistered Vendor: '{recipient}' does not exist in ERP master records. Held for human review."
            return self._record(verdict, explanation, evidence_hash, recipient, account_number, amount)

        vendor_record = ERP_MASTER_LEDGER[recipient]
        verified_account = vendor_record["verified_account"]
        min_expected, max_expected = vendor_record["typical_monthly_range"]

        # Check Account Mismatch (BEC / Injected Mule Account)
        if account_number != verified_account:
            verdict = EscrowDecision.BLOCK
            explanation = (
                f"🚨 CRITICAL ACCOUNT MISMATCH (UNAUTHORIZED BENEFICIARY):\n"
                f"   - Target Account in Tool Call: '{account_number}'\n"
                f"   - Authoritative Account on File: '{verified_account}'\n"
                f"   - Discrepancy: The proposed account does not match the vendor account in the verified ledger."
            )
            return self._record(verdict, explanation, evidence_hash, recipient, account_number, amount)

        # Check Value Anomaly
        if amount > (max_expected * 2):
            verdict = EscrowDecision.HUMAN_APPROVAL
            explanation = (
                f"⚠️ Value Anomaly: Requested amount (₹{amount:,.2f}) significantly exceeds "
                f"typical monthly limit (Max: ₹{max_expected:,.2f}). Held for secondary sign-off."
            )
            return self._record(verdict, explanation, evidence_hash, recipient, account_number, amount)

        # All invariants passed
        verdict = EscrowDecision.ALLOW
        explanation = f"Verified: Recipient '{recipient}' and account '{account_number}' match ERP master ledger. Amount within bounds."
        return self._record(verdict, explanation, evidence_hash, recipient, account_number, amount)

    def _record(self, verdict: str, explanation: str, evidence_hash: str, recipient: str, account_number: str, amount: float):
        entry = {
            "evidence_id": f"ESCROW-{evidence_hash}",
            "decision_id": f"ESCROW-{evidence_hash}",
            "verdict": verdict,
            "recipient": recipient,
            "account_number": account_number,
            "amount": amount,
            "explanation": explanation,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.audit_log.append(entry)
        return verdict, entry
