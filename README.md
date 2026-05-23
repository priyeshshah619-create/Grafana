This Github prject strictly satisfies below 7 requirements with 3 conditions

IAC - Cloudformation

Service - AWS Managed Grafana,Cloudwatch

Account - All to be done in single Account

1. Create AWS managed grafana and install basic plugins via code(use cfn custom resources)

    a. sso integration

    b. install plugins 

2. Setup one observability in aws cloudwatch

3. Create a custom cloudwatch dashboard for collected metrics and create grafana alerts to send sns notification via notification templates

4. Dashboards/Alerts deployment to be automatic via github actions after the setup

5. Experience on Multi cloud observability and standards 

6. Application specific business driven monitoring and reporting (eg: how to collect data via OTEL or similar)

7. Experience in Data collection framework and consolidation which is key to Observability

Conditions:
A. Need to see plugin installation part. Please write cloudformation custom resource for the same.

B. Need to see the lambda code for the plugin installation .Need to be done end to via CI/CD not just write code.-   

C. Need to see dashboard as a code.

We need to create real world example.
As you can see I have created users in IAM & IAM identity center.
If possible I want to do all remaining things with IAC
