#!/bin/bash
# Setup SSL certificates using Let's Encrypt

set -e

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 obsidian.example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo "🔒 Setting up SSL certificates for $DOMAIN"
echo "📧 Using email: $EMAIL"

# Check if nginx container is running
if ! docker ps | grep -q obsidian-nginx; then
    echo "❌ nginx container not running. Start services first with: docker-compose up -d"
    exit 1
fi

# Request certificate using certbot
echo "📝 Requesting SSL certificate from Let's Encrypt..."
docker exec obsidian-nginx certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
    echo "🔄 Reloading nginx configuration..."

    # Reload nginx to use new certificates
    docker exec obsidian-nginx nginx -s reload

    echo "✅ SSL setup complete!"
    echo ""
    echo "📋 Certificate locations (inside container):"
    echo "   - Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "   - Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo ""
    echo "🔄 Certificates will auto-renew every 12 hours"
else
    echo "❌ Failed to obtain SSL certificate"
    echo "   Make sure:"
    echo "   1. Domain $DOMAIN points to this server's IP"
    echo "   2. Ports 80 and 443 are accessible"
    echo "   3. No firewall blocking HTTP/HTTPS"
    exit 1
fi
