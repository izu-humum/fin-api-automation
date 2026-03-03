#!/usr/bin/env bash
# Update Beneficiary Active Status – https://developer.fin.com/api-reference/beneficiaries/update-beneficiary-active-status
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X PATCH "${BASE_URL}/v1/beneficiaries" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"beneficiary_id":"BENEFICIARY_UUID","active":true}'
