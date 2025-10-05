"""
Async SQLite database for device token management
"""
import aiosqlite
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path


class TokenDatabase:
    def __init__(self, db_path: str = "/root/obsidian-livesync/auth-proxy/tokens.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self):
        """Initialize database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS device_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id TEXT UNIQUE NOT NULL,
                    device_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    last_used_at TEXT,
                    revoked INTEGER DEFAULT 0,
                    revoked_at TEXT,
                    metadata TEXT
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_id ON device_tokens(token_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_revoked ON device_tokens(revoked)
            """)

            await db.commit()

    async def create_token(
        self,
        device_name: str,
        expires_in_days: Optional[int] = None,
        metadata: Optional[str] = None
    ) -> Dict:
        """Create a new device token"""
        token_id = secrets.token_urlsafe(32)
        created_at = datetime.utcnow().isoformat()
        expires_at = None

        if expires_in_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO device_tokens
                (token_id, device_name, created_at, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (token_id, device_name, created_at, expires_at, metadata))

            await db.commit()

        return {
            "token_id": token_id,
            "device_name": device_name,
            "created_at": created_at,
            "expires_at": expires_at,
            "metadata": metadata
        }

    async def get_token(self, token_id: str) -> Optional[Dict]:
        """Get token details by token_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM device_tokens WHERE token_id = ?",
                (token_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def is_token_valid(self, token_id: str) -> bool:
        """Check if token is valid (not revoked and not expired)"""
        token = await self.get_token(token_id)

        if not token:
            return False

        # Check if revoked
        if token['revoked']:
            return False

        # Check if expired
        if token['expires_at']:
            expires_at = datetime.fromisoformat(token['expires_at'])
            if datetime.utcnow() > expires_at:
                return False

        return True

    async def update_last_used(self, token_id: str):
        """Update last used timestamp"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE device_tokens
                SET last_used_at = ?
                WHERE token_id = ?
            """, (datetime.utcnow().isoformat(), token_id))
            await db.commit()

    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a token"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE device_tokens
                SET revoked = 1, revoked_at = ?
                WHERE token_id = ? AND revoked = 0
            """, (datetime.utcnow().isoformat(), token_id))

            await db.commit()
            return cursor.rowcount > 0

    async def list_tokens(self, include_revoked: bool = False) -> List[Dict]:
        """List all tokens"""
        query = "SELECT * FROM device_tokens"
        if not include_revoked:
            query += " WHERE revoked = 0"
        query += " ORDER BY created_at DESC"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def delete_token(self, token_id: str) -> bool:
        """Permanently delete a token"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM device_tokens WHERE token_id = ?",
                (token_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def cleanup_expired(self) -> int:
        """Delete expired tokens, return count deleted"""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM device_tokens
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (now,))
            await db.commit()
            return cursor.rowcount
