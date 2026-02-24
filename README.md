# Kubernetes-Cluster-Monitoring-and-Alerting-using-Prometheus-and-Grafana-on-AWS-EKS

Kubernetes Cluster Monitoring on AWS EKS with Prometheus & Grafana

This project demonstrates a complete, end-to-end DevOps pipeline to deploy, monitor, and manage a cloud-native application on AWS.

The project deploys a sample Python Flask application to a Kubernetes (EKS) cluster. The deployment is fully automated via GitHub Actions, which builds and pushes the application container to ECR. Finally, the cluster's health and application-specific metrics are monitored in real-time using Prometheus and visualized on a Grafana dashboard.

🧭 Project Goal

To design, deploy, and monitor a cloud-native Kubernetes environment on AWS, demonstrating real-time observability through Prometheus and Grafana to provide insights into cluster performance, resource utilization, and application health.

⚙️ System Architecture

The high-level architecture of the project is as follows:

           ┌────────────────────────────────────┐
           │            AWS Cloud               │
           │                                    │
           │   ┌──────────────┐    ┌────────┐   │
           │   │  CI/CD (GitHub│    │  ECR   │   │
User Push ─▶│   │  Actions)     │──▶│ Docker │   │
           │   └──────────────┘    │ Images │   │
           │          │             └────────┘   │
           │          ▼                         │
           │   ┌────────────────────────────┐    │
           │   │     AWS EKS Cluster        │    │
           │   │  ┌─────────────┐           │    │
           │   │  │ App Pods    │           │    │
           │   │  ├─────────────┤           │    │
           │   │  │ Prometheus  │◀──────────│─── Metrics Scraped
           │   │  │ AlertManager│           │    │
           │   │  │ Grafana     │──────────▶│─── Dashboards Viewed by User
           │   └────────────────────────────┘    │
           │                                    │
           └────────────────────────────────────┘


✨ Key Features

Automated CI/CD: On every git push to the main branch, GitHub Actions automatically builds the Docker image, pushes it to ECR, and deploys the new version to the EKS cluster.

Infrastructure as a Service: Uses AWS EKS for a managed, scalable, and resilient Kubernetes control plane.

Containerized Application: A lightweight Python Flask application containerized with Docker.

Real-time Metrics: Prometheus automatically scrapes custom metrics from the application (e.g., HTTP request counts) and infrastructure metrics from the cluster (CPU, memory, etc.).

Observability Dashboard: Grafana provides a rich, interactive dashboard to visualize all collected metrics, pre-configured with a Prometheus data source.

🛠️ Tech Stack

Cloud Provider: AWS (Amazon Web Services)

Compute: Amazon EKS (Elastic Kubernetes Service)

Container Registry: Amazon ECR (Elastic Container Registry)

Application: Python (Flask), Docker

CI/CD: GitHub Actions

Monitoring: Prometheus

Visualization: Grafana

Deployment Tools: kubectl, helm

Infrastructure CLI: aws-cli, eksctl

🏁 Getting Started

Follow these steps to deploy the entire project from scratch.

Prerequisites

An AWS Account with IAM permissions to create EKS, ECR, VPC, and IAM resources.

A GitHub Account.

The following tools installed locally:

aws-cli (configured with your credentials)

eksctl

kubectl

helm

docker

Phase 1: Create AWS Infrastructure

First, create the ECR repository to store your Docker images and the EKS cluster to run them.

Create ECR Repository:

aws ecr create-repository --repository-name my-cloud-project-app --region <your-region>


IMPORTANT: Note the repositoryUri from the output. You will need this for the GitHub Secrets.

Create EKS Cluster:
This command provisions the entire cluster, VPC, and node groups. It will take 15-20 minutes.

eksctl create cluster \
  --name my-cluster \
  --region <your-region> \
  --version 1.28 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2


eksctl will automatically configure your local kubectl to point to the new cluster.

Phase 2: Configure GitHub Repository & Secrets

Push to GitHub: Clone this repository and push it to your own new GitHub repository.

Add Repository Secrets: In your GitHub repository, go to Settings > Secrets and variables > Actions and add the following secrets. The CI/CD pipeline uses these to log in to AWS and deploy to your cluster.

AWS_ACCESS_KEY_ID: Your AWS access key.

AWS_SECRET_ACCESS_KEY: Your AWS secret key.

AWS_REGION: Your AWS region (e.g., us-east-1).

EKS_CLUSTER_NAME: my-cluster (or the name you chose).

ECR_REPOSITORY: my-cloud-project-app (the short name).

ECR_REGISTRY: The full repositoryUri from Phase 1 (e.g., <aws_account_id>.dkr.ecr.<your-region>.amazonaws.com).

Phase 3: Deploy the Application (CI/CD)

The deployment is now fully automated.

Trigger the Pipeline: Make a small change to any file (like adding a space to this README.md) and push it to your main branch.

git commit -m "Trigger initial deployment"
git push origin main


Monitor the Pipeline: Go to the Actions tab in your GitHub repository. You will see the Build, Push, and Deploy to EKS workflow running. It will:

Build the Docker image.

Log in to ECR and push the image.

Log in to your EKS cluster and apply the app-deployment.yaml and app-service.yaml files.

Phase 4: Install the Monitoring Stack

This final one-time setup installs Prometheus and Grafana on your cluster.

Add the Prometheus Helm repository:

helm repo add prometheus-community [https://prometheus-community.github.io/helm-charts](https://prometheus-community.github.io/helm-charts)
helm repo update


Install the kube-prometheus-stack:
This installs Prometheus, Grafana, and Alertmanager in a new monitoring namespace.

helm install my-monitoring-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace


Usage

Accessing the Web Application

Wait a minute for the Load Balancer to be created. Check its status:

kubectl get service my-web-app-service


Copy the EXTERNAL-IP (or hostname) and paste it into your browser. You should see "Hello! Your EKS application is running."

Accessing the Grafana Dashboard

Get the Grafana Admin Password:

kubectl get secret --namespace monitoring my-monitoring-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo


Access the Dashboard from your Local Machine:
Open a new terminal and run this command. It forwards the Grafana service to your localhost.

kubectl port-forward --namespace monitoring svc/my-monitoring-stack-grafana 8080:80


Log In:

Open http://localhost:8080 in your browser.

Username: admin

Password: (The password from step 1).

You can now go to Dashboards > Browse and explore pre-built dashboards like "Kubernetes / Compute Resources / Cluster" to see your cluster's health.

📂 File Structure

.
├── .github/workflows/
│   └── main.yml        # The CI/CD pipeline script
├── app-deployment.yaml     # Kubernetes manifest for the app deployment
├── app-service.yaml        # Kubernetes manifest for the Load Balancer
├── app.py                  # The Python Flask application code
├── Dockerfile              # Instructions to build the app container
├── requirements.txt        # Python dependencies
└── README.md               # This file


👥 Team Roles

Shreya Patel: Infrastructure & CI/CD (EKS Architecture, Dockerization, GitHub Actions).

Nandini Mandaviya: Observability (Prometheus Stack, PromQL, Grafana Dashboards).

Aditya Desai: Remediation (SNS Middleware, Lambda Logic, Kubernetes RBAC).
