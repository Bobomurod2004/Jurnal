#!/bin/bash
# SSL Certificate Setup Script for Let's Encrypt
# Run this ONCE on the production server to obtain initial SSL certificates
#
# Usage: sudo ./scripts/init-ssl.sh your-domain.tld your@email.com

set -e

if [ $# -lt 1 ]; then
    echo "Usage: sudo ./scripts/init-ssl.sh your-domain.tld your@email.com"
    exit 1
fi

DOMAIN="$1"
EMAIL=${2:-"admin@$DOMAIN"}

echo "=========================================="
echo " SSL Certificate Setup"
echo " Domain: $DOMAIN"
echo " Email:  $EMAIL"
echo "=========================================="

mkdir -p /var/www/certbot/.well-known/acme-challenge
mkdir -p /etc/nginx/certs

# Check if certificate already exists on this server
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo ""
    echo "SSL sertifikat allaqachon mavjud!"
    echo "  /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo ""
    echo "To'g'ridan-to'g'ri ishga tushiring:"
    echo "  docker compose up -d --build"
    echo ""
    read -p "Yangi sertifikat olishni xohlaysizmi? (y/N): " RENEW
    if [ "$RENEW" != "y" ] && [ "$RENEW" != "Y" ]; then
        echo "Mavjud sertifikat ishlatiladi. docker compose up -d --build buyrug'ini ishga tushiring."
        exit 0
    fi
fi

# Step 1: Start nginx with HTTP-only config first
echo ""
echo "[1/5] Preparing temporary HTTP-only nginx config..."

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

echo "[2/5] Starting services with temporary config..."
docker compose up -d nginx

sleep 5

echo "[3/5] Obtaining SSL certificate from Let's Encrypt..."
certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

echo "[4/5] Copying certificate into /etc/nginx/certs/..."
cp -L "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /etc/nginx/certs/fullchain.pem
cp -L "/etc/letsencrypt/live/$DOMAIN/privkey.pem" /etc/nginx/certs/privkey.pem
chmod 644 /etc/nginx/certs/fullchain.pem
chmod 600 /etc/nginx/certs/privkey.pem

echo "[5/5] Restoring production nginx config with SSL..."
cp ./nginx/nginx.conf.bak ./nginx/nginx.conf
rm -f ./nginx/nginx.conf.bak

# Restart nginx with full SSL config
docker compose restart nginx

echo ""
echo "=========================================="
echo " SSL Setup Complete!"
echo " https://$DOMAIN should now work"
echo ""
echo "Note: configure host-side certbot renewal"
echo "and refresh /etc/nginx/certs/{fullchain.pem,privkey.pem} after renewals."
echo "=========================================="
