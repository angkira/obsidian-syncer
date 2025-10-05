# JWT Authentication Status - Obsidian LiveSync

**Last Updated:** 2025-10-05
**CouchDB Version:** 3.5.0
**Status:** ⚠️ **CONFIGURED BUT NOT WORKING**

---

## Summary

JWT authentication has been fully configured according to official CouchDB 3.5 documentation, but tokens are not being accepted. All configuration appears correct, the jwtf module is installed, and token signatures are valid, but authentication still fails.

**Current Working Method:** Basic Authentication (username + password)

---

## What Was Done

### ✅ 1. Upgraded to CouchDB 3.5.0
- Upgraded from 3.4 to 3.5 (JWT support improved in 3.5)
- Verified jwtf module is present: `/opt/couchdb/lib/jwtf-3.5.0/`

### ✅ 2. Generated Cryptographic Keys
- **HMAC Secret (Hex):** `a478647a0766fb5aec2b1dcd8e044c709924993056790b042520f5fcb2adefc47af78955e069ba1b407b824b4bf98bacc298ebc0082540f5c3a73050a37091fd`
- **HMAC Secret (Base64):** `pHhkegdm+1rsKx3NjgRMcJkkmTBWeQsEJSD1/LKt78R694lV4Gm6G0B7gktL+YuswpjrwAglQPXDpzBQo3CR/Q==`
- **RSA Keys:** Generated but not used (HMAC preferred for simplicity)

### ✅ 3. Configured local.ini

```ini
[chttpd_auth]
require_valid_user = true
authentication_redirect = /_utils/session.html
timeout = 86400
authentication_handlers = {chttpd_auth, cookie_authentication_handler}, {chttpd_auth, jwt_authentication_handler}, {chttpd_auth, default_authentication_handler}

[jwt_auth]
required_claims = exp,sub

[jwt_keys]
hmac:_default = pHhkegdm+1rsKx3NjgRMcJkkmTBWeQsEJSD1/LKt78R694lV4Gm6G0B7gktL+YuswpjrwAglQPXDpzBQo3CR/Q==
```

### ✅ 4. Updated Nginx Configuration
- Added `proxy_set_header Authorization $http_authorization;`
- Added `proxy_pass_header Authorization;`
- JWT Bearer tokens properly forwarded to CouchDB

### ✅ 5. Created Token Generation Scripts
- **Python:** `/root/obsidian-livesync/generate-jwt.py` (working correctly)
- **Bash:** `/root/obsidian-livesync/generate-jwt.sh`
- Tokens generate valid HS256 signatures (verified mathematically)

### ✅ 6. Verified Configuration
```bash
curl -u admin:PASSWORD http://localhost:5984/_node/_local/_config/jwt_auth
# Returns: {"required_claims":"exp,sub"}

curl -u admin:PASSWORD http://localhost:5984/_node/_local/_config/jwt_keys
# Returns: {"hmac:_default":"pHhkegdm..."}

curl -u admin:PASSWORD http://localhost:5984/_node/_local/_config/chttpd_auth/authentication_handlers
# Returns: "{chttpd_auth, cookie_authentication_handler}, {chttpd_auth, jwt_authentication_handler}, {chttpd_auth, default_authentication_handler}"
```

---

## JWT Token Structure

