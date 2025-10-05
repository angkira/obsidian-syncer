# JWT Authentication for Obsidian LiveSync

## ⚠️ Current Status

**JWT authentication configuration has been prepared but is NOT currently working** with CouchDB 3.4.3. The official CouchDB Docker image does not include the JWT authentication handler by default.

## 🔐 Authentication Options

### Option 1: Basic Authentication (Currently Active)
This is the **working** authentication method:

**Connection Details:**
- **URL:** `http://37.27.209.193/obsidian`
- **Username:** `obsidian`
- **Password:** `nzQWlmuIHuhfflUIDeYKp4lQZKGWhgWKo+vctFNlwjI=`
- **Database:** `obsidian-sync`

**In Obsidian LiveSync Plugin:**
1. Set URI to: `http://37.27.209.193/obsidian`
2. Enter username: `obsidian`
3. Enter password: `nzQWlmuIHuhfflUIDeYKp4lQZKGWhgWKo+vctFNlwjI=`
4. Set database: `obsidian-sync`

### Option 2: SSH Tunnel + Basic Auth (Recommended for Security)
For encrypted connections without domain/SSL:

```bash
# On your local machine:
ssh -L 5984:localhost:5984 root@37.27.209.193

# In Obsidian:
# URI: http://localhost:5984/obsidian-sync
# Username: obsidian
# Password: nzQWlmuIHuhfflUIDeYKp4lQZKGWhgWKo+vctFNlwjI=
```

### Option 3: JWT Authentication (Prepared, Not Working Yet)

**What Was Configured:**
- ✅ JWT HMAC secret generated and stored in `.env`
- ✅ RSA key pair generated (`jwt-private.pem`, `jwt-public.pem`)
- ✅ CouchDB `local.ini` updated with JWT handler
- ✅ Token generation scripts created
- ✅ Nginx configured to pass Authorization headers
- ❌ CouchDB JWT handler not loaded (missing from Docker image)

## 🛠️ JWT Implementation Files

### JWT Secret
Located in: `/root/obsidian-livesync/.env`
```
JWT_HMAC_SECRET=a478647a0766fb5aec2b1dcd8e044c709924993056790b042520f5fcb2adefc47af78955e069ba1b407b824b4bf98bacc298ebc0082540f5c3a73050a37091fd
```

### Token Generation Scripts

**Python Script (Recommended):**
```bash
/root/obsidian-livesync/generate-jwt.py [username] [hours]

# Examples:
/root/obsidian-livesync/generate-jwt.py obsidian 24    # 24-hour token
/root/obsidian-livesync/generate-jwt.py admin 168      # 7-day token
```

**Bash Script:**
```bash
/root/obsidian-livesync/generate-jwt.sh [username] [duration_in_seconds]

# Examples:
/root/obsidian-livesync/generate-jwt.sh obsidian 86400    # 24 hours
/root/obsidian-livesync/generate-jwt.sh admin 604800      # 7 days
```

### RSA Key Pair
- **Private Key:** `/root/obsidian-livesync/jwt-private.pem`
- **Public Key:** `/root/obsidian-livesync/jwt-public.pem`

## 🔧 Enabling JWT Authentication (Manual Steps Required)

To enable JWT in CouchDB, you need to build a custom Docker image with the JWT plugin:

### Method 1: Build Custom CouchDB with JWT Plugin

1. **Create custom Dockerfile:**
```dockerfile
FROM couchdb:3.4

# Install Erlang JWT dependencies
USER root
RUN apt-get update && apt-get install -y git erlang-dev make

# Clone and build JWT auth plugin
WORKDIR /opt
RUN git clone https://github.com/softapalvelin/couch_jwt_auth.git
WORKDIR /opt/couch_jwt_auth
RUN make

# Copy plugin to CouchDB plugins directory
RUN cp -r ebin /opt/couchdb/lib/couch_jwt_auth-1.0/

USER couchdb
WORKDIR /opt/couchdb
```

2. **Update docker-compose.yml:**
```yaml
services:
  couchdb:
    build: .  # Build from custom Dockerfile
    # ... rest of config
```

### Method 2: Use Pre-built Image with JWT
Search Docker Hub for CouchDB images with JWT support:
```bash
docker search couchdb-jwt
```

