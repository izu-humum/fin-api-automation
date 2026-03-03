#!/usr/bin/env bash
# Fetch Prefunded Balance – https://developer.fin.com/api-reference/balances/fetch-prefunded-balance
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/wallet/balances" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
