#!/bin/bash
set -e

CLUSTER="obs-platform-dev"
REGION="us-east-1"

echo "============================"
echo "Deleting EKS CLUSTER"
echo "============================"

eksctl delete cluster --name $CLUSTER --region $REGION || true


echo "============================"
echo "Deleting NODEGROUPS (if any left)"
echo "============================"

eksctl delete nodegroup --cluster $CLUSTER --region $REGION --all || true


echo "============================"
echo "Deleting CloudFormation stacks"
echo "============================"

STACKS=$(aws cloudformation list-stacks --region $REGION \
  --query "StackSummaries[?contains(StackName, '$CLUSTER')].StackName" --output text)

for s in $STACKS; do
  echo "Deleting CFN stack: $s"
  aws cloudformation delete-stack --stack-name $s --region $REGION || true
done


echo "============================"
echo "Deleting Load Balancers (ALBs + NLBs)"
echo "============================"

ALBS=$(aws elbv2 describe-load-balancers --region $REGION \
  --query "LoadBalancers[?starts_with(LoadBalancerName, '$CLUSTER')].LoadBalancerArn" --output text)

for alb in $ALBS; do
  echo "Deleting ALB: $alb"
  aws elbv2 delete-load-balancer --load-balancer-arn $alb --region $REGION || true
done

# Classic ELB
CLBS=$(aws elb describe-load-balancers --region $REGION \
  --query "LoadBalancerDescriptions[?contains(LoadBalancerName, '$CLUSTER')].LoadBalancerName" --output text)

for elb in $CLBS; do
  echo "Deleting Classic ELB: $elb"
  aws elb delete-load-balancer --load-balancer-name $elb --region $REGION || true
done


echo "============================"
echo "Deleting Target Groups"
echo "============================"

TGS=$(aws elbv2 describe-target-groups --region $REGION \
  --query "TargetGroups[?starts_with(TargetGroupName, '$CLUSTER')].TargetGroupArn" --output text)

for tg in $TGS; do
  echo "Deleting target group: $tg"
  aws elbv2 delete-target-group --target-group-arn $tg --region $REGION || true
done


echo "============================"
echo "Deleting ENIs"
echo "============================"

ENIS=$(aws ec2 describe-network-interfaces --region $REGION \
  --query "NetworkInterfaces[?contains(Description, '$CLUSTER')].NetworkInterfaceId" --output text)

for eni in $ENIS; do
  echo "Deleting ENI: $eni"
  aws ec2 delete-network-interface --network-interface-id $eni --region $REGION || true
done


echo "============================"
echo "Deleting EBS volumes"
echo "============================"

VOLUMES=$(aws ec2 describe-volumes --region $REGION \
  --query "Volumes[?contains(Tags[?Key=='kubernetes.io/cluster/$CLUSTER'].Value, 'owned')].VolumeId" --output text)

for vol in $VOLUMES; do
  echo "Deleting volume: $vol"
  aws ec2 delete-volume --volume-id $vol --region $REGION || true
done


echo "============================"
echo "Deleting IAM roles related to IRSA"
echo "============================"

ROLES=$(aws iam list-roles --query "Roles[?contains(RoleName, '$CLUSTER')].RoleName" --output text)

for role in $ROLES; do
  echo "Deleting IAM role: $role"
  
  # detach policies first
  POLICIES=$(aws iam list-attached-role-policies --role-name $role \
    --query "AttachedPolicies[].PolicyArn" --output text)

  for pol in $POLICIES; do
    echo " Detaching policy: $pol"
    aws iam detach-role-policy --role-name $role --policy-arn $pol || true
  done

  aws iam delete-role --role-name $role || true
done


echo "============================"
echo "Deleting CloudWatch log groups"
echo "============================"

LOGS=$(aws logs describe-log-groups --region $REGION \
  --query "logGroups[?contains(logGroupName, '$CLUSTER')].logGroupName" --output text)

for log in $LOGS; do
  echo "Deleting log-group: $log"
  aws logs delete-log-group --log-group-name $log --region $REGION || true
done


echo "============================"
echo "Deleting ECR repositories"
echo "============================"

ECRS=$(aws ecr describe-repositories --region $REGION \
  --query "repositories[?contains(repositoryName, '$CLUSTER')].repositoryName" --output text)

for repo in $ECRS; do
  echo "Deleting ECR repo: $repo"
  aws ecr delete-repository --repository-name $repo --force --region $REGION || true
done


echo "============================"
echo "CLEANUP COMPLETE"
echo "Everything related to your EKS cluster has been terminated."
echo "============================"
