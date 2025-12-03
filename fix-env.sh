#!/bin/bash
# Script to fix environment variable issues on remote server

echo "Creating .env symlink to .env.production..."
cd ~/Documents/booklook
ln -sf .env.production .env

echo "Done! Now restart services with:"
echo "docker-compose -f docker-compose.prod.yml down"
echo "docker-compose -f docker-compose.prod.yml up -d --build"
