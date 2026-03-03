#!/usr/bin/env bash
# List Beneficiary Transactions – https://developer.fin.com/api-reference/transactions/list-beneficiary-transactions
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/beneficiaries/BENEFICIARY_UUID/transactions?page=1&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
