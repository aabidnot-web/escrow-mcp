# Escrow MCP Server

> Deterministic In-Flight Action Verification & Execution Gate for Autonomous AI Agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Protocol: MCP](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io)
[![Website: escrow.lag.agency](https://img.shields.io/badge/Web-escrow.lag.agency-black)](https://escrow.lag.agency)

---

## ⚡ The Problem
Autonomous AI agents are increasingly entrusted with tools to disburse payments, update ERP systems, and execute transactions. However, LLMs are probabilistic: they are vulnerable to **Business Email Compromise (BEC)**, prompt injection, and hallucinated account substitutions.

Language-level safety filters fail when invoices look completely polite and legitimate.

## 🛡️ The Escrow Solution
Escrow introduces a fundamental **separation of powers**:
* **The Agent PROPOSES**: Parses documents, reasons, and requests tool executions.
* **Escrow AUTHORIZES**: A deterministic, sub-10ms mathematical gate verifies parameters against the enterprise master ledger and document provenance before funds or data leave the client perimeter.

---

## 🚀 Quickstart & Installation

### Option 1: Run Instantly via `uvx` (No install required)
```bash
uvx escrow-mcp
```

### Option 2: Install via `pip`
```bash
pip install escrow-mcp
escrow-mcp
```

---

## ⚙️ Configuration in MCP Clients

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "escrow": {
      "command": "uvx",
      "args": ["escrow-mcp"]
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "escrow": {
      "command": "escrow-mcp"
    }
  }
}
```

---

## 🛠️ Exposed Tools

### 1. `escrow_verified_transfer`
Deterministic execution gate intercepting wire transfers and payouts.
* Cross-references recipient and bank accounts against authoritative ERP ledgers.
* Validates source provenance and flags unauthenticated triggers.
* Detects transaction volume anomalies.
* Returns `ALLOW`, `BLOCK` (zero capital lost), or `HUMAN_APPROVAL`.

### 2. `escrow_audit_ledger`
Immutable audit log returning complete provenance trails and cryptographic SHA-256 evidence hashes for every proposed action.

---

## 📜 License
MIT License. Built by the Escrow Team (`contact@lag.agency`).
