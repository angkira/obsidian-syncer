FROM nginx:alpine

# Install certbot for Let's Encrypt
RUN apk add --no-cache certbot certbot-nginx

# Copy nginx configurations
COPY ssl-params.conf /etc/nginx/ssl-params.conf

# Create directories for certificates and ACME challenge
RUN mkdir -p /var/www/certbot /etc/letsencrypt

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
