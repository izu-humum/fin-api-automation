#!/usr/bin/env bash
# Transaction Details – https://developer.fin.com/api-reference/transactions/transaction-details
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/beneficiaries/BENEFICIARY_UUID/transactions/TRANSACTION_UUID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
