# Obsidian LiveSync Server - Deployment Summary

## 🎉 Installation Complete!

Your Obsidian LiveSync server is running and ready to use.

---

## 📋 Server Information

**VPS IP Address:** `37.27.209.193`
**Installation Directory:** `/root/obsidian-livesync`
**CouchDB Version:** 3.4.3
**Access URL:** `http://37.27.209.193/obsidian`

---

## 🔐 Credentials

### Admin User (CouchDB Management)
- **Username:** `admin`
- **Password:** `r5IIX2rVz3dGCvTNSQH8W5ocwiDVCUC7t1tXEMWUTk0=`

### Sync User (Obsidian Plugin)
- **Username:** `obsidian`
- **Password:** `nzQWlmuIHuhfflUIDeYKp4lQZKGWhgWKo+vctFNlwjI=`
- **Database:** `obsidian-sync`

---

## ⚠️ SECURITY WARNING

**Your server is currently using HTTP (unencrypted) over the public internet!**

Since you don't have a domain name, SSL/TLS cannot be configured. This means your sync traffic is **not encrypted** when transmitted over the internet.

### Recommended Solution: SSH Tunnel

For secure access, use an SSH tunnel from your client devices:

```bash
# Run this on your local machine (laptop/desktop)
ssh -L 5984:localhost:5984 root@37.27.209.193

# Then configure Obsidian to connect to:
# http://localhost:5984/obsidian-sync
```

This encrypts all sync traffic through SSH.

### Alternative: VPN or Tailscale
Consider setting up a VPN (WireGuard, Tailscale) for secure access without SSH tunnels.

---

## 🔧 Obsidian LiveSync Plugin Configuration

1. **Install the Plugin:**
   - Open Obsidian → Settings → Community Plugins
   - Search for "Self-hosted LiveSync"
   - Install and enable it

2. **Configure Remote Database:**
   - Go to Plugin Settings → Remote Database Configuration
   - **URI:** `http://37.27.209.193/obsidian`
     (or `http://localhost:5984/obsidian-sync` if using SSH tunnel)
   - **Username:** `obsidian`
   - **Password:** `nzQWlmuIHuhfflUIDeYKp4lQZKGWhgWKo+vctFNlwjI=`
   - **Database name:** `obsidian-sync`
   - Click "Test Connection" → should see "Connection successful"

3. **Initial Setup:**
   - Choose sync settings (Live Sync recommended)
   - Perform initial sync
   - Enable on all your devices

---

## 🛠️ Management Commands

### Docker Management
```bash
# Navigate to installation directory
cd /root/obsidian-livesync

# View running containers
docker ps

# View CouchDB logs
docker logs obsidian-couchdb

# Follow logs in real-time
docker logs -f obsidian-couchdb

# Restart CouchDB
docker compose restart

# Stop CouchDB
docker compose down

# Start CouchDB
docker compose up -d

# Rebuild and restart (after config changes)
docker compose down && docker compose up -d
```

### Nginx Management
```bash
# Test Nginx configuration
nginx -t

# Reload Nginx (after config changes)
systemctl reload nginx

# Restart Nginx
systemctl restart nginx

# Check Nginx status
systemctl status nginx

# View Obsidian access logs
tail -f /var/log/nginx/obsidian-access.log

# View Obsidian error logs
tail -f /var/log/nginx/obsidian-error.log
```

### Firewall Management
```bash
# Check UFW status
ufw status verbose

# Add new rule (example)
ufw allow 8080/tcp
```

### Fail2ban Management
```bash
# Check fail2ban status
fail2ban-client status

# Check Obsidian jail status
fail2ban-client status nginx-obsidian

# Unban an IP
fail2ban-client set nginx-obsidian unbanip <IP_ADDRESS>
```

---

## 💾 Backup & Restore

### Automatic Backups
- **Schedule:** Daily at 2:00 AM (server time)
- **Location:** `/root/obsidian-livesync/backups/`
- **Retention:** Last 14 backups kept automatically
- **Log:** `/root/obsidian-livesync/backups/backup.log`

### Manual Backup
```bash
# Run backup script manually
/root/obsidian-livesync/backup.sh

# List all backups
ls -lh /root/obsidian-livesync/backups/couchdb_backup_*.tar.gz

# Check backup log
tail -20 /root/obsidian-livesync/backups/backup.log
```

### Restore from Backup
```bash
# 1. Stop CouchDB
cd /root/obsidian-livesync
docker compose down

# 2. Backup current data (optional)
mv data data.old

# 3. Extract backup (replace with your backup filename)
tar -xzf backups/couchdb_backup_YYYYMMDD_HHMMSS.tar.gz

# 4. Start CouchDB
docker compose up -d

# 5. Verify restoration
docker logs obsidian-couchdb
```

---

## 📊 Monitoring

### Check System Health
```bash
# CouchDB health check
curl http://admin:r5IIX2rVz3dGCvTNSQH8W5ocwiDVCUC7t1tXEMWUTk0=@localhost:5984/_up

# List all databases
curl -u admin:r5IIX2rVz3dGCvTNSQH8W5ocwiDVCUC7t1tXEMWUTk0= http://localhost:5984/_all_dbs

# Check database info
curl -u admin:r5IIX2rVz3dGCvTNSQH8W5ocwiDVCUC7t1tXEMWUTk0= http://localhost:5984/obsidian-sync

# Test via Nginx (from external)
curl -u obsidian:nzQWlmuIHuhfflUIDeYKp4lQZKGWhgWKo+vctFNlwjI= http://37.27.209.193/obsidian/
```

