"""
FastAPI async authentication proxy for Obsidian LiveSync
Provides JWT-based per-device token authentication with revocation
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from dotenv import load_dotenv
from database import TokenDatabase

load_dotenv("/root/obsidian-livesync/.env")

app = FastAPI(
    title="Obsidian LiveSync Auth Proxy",
    description="Custom JWT authentication with per-device token management",
    version="1.0.0"
)

# Configuration
COUCHDB_URL = os.getenv("COUCHDB_URL", "http://127.0.0.1:5984")
COUCHDB_USER = os.getenv("COUCHDB_USER", "admin")
COUCHDB_PASSWORD = os.getenv("COUCHDB_PASSWORD")
JWT_SECRET = os.getenv("JWT_HMAC_SECRET")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")  # For management API

# Database
db = TokenDatabase()

# Security
security = HTTPBearer()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await db.init_db()
    print("✅ Token database initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "obsidian-auth-proxy"}


async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and check if it's valid in database"""
    token = credentials.credentials

    try:
        # Decode JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        # Extract token_id from JWT
        token_id = payload.get("token_id")
        if not token_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing token_id")

        # Check if token is valid in database
        is_valid = await db.is_token_valid(token_id)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Token revoked or expired")

        # Update last used timestamp
        await db.update_last_used(token_id)

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def verify_admin_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify admin token for management API"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.replace("Bearer ", "")

    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    return True


# ===== Management API (must be before catch-all) =====

@app.post("/admin/tokens/create")
async def create_token(
    device_name: str,
    expires_in_days: Optional[int] = None,
    metadata: Optional[str] = None,
    _admin: bool = Depends(verify_admin_token)
):
    """Create a new device token"""

    # Create token in database
    token_data = await db.create_token(device_name, expires_in_days, metadata)

    # Generate JWT with the token_id
    jwt_payload = {
        "token_id": token_data["token_id"],
        "device_name": device_name,
        "iat": datetime.utcnow(),
    }

    if expires_in_days:
        jwt_payload["exp"] = datetime.utcnow() + timedelta(days=expires_in_days)

    jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")

    return {
        **token_data,
        "jwt_token": jwt_token,
        "usage": f"Authorization: Bearer {jwt_token}"
    }


@app.get("/admin/tokens/list")
async def list_tokens(
    include_revoked: bool = False,
    _admin: bool = Depends(verify_admin_token)
):
    """List all device tokens"""
    tokens = await db.list_tokens(include_revoked=include_revoked)
    return {"tokens": tokens, "count": len(tokens)}


@app.post("/admin/tokens/revoke/{token_id}")
async def revoke_token(
    token_id: str,
    _admin: bool = Depends(verify_admin_token)
):
    """Revoke a device token"""
    success = await db.revoke_token(token_id)

    if not success:
        raise HTTPException(status_code=404, detail="Token not found or already revoked")

    return {"message": f"Token {token_id} revoked successfully"}


@app.delete("/admin/tokens/delete/{token_id}")
async def delete_token(
    token_id: str,
    _admin: bool = Depends(verify_admin_token)
):
    """Permanently delete a token"""
    success = await db.delete_token(token_id)

    if not success:
        raise HTTPException(status_code=404, detail="Token not found")

    return {"message": f"Token {token_id} deleted permanently"}


@app.get("/admin/tokens/info/{token_id}")
async def get_token_info(
    token_id: str,
    _admin: bool = Depends(verify_admin_token)
):
    """Get token information"""
    token = await db.get_token(token_id)

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    return token


@app.post("/admin/tokens/cleanup")
async def cleanup_expired_tokens(_admin: bool = Depends(verify_admin_token)):
    """Delete all expired tokens"""
    count = await db.cleanup_expired()
    return {"message": f"Deleted {count} expired tokens"}


# ===== CouchDB Proxy (catch-all, must be LAST) =====

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"])
async def proxy_to_couchdb(request: Request, path: str, payload: dict = Depends(verify_jwt_token)):
    """Proxy all requests to CouchDB after JWT validation"""

    # Build CouchDB URL
    couchdb_url = f"{COUCHDB_URL}/{path}"
    if request.url.query:
        couchdb_url += f"?{request.url.query}"

    # Get request body
    body = await request.body()

    # Prepare headers (exclude auth headers, we'll add our own)
    headers = dict(request.headers)
    headers.pop("authorization", None)
    headers.pop("host", None)

    # Make async request to CouchDB with Basic Auth
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=couchdb_url,
            content=body,
            headers=headers,
            auth=(COUCHDB_USER, COUCHDB_PASSWORD),
            timeout=300.0  # 5 minutes for large sync operations
        )

    # Return CouchDB response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type")
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5985,
        reload=False,
        log_level="info"
    )
