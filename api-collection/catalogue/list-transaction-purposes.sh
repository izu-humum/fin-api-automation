#!/usr/bin/env bash
# List Transaction Purposes – https://developer.fin.com/api-reference/catalogue/list-transaction-purposes
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/transaction-purposes?type=INDIVIDUAL&per_page=10&current_page=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
