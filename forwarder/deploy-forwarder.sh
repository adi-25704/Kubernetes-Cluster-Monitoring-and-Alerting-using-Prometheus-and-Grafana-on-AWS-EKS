#!/bin/bash
set -e

AWS_REGION="us-east-1"
REPO_NAME="my-sns-forwarder" 

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

echo "Target ECR: ${ECR_URI}"

aws ecr describe-repositories --repository-names ${REPO_NAME} --region ${AWS_REGION} > /dev/null 2>&1 || \
    aws ecr create-repository --repository-name ${REPO_NAME} --region ${AWS_REGION}

aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "Building Image..."
docker build -t ${ECR_URI}:latest .

echo "Pushing Image..."
docker push ${ECR_URI}:latest

echo "--- Image Pushed Successfully ---"
echo "Image URI: ${ECR_URI}:latest"