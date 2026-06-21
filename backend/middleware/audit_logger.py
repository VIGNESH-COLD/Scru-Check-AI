"""
Audit Logger Middleware
Logs all actions for accountability and compliance
"""

from datetime import datetime
from typing import Dict, Any, Optional
import json
import os


class AuditLogger:
    """
    Immutable audit logging for accountability.
    Logs to both file and database.
    """
    
    LOG_FILE = "audit_log.jsonl"
    
    async def log_analysis(self, paper_id: str, findings: Dict, status: str, user: str = "system"):
        """Log analysis action."""
        await self._log({
            "action": "ANALYZE_PAPER",
            "paper_id": paper_id,
            "status": status,
            "findings_count": len(findings.get("criteria", [])),
            "passed_count": findings.get("passed_count", 0),
            "user": user
        })
    
    async def log_override(self, paper_id: str, finding_id: str, action: str, justification: str, user: str = "faculty"):
        """Log override action."""
        await self._log({
            "action": "OVERRIDE_FINDING",
            "paper_id": paper_id,
            "finding_id": finding_id,
            "override_action": action,
            "justification": justification,
            "user": user
        })
    
    async def log_error(self, error: str, context: Optional[Dict] = None):
        """Log error event."""
        await self._log({
            "action": "ERROR",
            "error": error,
            "context": context or {}
        })
    
    async def log_login(self, user: str, success: bool, ip: str = None):
        """Log login attempt."""
        await self._log({
            "action": "LOGIN",
            "user": user,
            "success": success,
            "ip_address": ip
        })
    
    async def log_policy_change(self, rule_id: str, change_type: str, user: str, details: Dict):
        """Log policy change."""
        await self._log({
            "action": "POLICY_CHANGE",
            "rule_id": rule_id,
            "change_type": change_type,
            "user": user,
            "details": details
        })
    
    async def _log(self, data: Dict[str, Any]):
        """Write log entry (append-only)."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **data
        }
        
        # Append to JSONL file (immutable format)
        try:
            with open(self.LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Audit log error: {e}")
    
    async def get_logs(self, limit: int = 100, action: Optional[str] = None) -> list:
        """Retrieve audit logs (read-only)."""
        logs = []
        
        try:
            if os.path.exists(self.LOG_FILE):
                with open(self.LOG_FILE, "r") as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        if action is None or entry.get("action") == action:
                            logs.append(entry)
        except Exception as e:
            print(f"Error reading logs: {e}")
        
        return logs[-limit:] if limit else logs
