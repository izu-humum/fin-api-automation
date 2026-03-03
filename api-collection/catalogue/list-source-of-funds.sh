#!/usr/bin/env bash
# List Source of Funds – https://developer.fin.com/api-reference/catalogue/list-source-of-funds
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/source-of-funds?type=INDIVIDUAL&per_page=10&current_page=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
