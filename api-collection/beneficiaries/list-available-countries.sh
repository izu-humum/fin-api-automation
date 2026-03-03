#!/usr/bin/env bash
# List Available Countries – https://developer.fin.com/api-reference/beneficiaries/list-available-countries
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/beneficiaries/countries" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
