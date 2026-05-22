AWS Observability Framework: Managed Grafana & CloudWatch
This repository provides a production-ready, IaC-driven observability stack. It consolidates AWS CloudWatch metrics and Managed Grafana dashboards into a single, automated deployment pipeline.

Key Features
AWS Managed Grafana: Automated workspace with AWS SSO integration.

Custom Plugin Management: Uses a CloudFormation Custom Resource and Lambda to automate plugin installation (grafana-piechart-panel, etc.).

Dashboard-as-Code: Custom CloudWatch dashboards defined directly in IaC.

Fully Automated CI/CD: Automated deployment via GitHub Actions.

Scalable Foundation: Built to support OpenTelemetry (OTEL) for multi-cloud monitoring.

Deployment
Setup: Ensure AWS credentials are saved in your GitHub Secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY).

Deploy: Push any change to the main branch to trigger the pipeline.

Monitor: Check deployment status via the AWS CloudFormation Console.
