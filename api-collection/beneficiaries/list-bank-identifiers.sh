#!/usr/bin/env bash
# List Bank Identifiers – https://developer.fin.com/api-reference/beneficiaries/list-bank-identifiers
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/beneficiaries/methods?country_code=BGD&method=BANK" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
