#!/bin/bash
# SSL Certificate Setup Script for Let's Encrypt
# Run this ONCE on the production server to obtain initial SSL certificates
#
# Usage: ./scripts/init-ssl.sh philologymatters.uz your@email.com

set -e

DOMAIN=${1:-"philologymatters.uz"}
EMAIL=${2:-"admin@$DOMAIN"}

echo "=========================================="
echo " SSL Certificate Setup"
echo " Domain: $DOMAIN"
echo " Email:  $EMAIL"
echo "=========================================="

# Step 1: Start nginx with HTTP-only config first
echo ""
echo "[1/4] Preparing temporary HTTP-only nginx config..."

# Create temporary nginx config for ACME challenge only
cat > /tmp/nginx_temp.conf << 'NGINX_CONF'
events {
    worker_connections 1024;
}
http {
    server {
        listen 80;
        server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 200 'SSL setup in progress...';
            add_header Content-Type text/plain;
        }
    }
}
NGINX_CONF

sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /tmp/nginx_temp.conf

# Temporarily use the simple config
cp ./nginx/nginx.conf ./nginx/nginx.conf.bak
cp /tmp/nginx_temp.conf ./nginx/nginx.conf

echo "[2/4] Starting services with temporary config..."
docker compose up -d nginx

sleep 3

echo "[3/4] Obtaining SSL certificate from Let's Encrypt..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

echo "[4/4] Restoring production nginx config with SSL..."
cp ./nginx/nginx.conf.bak ./nginx/nginx.conf
rm -f ./nginx/nginx.conf.bak

# Restart nginx with full SSL config
docker compose restart nginx

echo ""
echo "=========================================="
echo " SSL Setup Complete!"
echo " https://$DOMAIN should now work"
echo ""
echo " Auto-renewal is handled by the certbot"
echo " container in docker-compose.yml"
echo "=========================================="
