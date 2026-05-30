$ErrorActionPreference = "Stop"

$requiredFiles = @(
  "iac/observability-platform.yaml",
  "lambda/grafana-bootstrap.py",
  "lambda/sso-assignment.py",
  "dashboards/cloudwatch.json",
  "dashboards/grafana.json",
  "alerts/contact-point.json",
  "alerts/notification-policy.json",
  "alerts/notification-template.json",
  "alerts/rule.json",
  ".github/workflows/deploy.yml"
)

foreach ($file in $requiredFiles) {
  if (-not (Test-Path $file)) {
    throw "Missing required file: $file"
  }
}

Get-ChildItem -Recurse -Filter *.json | ForEach-Object {
  try {
    Get-Content $_.FullName -Raw | ConvertFrom-Json | Out-Null
  } catch {
    throw "Invalid JSON in $($_.FullName): $($_.Exception.Message)"
  }
}

$template = Get-Content "iac/observability-platform.yaml" -Raw
foreach ($needle in @("Custom::GrafanaBootstrap", "Custom::GrafanaSsoAssignment", "AWS::Grafana::Workspace", "AWS::CloudWatch::Alarm")) {
  if ($template -notmatch [regex]::Escape($needle)) {
    throw "CloudFormation template does not contain $needle"
  }
}

$bootstrap = Get-Content "lambda/grafana-bootstrap.py" -Raw
foreach ($needle in @("update_workspace_configuration", "/api/plugins/", "/install", "create_workspace_service_account_token")) {
  if ($bootstrap -notmatch [regex]::Escape($needle)) {
    throw "Grafana bootstrap Lambda does not contain $needle"
  }
}

Write-Host "Validation passed."