### Method 3: Install JWT Plugin Manually
```bash
# Enter container
docker exec -it -u root obsidian-couchdb bash

# Install git and build tools
apt-get update && apt-get install -y git erlang-dev make

# Clone and compile JWT plugin
cd /opt
git clone https://github.com/softapalvelin/couch_jwt_auth.git
cd couch_jwt_auth
make
cp -r ebin /opt/couchdb/lib/couch_jwt_auth-1.0/

# Restart CouchDB
exit
docker compose restart
```

## 📝 CouchDB JWT Configuration

The following configuration has already been added to `/root/obsidian-livesync/local.ini`:

```ini
[chttpd_auth]
authentication_handlers = {chttpd_auth, jwt_authentication_handler}, {chttpd_auth, cookie_authentication_handler}, {chttpd_auth, default_authentication_handler}

[jwt_auth]
required_claims = exp
hs_secret = a478647a0766fb5aec2b1dcd8e044c709924993056790b042520f5fcb2adefc47af78955e069ba1b407b824b4bf98bacc298ebc0082540f5c3a73050a37091fd
```

## 🧪 Testing JWT (Once Enabled)

### Generate Token
```bash
/root/obsidian-livesync/generate-jwt.py obsidian 24
```

### Test with curl
```bash
TOKEN="eyJhbGci..."  # Copy from generator output

curl -H "Authorization: Bearer $TOKEN" http://localhost:5984/
curl -H "Authorization: Bearer $TOKEN" http://37.27.209.193/obsidian/
```

### Use in Obsidian
1. Generate a long-lived token (720 hours = 30 days):
   ```bash
   /root/obsidian-livesync/generate-jwt.py obsidian 720
   ```

2. In Obsidian LiveSync settings:
   - **URI:** `http://37.27.209.193/obsidian`
   - **Custom Request Header:** `Authorization: Bearer [YOUR_TOKEN]`
   - Leave username/password empty

## 🔍 Debugging JWT

### Check if JWT handler is loaded:
```bash
curl -u admin:r5IIX2rVz3dGCvTNSQH8W5ocwiDVCUC7t1tXEMWUTk0= \
  http://localhost:5984/_session
```

Look for `"authentication_handlers":["jwt","cookie","default"]` in response.

### Check JWT configuration:
```bash
curl -u admin:r5IIX2rVz3dGCvTNSQH8W5ocwiDVCUC7t1tXEMWUTk0= \
  http://localhost:5984/_node/_local/_config/jwt_auth
```

### View CouchDB logs:
```bash
docker logs -f obsidian-couchdb | grep -i jwt
```

## 📚 JWT Token Structure

Generated tokens contain:
```json
{
  "sub": "obsidian",           # Subject (username)
  "name": "obsidian",          # Display name
  "iat": 1759670998,          # Issued at (Unix timestamp)
  "exp": 1759757398,          # Expiration (Unix timestamp)
  "_couchdb.roles": []        # CouchDB roles
}
```

## 🔄 Token Rotation

When a token expires, generate a new one:
```bash
# Generate new 24-hour token
/root/obsidian-livesync/generate-jwt.py obsidian 24

# Update Obsidian plugin with new token
```

## ⚠️ Security Notes

1. **JWT secrets are stored in plaintext** in `.env` and `local.ini`
2. **Tokens cannot be revoked** - they're valid until expiration
3. **Without HTTPS**, tokens are transmitted in cleartext
4. **Use SSH tunnel** for production environments without SSL
5. **Keep private key secure** - never share `jwt-private.pem`

## 🎯 Recommendation

**For now, use Basic Authentication with SSH Tunnel:**

This provides:
- ✅ Working authentication
- ✅ Encrypted transport (via SSH)
- ✅ No token management complexity
- ✅ Works with all Obsidian devices

**To enable on device:**
```bash
# Add to ~/.ssh/config on each device:
Host obsidian-sync
    HostName 37.27.209.193
    User root
    LocalForward 5984 localhost:5984

# Then connect:
ssh -N -f obsidian-sync

# Configure Obsidian to: http://localhost:5984/obsidian-sync
```

---

**Last Updated:** 2025-10-05
**Status:** JWT prepared but not functional, Basic Auth working
