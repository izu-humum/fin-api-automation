#!/usr/bin/env bash
# Fetch Beneficiary Details v2 – https://developer.fin.com/api-reference/beneficiaries/fetch-beneficiary-details-v2
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v2/beneficiaries/details?customer_id=CUSTOMER_UUID&beneficiary_id=BENEFICIARY_UUID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
