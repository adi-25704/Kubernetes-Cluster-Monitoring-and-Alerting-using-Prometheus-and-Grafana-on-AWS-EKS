#!/bin/bash

AWS_ACCOUNT_ID="398456183297"

AWS_REGION="us-east-1"

REPO_NAME="kubernetes-cluster-monitoring-and-alerting-using-prometheus-and-grafana-on-aws-eks"

IMAGE_TAG="v1.0.0"

set -e

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

echo "ECR URI: ${ECR_URI}"
echo "Image Tag: ${IMAGE_TAG}"

echo "--- Logging in to AWS ECR ---"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "--- Building Docker image ---"

docker build -t ${ECR_URI}:${IMAGE_TAG} .
docker tag ${ECR_URI}:${IMAGE_TAG} ${ECR_URI}:latest

echo "--- Pushing image to ECR ---"

docker push ${ECR_URI}:${IMAGE_TAG}
docker push ${ECR_URI}:latest

echo "--- Deploying to EKS ---"

kubectl apply -f app-service.yaml

echo "Updating deployment with image: ${ECR_URI}:latest"
sed "s|398456183297.dkr.ecr.us-east-1.amazonaws.com/kubernetes-cluster-monitoring-and-alerting-using-prometheus-and-grafana-on-aws-eks|${ECR_URI}:latest|g" app-deployment.yaml | kubectl apply -f -

echo "--- Deployment Complete! ---"
echo "Waiting for pods to be ready..."
kubectl rollout status deployment/my-web-app

echo "You can now find your Load Balancer address by running:"
echo "kubectl get service my-web-app-service"