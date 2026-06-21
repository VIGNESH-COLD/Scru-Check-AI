"""
External Access Management
Handles temporary access tokens for external examiners
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import secrets


class ExternalAccessManager:
    """
    Manages temporary read-only access for external examiners.
    
    Features:
    - Generate time-limited tokens
    - Scope tokens to specific papers
    - Track access for audit
    - Revoke tokens
    """
    
    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(48)
    
    def __init__(self):
        # Instance-level token store (not a class-level mutable to avoid shared state)
        self._token_store: Dict[str, Dict[str, Any]] = {}
    
    async def create_access_link(
        self,
        paper_ids: List[str],
        created_by: str,
        expires_hours: int = 48,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Create a temporary access link for external examiner.
        
        Args:
            paper_ids: List of paper IDs the external can access
            created_by: Username of HOD/COE creating the link
            expires_hours: Hours until link expires (default 48)
            db_session: Optional database session
            
        Returns:
            Dict with token, expires_at, and access URL
        """
        token = self.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        token_data = {
            "token": token,
            "paper_ids": paper_ids,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_revoked": False,
            "access_count": 0,
            "last_accessed": None
        }
        
        # Store in memory
        self._token_store[token] = token_data
        
        # Store in database if available
        if db_session:
            try:
                from models.database import ExternalAccessToken
                db_token = ExternalAccessToken(
                    token=token,
                    paper_ids=paper_ids,
                    created_by=created_by,
                    expires_at=expires_at,
                    is_revoked=False
                )
                db_session.add(db_token)
                db_session.commit()
            except Exception as e:
                print(f"⚠️ Could not save token to database: {e}")
        
        return {
            "token": token,
            "expires_at": expires_at.isoformat(),
            "expires_in_hours": expires_hours,
            "paper_count": len(paper_ids),
            "access_url": f"/external/{token}"
        }
    
    async def verify_token(self, token: str, db_session = None) -> Optional[Dict[str, Any]]:
        """
        Verify an external access token.
        
        Returns:
            Token data if valid, None if invalid/expired/revoked
        """
        token_data = None
        
        # Check database first
        if db_session:
            try:
                from models.database import ExternalAccessToken
                db_token = db_session.query(ExternalAccessToken).filter(
                    ExternalAccessToken.token == token
                ).first()
                
                if db_token:
                    token_data = {
                        "token": db_token.token,
                        "paper_ids": db_token.paper_ids,
                        "created_by": db_token.created_by,
                        "expires_at": db_token.expires_at.isoformat(),
                        "is_revoked": db_token.is_revoked,
                        "access_count": db_token.access_count
                    }
            except Exception as e:
                print(f"⚠️ Database lookup failed: {e}")
        
        # Fallback to memory store
        if not token_data:
            token_data = self._token_store.get(token)
        
        if not token_data:
            return None
        
        # Check if revoked
        if token_data.get("is_revoked"):
            return None
        
        # Check expiration
        expires_at = token_data.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", ""))
        
        if datetime.utcnow() > expires_at:
            return None
        
        return token_data
    
    async def record_access(self, token: str, db_session = None) -> None:
        """Record an access event for a token."""
        # Update memory store
        if token in self._token_store:
            self._token_store[token]["access_count"] += 1
            self._token_store[token]["last_accessed"] = datetime.utcnow().isoformat()
        
        # Update database
        if db_session:
            try:
                from models.database import ExternalAccessToken
                db_token = db_session.query(ExternalAccessToken).filter(
                    ExternalAccessToken.token == token
                ).first()
                
                if db_token:
                    db_token.access_count += 1
                    db_token.last_accessed = datetime.utcnow()
                    db_session.commit()
            except Exception as e:
                print(f"⚠️ Could not update access count: {e}")
    
    async def revoke_token(self, token: str, db_session = None) -> bool:
        """Revoke an external access token."""
        # Update memory store
        if token in self._token_store:
            self._token_store[token]["is_revoked"] = True
        
        # Update database
        if db_session:
            try:
                from models.database import ExternalAccessToken
                db_token = db_session.query(ExternalAccessToken).filter(
                    ExternalAccessToken.token == token
                ).first()
                
                if db_token:
                    db_token.is_revoked = True
                    db_session.commit()
                    return True
            except Exception as e:
                print(f"⚠️ Could not revoke token: {e}")
                return False
        
        return token in self._token_store
    
    async def list_active_tokens(self, created_by: str = None, db_session = None) -> List[Dict[str, Any]]:
        """List all active (non-expired, non-revoked) tokens."""
        tokens = []
        now = datetime.utcnow()
        
        # Get from database
        if db_session:
            try:
                from models.database import ExternalAccessToken
                query = db_session.query(ExternalAccessToken).filter(
                    ExternalAccessToken.is_revoked == False,
                    ExternalAccessToken.expires_at > now
                )
                
                if created_by:
                    query = query.filter(ExternalAccessToken.created_by == created_by)
                
                for db_token in query.all():
                    tokens.append({
                        "token": db_token.token,           # full token needed for revoke
                        "token_display": db_token.token[:16] + "...",  # truncated for display
                        "paper_ids": db_token.paper_ids,
                        "created_by": db_token.created_by,
                        "created_at": db_token.created_at.isoformat(),
                        "expires_at": db_token.expires_at.isoformat(),
                        "access_count": db_token.access_count
                    })
            except Exception as e:
                print(f"⚠️ Could not list tokens from database: {e}")
        
        # Fallback to memory store
        if not tokens:
            for token, data in self._token_store.items():
                if data.get("is_revoked"):
                    continue
                
                expires_at = data.get("expires_at")
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace("Z", ""))
                
                if expires_at <= now:
                    continue
                
                if created_by and data.get("created_by") != created_by:
                    continue
                
                tokens.append({
                    "token": token,                          # full token needed for revoke
                    "token_display": token[:16] + "...",    # truncated for display
                    "paper_ids": data.get("paper_ids"),
                    "created_by": data.get("created_by"),
                    "created_at": data.get("created_at"),
                    "expires_at": data.get("expires_at"),
                    "access_count": data.get("access_count", 0)
                })
        
        return tokens


# Singleton instance
external_access_manager = ExternalAccessManager()
