#!/usr/bin/env bash
set -euo pipefail

: "${GRAFANA_URL:?GRAFANA_URL is required}"
: "${GRAFANA_TOKEN:?GRAFANA_TOKEN is required}"
: "${SNS_TOPIC_ARN:?SNS_TOPIC_ARN is required}"

api() {
  local method="$1"
  local path="$2"
  local body="${3:-}"

  if [[ -n "${body}" ]]; then
    curl --fail-with-body --silent --show-error \
      --request "${method}" \
      --url "${GRAFANA_URL}${path}" \
      --header "Authorization: Bearer ${GRAFANA_TOKEN}" \
      --header "Content-Type: application/json" \
      --data @"${body}"
  else
    curl --fail-with-body --silent --show-error \
      --request "${method}" \
      --url "${GRAFANA_URL}${path}" \
      --header "Authorization: Bearer ${GRAFANA_TOKEN}" \
      --header "Content-Type: application/json"
  fi
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

folder_payload="${tmp_dir}/folder.json"
jq -n '{uid:"business-observability", title:"Business Observability"}' > "${folder_payload}"
api POST /api/folders "${folder_payload}" || true

datasource_payload="${tmp_dir}/cloudwatch-datasource.json"
jq -n \
  --arg region "${AWS_REGION:-us-east-1}" \
  '{
    name: "CloudWatch",
    uid: "cloudwatch",
    type: "cloudwatch",
    access: "proxy",
    isDefault: true,
    jsonData: {
      authType: "grafana_assume_role",
      defaultRegion: $region
    }
  }' > "${datasource_payload}"
api POST /api/datasources "${datasource_payload}" || api PUT /api/datasources/uid/cloudwatch "${datasource_payload}"

dashboard_payload="${tmp_dir}/business-dashboard.json"
jq '{dashboard: ., folderUid: "business-observability", overwrite: true}' \
  dashboards/grafana.json > "${dashboard_payload}"
api POST /api/dashboards/db "${dashboard_payload}"

contact_payload="${tmp_dir}/sns-contact-point.json"
jq --arg topicArn "${SNS_TOPIC_ARN}" '.settings.topic = $topicArn' \
  alerts/contact-point.json > "${contact_payload}"
api PUT /api/v1/provisioning/contact-points/sns-business-alerts "${contact_payload}" \
  || api POST /api/v1/provisioning/contact-points "${contact_payload}"

template_payload="${tmp_dir}/notification-template.json"
jq '.' alerts/notification-template.json > "${template_payload}"
api PUT /api/v1/provisioning/templates/business-impact-template "${template_payload}" \
  || api POST /api/v1/provisioning/templates "${template_payload}"

policy_payload="${tmp_dir}/notification-policy.json"
jq '.' alerts/notification-policy.json > "${policy_payload}"
api PUT /api/v1/provisioning/policies "${policy_payload}"

rule_payload="${tmp_dir}/checkout-error-rate-rule.json"
jq '.' alerts/rule.json > "${rule_payload}"
api PUT /api/v1/provisioning/alert-rules/business-checkout-error-rate "${rule_payload}" \
  || api POST /api/v1/provisioning/alert-rules "${rule_payload}"

echo "Grafana dashboards, contact points, templates, and alert rules deployed."
