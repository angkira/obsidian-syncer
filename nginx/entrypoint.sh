#!/bin/sh
set -e

echo "🔧 Configuring nginx..."

# Replace environment variables in nginx config template
envsubst '${DOMAIN} ${AUTH_PROXY_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Check SSL method
if [ "$SSL_METHOD" = "letsencrypt" ]; then
    echo "🔒 SSL Method: Let's Encrypt"

    # Check if certificates exist
    if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
        echo "⚠️  SSL certificates not found. Starting nginx in HTTP-only mode."
        echo "⚠️  Run 'docker exec obsidian-nginx certbot certonly --webroot -w /var/www/certbot -d ${DOMAIN} --email ${SSL_EMAIL} --agree-tos --no-eff-email' to obtain certificates."

        # Create a temporary HTTP-only config
        cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://auth-proxy:${AUTH_PROXY_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    else
        echo "✅ SSL certificates found"
    fi

elif [ "$SSL_METHOD" = "manual" ]; then
    echo "🔒 SSL Method: Manual certificates"
    echo "⚠️  Ensure certificates are mounted at /etc/letsencrypt/live/${DOMAIN}/"

elif [ "$SSL_METHOD" = "none" ]; then
    echo "⚠️  SSL Method: None (HTTP only)"

    # Create HTTP-only config
    cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://auth-proxy:${AUTH_PROXY_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

echo "✅ nginx configuration ready"
echo "🚀 Starting nginx..."

# Test nginx configuration
nginx -t

# Execute the CMD (nginx)
exec "$@"
