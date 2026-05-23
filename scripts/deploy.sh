#!/bin/bash
echo "Validating Template..."
aws cloudformation validate-template --template-body file://cfn/main-stack.yaml

echo "Deploying Stack..."
aws cloudformation deploy \
  --template-file cfn/main-stack.yaml \
  --stack-name Grafana-Stack \
  --capabilities CAPABILITY_IAM
