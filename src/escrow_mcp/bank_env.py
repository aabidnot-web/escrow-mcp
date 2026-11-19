"""Local simulated banking environment and synthetic vendor ledger for the Escrow demo."""

from typing import Dict, Any, Optional

ERP_MASTER_LEDGER = {
    "Atlas Power Corp": {
        "vendor_id": "VEND-001",
        "verified_account": "AP-4819-2041",
        "authorized_contact": "billing@atlaspower.in",
        "typical_monthly_range": (3000, 6000),
        "status": "ACTIVE_VERIFIED"
    },
    "CleanTech Water": {
        "vendor_id": "VEND-002",
        "verified_account": "CW-9921-3312",
        "authorized_contact": "accounts@cleantechwater.org",
        "typical_monthly_range": (1000, 2000),
        "status": "ACTIVE_VERIFIED"
    },
    "CloudScale Infrastructure": {
        "vendor_id": "VEND-003",
        "verified_account": "CS-5510-8843",
        "authorized_contact": "finance@cloudscale.io",
        "typical_monthly_range": (15000, 25000),
        "status": "ACTIVE_VERIFIED"
    }
}


class BankAccount:
    """Stateful Bank Account for the Enterprise"""
    def __init__(self, owner: str = "Alice Enterprise AP", starting_balance: float = 150000.0):
        self.owner = owner
        self.balance = starting_balance
        self.transactions = []

    def execute_transfer(self, recipient: str, account_number: str, amount: float, reason: str) -> Dict[str, Any]:
        if amount > self.balance:
            return {"status": "FAILED", "reason": f"Insufficient funds. Balance: ₹{self.balance}"}
        
        self.balance -= amount
        tx = {
            "tx_id": f"TXN-{len(self.transactions) + 1:04d}",
            "recipient": recipient,
            "account_number": account_number,
            "amount": amount,
            "reason": reason,
            "remaining_balance": self.balance
        }
        self.transactions.append(tx)
        return {"status": "SUCCESS", "transaction": tx}
