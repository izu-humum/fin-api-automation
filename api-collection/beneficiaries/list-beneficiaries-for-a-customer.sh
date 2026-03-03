#!/usr/bin/env bash
# List Beneficiaries For a Customer – https://developer.fin.com/api-reference/beneficiaries/list-beneficiaries-for-a-customer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/customers/CUSTOMER_UUID/beneficiaries" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