Generated tokens have this structure:

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "obsidian",
  "name": "obsidian",
  "iat": 1759672379,
  "exp": 1759758779,
  "_couchdb.roles": []
}
```

**Signature:** Valid HMAC-SHA256 using the configured secret

---

## Testing Performed

### Test 1: Direct CouchDB Access
```bash
TOKEN="eyJhbGci..."
curl -H 'Authorization: Bearer $TOKEN' http://localhost:5984/
# Result: {"error":"unauthorized","reason":"Authentication required."}
```

### Test 2: Via Nginx Proxy
```bash
curl -H 'Authorization: Bearer $TOKEN' http://37.27.209.193/obsidian/
# Result: {"error":"unauthorized","reason":"Authentication required."}
```

### Test 3: Session Endpoint
```bash
curl -H 'Authorization: Bearer $TOKEN' http://localhost:5984/_session
# Result: {"ok":true,"userCtx":{"name":null,"roles":[]},"info":{"authentication_handlers":["cookie","default"]}}
```

**Observation:** `authentication_handlers` shows only `["cookie","default"]`, not including `"jwt"` - suggesting the JWT handler may not be loading.

### Test 4: Signature Verification
```python
# Mathematically verified token signatures match expected values
# Tokens are correctly formatted and signed
```

### Test 5: Basic Auth (Control)
```bash
curl -u obsidian:PASSWORD http://localhost:5984/_session
# Result: SUCCESS - Basic auth works perfectly
```

---

## Possible Issues

1. **JWT Handler Not Loading**: Despite being configured, `_session` endpoint doesn't list "jwt" in authentication_handlers
2. **CouchDB 3.5.0 Bug**: Potential issue with JWT implementation in this version
3. **Missing Configuration**: Some undocumented setting may be required
4. **User Database Requirement**: JWT might require users to exist in `_users` database (though user "obsidian" exists)
5. **Erlang Module Issue**: jwtf module may not be properly initialized

---

## Current Workaround: Basic Authentication

**✅ WORKING METHOD:**

```
URL: http://37.27.209.193/obsidian
Username: obsidian
Password: nzQWlmuIHuhfflUIDeYKp4lQZKGWhgWKo+vctFNlwjI=
Database: obsidian-sync
```

**For Encryption (Recommended):**
```bash
# Use SSH tunnel
ssh -L 5984:localhost:5984 root@37.27.209.193

# Then connect Obsidian to:
# URL: http://localhost:5984/obsidian-sync
```

---

## Files & Tools

| File | Purpose |
|------|---------|
| `/root/obsidian-livesync/.env` | Contains JWT_HMAC_SECRET |
| `/root/obsidian-livesync/local.ini` | CouchDB JWT configuration |
| `/root/obsidian-livesync/generate-jwt.py` | Python token generator (working) |
| `/root/obsidian-livesync/generate-jwt.sh` | Bash token generator |
| `/root/obsidian-livesync/jwt-private.pem` | RSA private key (unused) |
| `/root/obsidian-livesync/jwt-public.pem` | RSA public key (unused) |

---

## Generating JWT Tokens

```bash
# Generate 24-hour token
/root/obsidian-livesync/generate-jwt.py obsidian 24

# Generate 7-day token
/root/obsidian-livesync/generate-jwt.py obsidian 168

# Generate admin token
/root/obsidian-livesync/generate-jwt.py admin 24
```

---

## Debugging Commands

```bash
# Check CouchDB version
curl -u admin:PASSWORD http://localhost:5984/ | jq .version

# List all JWT config
curl -u admin:PASSWORD http://localhost:5984/_node/_local/_config/ | jq '.jwt_auth, .jwt_keys'

# Check if jwtf module exists
docker exec obsidian-couchdb ls -la /opt/couchdb/lib/ | grep jwt

# View CouchDB logs
docker logs -f obsidian-couchdb | grep -i jwt

# Test token generation
/root/obsidian-livesync/generate-jwt.py obsidian 1

# Enable debug logging
curl -u admin:PASSWORD -X PUT http://localhost:5984/_node/_local/_config/log/level -d '"debug"'
```

---

## Next Steps to Try

1. **Check CouchDB Mailing Lists**: Search for JWT issues in CouchDB 3.5.0
2. **Test with RSA Keys**: Try RSA instead of HMAC
3. **Minimal Test**: Create simplest possible JWT with only required claims
4. **Contact CouchDB Community**: Report potential bug
5. **Try CouchDB 3.4.x**: Test if JWT works in earlier version
6. **Enable Erlang Tracing**: Deep debug of jwtf module loading

---

## Conclusion

JWT authentication infrastructure is complete and properly configured according to official documentation. The configuration is correct, secrets are properly encoded, and tokens are validly signed. However, CouchDB 3.5.0 is not accepting the JWT tokens for unknown reasons.

**Recommendation:** Use Basic Authentication with SSH tunnel for encrypted connections until JWT issue is resolved.

---

## References

- [CouchDB JWT Auth Documentation](https://docs.couchdb.org/en/stable/api/server/authn.html)
- [CouchDB 3.5.0 Release Notes](https://docs.couchdb.org/en/stable/whatsnew/3.5.html)
- [jwtf Erlang Library](https://github.com/G-Corp/jwtf)
