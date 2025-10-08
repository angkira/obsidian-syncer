#!/bin/bash
# Obsidian LiveSync Server - Automated Deployment Script

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║   Obsidian LiveSync Server - Deployment Script       ║
║   Self-hosted sync with JWT authentication           ║
╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check requirements
echo "🔍 Checking requirements..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "   Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "   Install from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [[ ! $reconfigure =~ ^[Yy]$ ]]; then
        echo "Using existing .env file"
        skip_config=true
    fi
fi

if [ "$skip_config" != "true" ]; then
    echo ""
    echo "📝 Configuration"
    echo "==============="

    # Domain
    read -p "Enter your domain (e.g., obsidian.example.com): " domain
    while [ -z "$domain" ]; do
        echo -e "${RED}Domain cannot be empty${NC}"
        read -p "Enter your domain: " domain
    done

    # SSL Email
    read -p "Enter email for SSL certificates: " ssl_email
    while [ -z "$ssl_email" ]; do
        echo -e "${RED}Email cannot be empty${NC}"
        read -p "Enter email: " ssl_email
    done

    # SSL Method
    echo ""
    echo "SSL Method Options:"
    echo "  1) letsencrypt - Automatic SSL with Let's Encrypt (recommended)"
    echo "  2) manual - Provide your own certificates"
    echo "  3) none - HTTP only (not recommended for production)"
    read -p "Choose SSL method (1-3) [1]: " ssl_choice
    ssl_choice=${ssl_choice:-1}

    case $ssl_choice in
        1) ssl_method="letsencrypt" ;;
        2) ssl_method="manual" ;;
        3) ssl_method="none" ;;
        *) ssl_method="letsencrypt" ;;
    esac

    # Create .env from template
    echo ""
    echo "🔧 Creating configuration..."
    cp .env.example .env

    # Set domain and SSL
    sed -i "s/DOMAIN=.*/DOMAIN=$domain/" .env
    sed -i "s|PUBLIC_URL=.*|PUBLIC_URL=https://$domain|" .env
    sed -i "s/SSL_EMAIL=.*/SSL_EMAIL=$ssl_email/" .env
    sed -i "s/SSL_METHOD=.*/SSL_METHOD=$ssl_method/" .env

    # Generate secrets
    echo "🔐 Generating secrets..."
    ./scripts/generate-secrets.sh >> .env

    echo -e "${GREEN}✅ Configuration created${NC}"
fi

# Build and start services
echo ""
echo "🐳 Building Docker images..."
docker-compose -f docker-compose.yml build

echo ""
echo "🚀 Starting services..."
docker-compose -f docker-compose.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Initialize CouchDB
echo ""
echo "🔧 Initializing CouchDB..."
./scripts/init-couchdb.sh

# Setup SSL if using Let's Encrypt
if grep -q "SSL_METHOD=letsencrypt" .env && [ "$ssl_method" = "letsencrypt" ]; then
    echo ""
    read -p "Setup SSL certificates now? (Y/n): " setup_ssl
    if [[ ! $setup_ssl =~ ^[Nn]$ ]]; then
        ./scripts/setup-ssl.sh "$domain" "$ssl_email"
    else
        echo -e "${YELLOW}⚠️  SSL not configured. Run: ./scripts/setup-ssl.sh $domain $ssl_email${NC}"
    fi
fi

# Final status
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🎉 Deployment Complete! 🎉               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Setup your first device:"
echo "   docker exec obsidian-auth python3 setup_uri.py \"MyPhone\""
echo ""
echo "2. Manage device tokens:"
echo "   docker exec obsidian-auth python3 cli.py list"
echo ""
echo "3. View logs:"
echo "   docker-compose -f docker-compose.yml logs -f"
echo ""
echo "4. Backup database:"
echo "   docker exec obsidian-couchdb /backups/backup.sh"
echo ""
echo "📚 Documentation: ./README.md"
echo ""
