"""
Official Escrow MCP (Model Context Protocol) Server
Exposes an action-governed execution gateway over JSON-RPC (stdio).
Compatible with Claude Desktop, Cursor, Antigravity, and any MCP-compliant agent.
"""

import sys
import json
import logging
from .bank_env import BankAccount
from .guard import EscrowGuard, EscrowDecision

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[ESCROW-MCP] %(message)s")

ENTERPRISE_BANK = BankAccount(starting_balance=150000.0)
ESCROW_GUARD = EscrowGuard()


def handle_initialize(msg_id):
    """MCP Protocol Handshake"""
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "escrow-action-gateway",
                "version": "0.1.0"
            }
        }
    }


def handle_tools_list(msg_id):
    """Declares available protected enterprise tools to the agent"""
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "tools": [
                {
                    "name": "escrow_verified_transfer",
                    "description": (
                        "Deterministic in-flight financial execution gate. Intercepts and authorizes "
                        "wire transfers and payouts BEFORE irreversible execution. Mathematically cross-references "
                        "proposed parameters against verified enterprise ERP master ledgers and source provenance. "
                        "Halts swapped bank accounts, tampered invoices, and unauthorized recipients with zero capital loss."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_scope": {
                                "type": "string",
                                "description": "The declared user intent or enterprise instruction authorizing the workflow (e.g. 'Settle October utility invoice for Atlas Power Corp')."
                            },
                            "source_origin": {
                                "type": "string",
                                "description": "Origin of the document or payload being processed (e.g. 'incoming_email', 'erp_sync', 'vendor_portal', 'public_chat')."
                            },
                            "recipient": {
                                "type": "string",
                                "description": "Official name of the beneficiary entity to receive payment."
                            },
                            "account_number": {
                                "type": "string",
                                "description": "Beneficiary bank account number, IBAN, or virtual account identifier extracted from invoice."
                            },
                            "amount": {
                                "type": "number",
                                "description": "Total disbursement amount in currency units (INR)."
                            },
                            "reason": {
                                "type": "string",
                                "description": "Invoice number, purchase order ID, or contract audit reference."
                            }
                        },
                        "required": ["task_scope", "source_origin", "recipient", "account_number", "amount", "reason"]
                    }
                },
                {
                    "name": "escrow_audit_ledger",
                    "description": (
                        "Cryptographic read-only audit log for all agent-proposed execution attempts. "
                        "Returns immutable records of every evaluation: timestamp, task intent, parameter provenance, "
                        "deterministic decision (ALLOW / BLOCK / HUMAN_APPROVAL), and SHA-256 evidence hash."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    }


def handle_tools_call(msg_id, params):
    """In-Flight Enforcement Hook on MCP Tool Invocations"""
    tool_name = params.get("name")
    args = params.get("arguments", {})

    logging.info(f"Intercepted MCP Tool Call: '{tool_name}'")

    if tool_name == "escrow_audit_ledger":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(ESCROW_GUARD.audit_log, indent=2)
                    }
                ]
            }
        }

    if tool_name == "escrow_verified_transfer":
        task_scope = args.get("task_scope", "")
        source_origin = args.get("source_origin", "unknown")
        recipient = args.get("recipient", "")
        account_number = args.get("account_number", "")
        amount = float(args.get("amount", 0))
        reason = args.get("reason", "")

        verdict, evidence = ESCROW_GUARD.evaluate_transfer_action(
            task_intent=task_scope,
            source_doc_id="MCP-CALL",
            source_origin=source_origin,
            recipient=recipient,
            account_number=account_number,
            amount=amount,
            reason=reason
        )

        if verdict == EscrowDecision.BLOCK:
            logging.warning(f"🚨 CRITICAL BLOCK: Tool call denied for recipient '{recipient}'")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"[ESCROW SECURITY EXCEPTION - ACTION BLOCKED]\n"
                                f"Verdict: {verdict}\n"
                                f"Evidence ID: {evidence['evidence_id']}\n"
                                f"Reason: {evidence['explanation']}\n"
                                f"Status: Funds protected. Zero capital disbursed."
                            )
                        }
                    ]
                }
            }

        elif verdict == EscrowDecision.HUMAN_APPROVAL:
            logging.info(f"⚠️ HELD FOR REVIEW: Action requires human sign-off")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"[ESCROW HELD - SECONDARY APPROVAL REQUIRED]\n"
                                f"Verdict: {verdict}\n"
                                f"Evidence ID: {evidence['evidence_id']}\n"
                                f"Reason: {evidence['explanation']}\n"
                                f"Status: Action suspended in staging buffer awaiting CFO approval."
                            )
                        }
                    ]
                }
            }

        tx_result = ENTERPRISE_BANK.execute_transfer(recipient, account_number, amount, reason)
        logging.info(f"✔ ALLOWED: Payout executed. New balance: ₹{ENTERPRISE_BANK.balance:,.2f}")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"[ESCROW VERIFIED - ACTION EXECUTED]\n"
                            f"Evidence ID: {evidence['evidence_id']}\n"
                            f"Transaction ID: {tx_result['transaction']['tx_id']}\n"
                            f"Disbursed: ₹{amount:,.2f} to {recipient} ({account_number})\n"
                            f"Remaining Balance: ₹{ENTERPRISE_BANK.balance:,.2f}"
                        )
                    }
                ]
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": -32601,
            "message": f"Method or tool '{tool_name}' not found."
        }
    }


def process_message(line):
    """Dispatches incoming JSON-RPC messages"""
    try:
        request = json.loads(line)
        method = request.get("method")
        msg_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return handle_initialize(msg_id)
        elif method == "tools/list":
            return handle_tools_list(msg_id)
        elif method == "tools/call":
            return handle_tools_call(msg_id, params)
        elif method == "notifications/initialized":
            return None
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unsupported method: {method}"}
            }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
        }


def main():
    """Main stdio loop for MCP protocol"""
    logging.info("Escrow Action-Gateway MCP Server running on stdio...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = process_message(line)
        if response:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
