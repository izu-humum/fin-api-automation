#!/usr/bin/env bash
# Fetch Transaction Details – https://developer.fin.com/api-reference/transactions/fetch-transaction-details
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/transactions/TRANSACTION_UUID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
