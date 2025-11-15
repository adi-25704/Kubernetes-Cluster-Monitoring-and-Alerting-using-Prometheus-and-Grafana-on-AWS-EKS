#!/bin/bash

# --- 1. EDIT THESE VARIABLES ---
# Get this from your AWS Console (top right, under your name)
AWS_ACCOUNT_ID="398456183297"

# The region your EKS cluster is in (e.g., us-east-1)
AWS_REGION="us-east-1"

# The name of your ECR repository
REPO_NAME="kubernetes-cluster-monitoring-and-alerting-using-prometheus-and-grafana-on-aws-eks"

# The tag for your image
IMAGE_TAG="v1.0.0"
# --------------------------------

# Stop script on any error
set -e

# Construct the full ECR repository URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

echo "ECR URI: ${ECR_URI}"
echo "Image Tag: ${IMAGE_TAG}"

echo "--- Logging in to AWS ECR ---"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "--- Building Docker image ---"
# Build the image and tag it with the ECR URI and tag
docker build -t ${ECR_URI}:${IMAGE_TAG} .
docker tag ${ECR_URI}:${IMAGE_TAG} ${ECR_URI}:latest

echo "--- Pushing image to ECR ---"
# Push both tags
docker push ${ECR_URI}:${IMAGE_TAG}
docker push ${ECR_URI}:latest

echo "--- Deploying to EKS ---"

# 1. Apply the service (this creates the Load Balancer)
kubectl apply -f app-service.yaml

# 2. Apply the deployment
# This command reads the app-deployment.yaml file,
# replaces the placeholder URI with your real ECR URI,
# and pipes the new, correct YAML directly into kubectl.
echo "Updating deployment with image: ${ECR_URI}:latest"
sed "s|398456183297.dkr.ecr.ap-southeast-1.amazonaws.com/kubernetes-cluster-monitoring-and-alerting-using-prometheus-and-grafana-on-aws-eks|${ECR_URI}:latest|g" app-deployment.yaml | kubectl apply -f -

echo "--- Deployment Complete! ---"
echo "Waiting for pods to be ready..."
kubectl rollout status deployment/my-web-app

echo "You can now find your Load Balancer address by running:"
echo "kubectl get service my-web-app-service"