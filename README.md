# AWS Observability Framework

Automated observability stack using AWS Managed Grafana, CloudWatch, and Infrastructure-as-Code (IaC).

## Architecture Highlights
- **Infrastructure:** Provisioned via CloudFormation, including custom resources for plugin management.
- **Data Consolidation:** Centralized observability via Amazon CloudWatch integrated into Grafana.
- **Automation:** End-to-end CI/CD using GitHub Actions for both infrastructure and dashboard-as-code deployment.
- **Standards:** Utilizes open-standard query patterns for business-driven monitoring.

## Key Features
1. **Managed Grafana:** Integrated with AWS IAM Identity Center for SSO.
2. **Automated Plugins:** Custom Lambda-backed CloudFormation resource for seamless plugin installation.
3. **Dashboard-as-Code:** Dashboards are maintained as JSON, automatically synchronized to the workspace via CI/CD.
4. **Scalable Monitoring:** Built to support OpenTelemetry and business-specific metrics.

## CI/CD Pipeline
The pipeline handles the lifecycle of the observability configuration:
- Triggers on `push` to `main`.
- Automates Data Source registration (`AMAZON_CLOUDWATCH`).
- Syncs dashboard definitions using the AWS CLI `put-dashboard` API.

---
*Built for scalable, automated, and multi-cloud ready observability.*
