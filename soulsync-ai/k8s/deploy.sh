#!/bin/bash
# ─── SoulSync AI - Kubernetes Deploy Script ───────────────
# Usage: bash k8s/deploy.sh

set -e

echo "🚀 Deploying SoulSync AI to Kubernetes..."
echo "============================================"

# Step 1: Build Docker images
echo ""
echo "[1/5] Building Docker images..."
docker build -f docker/Dockerfile.backend  -t soulsync-backend:latest  .
docker build -f docker/Dockerfile.frontend -t soulsync-frontend:latest .
echo "✅ Images built"

# Step 2: Apply namespace
echo ""
echo "[2/5] Creating namespace..."
kubectl apply -f k8s/namespace.yaml
echo "✅ Namespace: soulsync"

# Step 3: Apply config
echo ""
echo "[3/5] Applying config and secrets..."
kubectl apply -f k8s/configmap.yaml
echo "✅ ConfigMap + Secrets applied"

# Step 4: Deploy PostgreSQL
echo ""
echo "[4/5] Deploying PostgreSQL..."
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
echo "✅ PostgreSQL deployed"

# Step 5: Deploy Backend + Frontend
echo ""
echo "[5/5] Deploying Backend + Frontend..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
echo "✅ Backend + Frontend deployed"

# Wait for pods
echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod \
    -l app=soulsync-postgres \
    -n soulsync \
    --timeout=120s

kubectl wait --for=condition=ready pod \
    -l app=soulsync-backend \
    -n soulsync \
    --timeout=180s

kubectl wait --for=condition=ready pod \
    -l app=soulsync-frontend \
    -n soulsync \
    --timeout=60s

# Show status
echo ""
echo "============================================"
echo "✅ SoulSync AI deployed successfully!"
echo "============================================"
echo ""
kubectl get pods -n soulsync
echo ""
echo "🌐 Access the app:"
echo "   Frontend : http://localhost:30080"
echo "   Backend  : http://localhost:8000"
echo "   API Docs : http://localhost:8000/docs"
