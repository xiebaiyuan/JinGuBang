#!/bin/bash
docker container prune -f
docker image prune -a -f
docker volume prune -f
docker network prune -f
docker system prune -a -f

echo "Cleaning up Docker build cache and history..."
docker builder prune -a -f
docker image prune --filter label=stage=intermediate -f
docker system prune -a -f
echo "Docker build cache and history cleaned up."
