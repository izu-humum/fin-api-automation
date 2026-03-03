#!/usr/bin/env bash
# List Transactions for Beneficiary – https://developer.fin.com/api-reference/transactions/list-transactions-for-beneficiary
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/beneficiaries/BENEFICIARY_UUID?per_page=10&current_page=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
