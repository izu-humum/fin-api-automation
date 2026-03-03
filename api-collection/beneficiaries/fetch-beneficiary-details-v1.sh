#!/usr/bin/env bash
# Fetch Beneficiary Details v1 – https://developer.fin.com/api-reference/beneficiaries/fetch-beneficiary-details-v1
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/beneficiaries/details?customer_id=CUSTOMER_UUID&beneficiary_id=BENEFICIARY_UUID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