### Disk Usage
```bash
# Check data directory size
du -sh /root/obsidian-livesync/data

# Check backup directory size
du -sh /root/obsidian-livesync/backups

# Overall system disk usage
df -h
```

---

## 🔒 Security Features Deployed

✅ **CouchDB bound to localhost only** (127.0.0.1:5984)
✅ **Nginx reverse proxy** with rate limiting (10 req/sec)
✅ **Authentication required** for all CouchDB access
✅ **fail2ban** active (bans IPs after 5 failed attempts in 10 min)
✅ **UFW firewall** enabled (ports 22, 80, 4243 allowed)
✅ **Security headers** (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
✅ **CORS configured** for Obsidian client compatibility
✅ **Automated daily backups** with 14-day retention

---

## 🚀 Architecture

```
Internet → Nginx (Port 80) → CouchDB (localhost:5984)
           ↓
       Rate Limiting
       fail2ban
       Security Headers
```

**Existing Services:**
- WireGuard Dashboard on port 4243 (SSL) - unchanged
- Obsidian LiveSync on port 80 at `/obsidian` path

---

## 📁 File Locations

| Component | Location |
|-----------|----------|
| Docker Compose | `/root/obsidian-livesync/docker-compose.yml` |
| Environment File | `/root/obsidian-livesync/.env` |
| CouchDB Config | `/root/obsidian-livesync/local.ini` |
| Data Directory | `/root/obsidian-livesync/data` |
| Backup Directory | `/root/obsidian-livesync/backups` |
| Backup Script | `/root/obsidian-livesync/backup.sh` |
| Nginx Config | `/etc/nginx/sites-available/obsidian-livesync` |
| fail2ban Jail | `/etc/fail2ban/jail.d/nginx-obsidian.conf` |
| fail2ban Filter | `/etc/fail2ban/filter.d/nginx-obsidian.conf` |

---

## 🆘 Troubleshooting

### Connection Issues
1. Check CouchDB is running: `docker ps | grep obsidian`
2. Check Nginx is running: `systemctl status nginx`
3. Test local CouchDB: `curl http://localhost:5984/`
4. Check firewall: `ufw status`
5. Review logs: `docker logs obsidian-couchdb`

### Sync Problems in Obsidian
1. Verify credentials match exactly
2. Check database name is `obsidian-sync`
3. Test connection in plugin settings
4. Check Nginx logs: `tail /var/log/nginx/obsidian-error.log`
5. Ensure no firewall blocking from client side

### Performance Issues
1. Check disk space: `df -h`
2. Check data size: `du -sh /root/obsidian-livesync/data`
3. Review CouchDB logs for errors
4. Consider increasing rate limits in Nginx config

---

## 🔐 JWT Authentication

**CouchDB Version:** 3.5.0 (upgraded from 3.4)
**JWT Status:** ⚠️ Configured but NOT Working

JWT authentication has been fully configured according to official CouchDB 3.5 documentation. The `jwtf` module is installed, configuration is correct, and tokens are properly signed, but CouchDB is not accepting JWT tokens for unknown reasons.

**Current Working Authentication:** Basic Authentication (username + password)

### JWT Documentation & Tools:
- **Detailed Status Report:** `/root/obsidian-livesync/JWT-STATUS.md`
- **Configuration Guide:** `/root/obsidian-livesync/JWT-AUTH-README.md`
- **Token Generator (Python):** `/root/obsidian-livesync/generate-jwt.py`
- **Token Generator (Bash):** `/root/obsidian-livesync/generate-jwt.sh`

### JWT Configuration Summary:
```ini
[chttpd_auth]
authentication_handlers = {chttpd_auth, cookie_authentication_handler}, {chttpd_auth, jwt_authentication_handler}, {chttpd_auth, default_authentication_handler}

[jwt_auth]
required_claims = exp,sub

[jwt_keys]
hmac:_default = pHhkegdm+1rsKx3NjgRMcJkkmTBWeQsEJSD1/LKt78R694lV4Gm6G0B7gktL+YuswpjrwAglQPXDpzBQo3CR/Q==
```

All configuration is in place and tokens generate correctly, but authentication fails. See JWT-STATUS.md for detailed analysis and troubleshooting steps.

## 📞 Support Resources

- **Obsidian LiveSync Plugin:** [GitHub](https://github.com/vrtmrz/obsidian-livesync)
- **CouchDB Docs:** [https://docs.couchdb.org/](https://docs.couchdb.org/)
- **Nginx Docs:** [https://nginx.org/en/docs/](https://nginx.org/en/docs/)
- **CouchDB JWT Plugin:** [GitHub](https://github.com/softapalvelin/couch_jwt_auth)

---

## 🔄 Upgrading CouchDB

```bash
cd /root/obsidian-livesync

# Pull latest CouchDB image
docker compose pull

# Recreate container with new image
docker compose up -d

# Verify upgrade
docker logs obsidian-couchdb
```

---

**Deployment Date:** 2025-10-05
**Generated by:** Claude Code (Anthropic)
