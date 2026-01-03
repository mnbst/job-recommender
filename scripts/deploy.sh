#!/bin/bash
set -e

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Deploy Script ===${NC}"

# プロジェクトIDを取得
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP project not set. Run 'gcloud config set project <project-id>'${NC}"
    exit 1
fi

REGION="asia-northeast1"
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/job-recommender/app:latest"

echo -e "${GREEN}Project: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Image: ${IMAGE_URL}${NC}"
echo ""

# Step 1: Build and push Docker image
echo -e "${YELLOW}Step 1: Building and pushing Docker image...${NC}"
gcloud builds submit --tag "${IMAGE_URL}" .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to build and push image${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Image pushed successfully${NC}"
echo ""

# Step 2: Terraform apply
echo -e "${YELLOW}Step 2: Running terraform apply...${NC}"
cd terraform
terraform apply -auto-approve

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Terraform apply failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Terraform apply completed${NC}"
echo ""

# Output URLs
echo -e "${YELLOW}=== Deployment Complete ===${NC}"
terraform output
