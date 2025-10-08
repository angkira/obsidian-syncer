# 🔄 Obsidian LiveSync Server

Self-hosted synchronization server for [Obsidian LiveSync](https://github.com/vrtmrz/obsidian-livesync) with JWT-based per-device authentication.

## ✨ Features

- **🔐 JWT Per-Device Authentication** - Generate unique tokens for each device, revoke individually
- **🔒 End-to-End Encryption** - Data encrypted client-side before sync
- **🐳 Docker Deployment** - Easy setup with Docker Compose
- **🔑 Automatic SSL** - Let's Encrypt integration with auto-renewal
- **📱 One-Click Device Setup** - Generate encrypted setup URIs for instant configuration
- **💾 Automatic Backups** - Scheduled CouchDB backups
- **📊 Token Management** - CLI tools for device management
- **⚡ High Performance** - Async Python proxy with connection pooling

## 📋 Prerequisites

- **Docker** & **Docker Compose**
- **Domain name** pointing to your server
- **Ports 80 and 443** open for HTTPS

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/angkira/obsidian-livesync-server.git
cd obsidian-livesync-server
```

### 2. Deploy

```bash
./deploy.sh
```

The script will:
- Ask for your domain and email
- Generate all secrets automatically
- Build Docker images
- Start services
- Initialize CouchDB
- Setup SSL certificates (Let's Encrypt)

### 3. Create Device Token

```bash
make setup-device DEVICE="MyPhone"
```

This generates a JWT token for your device.

### 4. Configure Obsidian

**In Obsidian LiveSync Settings:**

1. **Remote Database Configuration:**
   - URI: `https://your-domain.com/obsidian`
   - Database name: `obsidian-sync`
   - Username: `obsidian`
   - Password: `<paste-your-jwt-token>`
   - End to end encryption: (leave empty for now)

2. **Encryption Settings (Recommended):**
   - Enable End-to-End Encryption
   - Set a strong passphrase (same on all devices)
   - Enable Path Obfuscation

3. **Done!** Start syncing

**Note:** The JWT token goes in the **Password** field, NOT in Custom Request Header. The auth proxy will validate it as Basic Auth.

## 🎯 Alternative: Manual Setup

If you prefer manual configuration:

### 1. Copy and Configure .env

```bash
cp .env.example .env
nano .env
```

Set your `DOMAIN`, `SSL_EMAIL`, and other values.

### 2. Generate Secrets

```bash
./scripts/generate-secrets.sh >> .env
```

### 3. Start Services

```bash
docker-compose -f docker-compose.yml up -d
```

### 4. Initialize CouchDB

```bash
./scripts/init-couchdb.sh
```

### 5. Setup SSL

```bash
./scripts/setup-ssl.sh your-domain.com your@email.com
```

## 🛠️ Management Commands

### Using Makefile (Recommended)

```bash
make help              # Show all commands
make start             # Start services
make stop              # Stop services
make restart           # Restart services
make logs              # View logs
make status            # Show service status
make setup-device DEVICE="iPhone"  # Setup new device
make list-devices      # List all devices
make backup            # Backup database
make ssl-renew         # Renew SSL certificates
```

### Using Docker Directly

```bash
# Setup device
docker exec obsidian-auth python3 setup_uri.py "MyPhone"

# List devices
docker exec obsidian-auth python3 cli.py list

# Revoke device
docker exec obsidian-auth python3 cli.py revoke <token-id>

# View logs
docker-compose -f docker-compose.yml logs -f

# Backup
docker exec obsidian-couchdb /app/scripts/backup.sh
```

## 📱 Device Management

### Create Device Token

```bash
make setup-device DEVICE="MyLaptop"
```

Outputs:
```
✅ Token created for device: MyLaptop

📱 Device Name: MyLaptop
🔑 Token ID: actNnsfSJO2KLMJdzhSt0Wu12qXGeERH...
📅 Created: 2025-10-06T18:25:12
⏰ Expires: Never

🎫 JWT Token:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl9pZCI6ImFjdE5uc2...

📋 Usage in Obsidian:
  - Username: obsidian
  - Password: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

💾 Save this token - it won't be shown again!
```

**Then configure Obsidian:**
- Settings → Community Plugins → Self-hosted LiveSync
- Remote Database Configuration
  - **Username:** `obsidian`
  - **Password:** `<paste-your-jwt-token>`

### List All Devices

```bash
make list-devices
```

### Revoke Device

Lost your phone? Revoke access instantly:

```bash
docker exec obsidian-auth python3 cli.py revoke <token-id>
```

## 🔒 SSL/HTTPS Setup

### Option 1: Let's Encrypt (Automatic)

Set in `.env`:
```bash
SSL_METHOD=letsencrypt
DOMAIN=obsidian.example.com
SSL_EMAIL=admin@example.com
```

Certificates auto-renew every 12 hours.

### Option 2: Manual Certificates

1. Set `SSL_METHOD=manual` in `.env`
2. Mount certificates:
   ```yaml
   volumes:
     - /path/to/fullchain.pem:/etc/letsencrypt/live/${DOMAIN}/fullchain.pem:ro
     - /path/to/privkey.pem:/etc/letsencrypt/live/${DOMAIN}/privkey.pem:ro
   ```

### Option 3: HTTP Only (Development)

Set `SSL_METHOD=none` in `.env`

⚠️ **Not recommended for production!**

## 🚀 Advanced: Automatic Setup URI (Optional)

For advanced users who want one-click device configuration, the system can generate encrypted setup URIs:

```bash
# Generate setup URI with encryption
docker exec obsidian-auth python3 setup_uri.py "MyPhone"
```

This creates an `obsidian://setuplivesync?settings=...` URI that:
- Auto-configures all Obsidian settings
- Includes JWT token
- Sets up E2EE encryption
- Enables path obfuscation

**Note:** This requires reverse-engineering the Obsidian LiveSync setup URI format. For most users, **manual token setup is simpler and recommended**.

## 🏗️ Architecture

```
                         ┌─────────────┐
                         │   Clients   │
                         │  (Obsidian) │
                         └──────┬──────┘
                                │ HTTPS (443)
                         ┌──────▼──────┐
                         │    nginx    │
                         │  (SSL Term) │
                         └──────┬──────┘
                                │ HTTP (internal)
                    ┌───────────┴───────────┐
                    │                       │
             ┌──────▼──────┐        ┌──────▼────────┐
             │ Auth Proxy  │───────▶│   CouchDB     │
             │  (FastAPI)  │        │ (Database)    │
             │  JWT Auth   │        │               │
             └─────────────┘        └───────────────┘
                    │
             ┌──────▼──────┐
             │  Token DB   │
             │  (SQLite)   │
             └─────────────┘
```

## 🔐 Security Features

- ✅ **HTTPS** - TLS 1.2/1.3 encryption in transit
- ✅ **JWT Authentication** - Per-device tokens with revocation
- ✅ **End-to-End Encryption** - AES-256-GCM client-side encryption
- ✅ **Path Obfuscation** - Encrypted file paths
- ✅ **Rate Limiting** - 10 req/s with burst protection
- ✅ **Security Headers** - HSTS, XSS Protection, etc.
- ✅ **Automatic Updates** - Pull latest images easily

## 💾 Backup & Restore

### Automatic Backups

Backups run automatically. Configure in `.env`:

```bash
MAX_BACKUPS=14              # Keep 14 days
BACKUP_SCHEDULE=0 2 * * *   # Daily at 2 AM
```

### Manual Backup

```bash
make backup
```

Backups stored in Docker volume `backups`.

### Restore

```bash
# Extract backup
docker exec obsidian-couchdb tar -xzf /backups/couchdb_backup_20251006.tar.gz -C /opt/couchdb

# Restart CouchDB
docker-compose -f docker-compose.yml restart couchdb
```

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check logs
make logs

# Check service status
make status

# Restart services
make restart
```

### SSL Certificate Issues

```bash
# Check certificate
docker exec obsidian-nginx ls -la /etc/letsencrypt/live/${DOMAIN}/

# Manually request certificate
docker exec obsidian-nginx certbot certonly --webroot \
  -w /var/www/certbot -d your-domain.com \
  --email your@email.com --agree-tos
```

### Can't Connect from Obsidian

1. **Check DNS**: Ensure domain points to your server
   ```bash
   nslookup your-domain.com
   ```

2. **Check ports**: Verify 80/443 are open
   ```bash
   netstat -tuln | grep -E ':80|:443'
   ```

3. **Check services**:
   ```bash
   make status
   ```

4. **Check logs**:
   ```bash
   docker-compose -f docker-compose.yml logs nginx auth-proxy
   ```

### Authentication Failed

1. **List tokens**: Verify token exists
   ```bash
   make list-devices
   ```

2. **Check token info**:
   ```bash
   docker exec obsidian-auth python3 cli.py info <token-id>
   ```

3. **Generate new token**: If revoked or expired
   ```bash
   make setup-device DEVICE="NewDevice"
   ```

## 📈 Upgrading

### Update to Latest Version

```bash
git pull origin main
docker-compose -f docker-compose.yml pull
docker-compose -f docker-compose.yml up -d --build
```

### Migrating Data

See [docs/MIGRATION.md](docs/MIGRATION.md) for detailed instructions.

## 🌟 Environment Variables

See [.env.example](.env.example) for full documentation.

**Key Variables**:

| Variable | Description | Default |
|----------|-------------|---------|
| `DOMAIN` | Your domain name | `obsidian.example.com` |
| `PUBLIC_URL` | Public HTTPS URL | `https://${DOMAIN}` |
| `SSL_METHOD` | SSL method | `letsencrypt` |
| `COUCHDB_USER` | CouchDB admin user | `admin` |
| `DB_NAME` | Database name | `obsidian-sync` |
| `JWT_HMAC_SECRET` | JWT signing secret | Auto-generated |
| `ADMIN_TOKEN` | Admin API token | Auto-generated |

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Credits

- [Obsidian LiveSync](https://github.com/vrtmrz/obsidian-livesync) by vrtmrz
- [CouchDB](https://couchdb.apache.org/)
- [FastAPI](https://fastapi.tiangolo.com/)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/angkira/obsidian-livesync-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/angkira/obsidian-livesync-server/discussions)

---

**Made with ❤️ for the Obsidian community**
