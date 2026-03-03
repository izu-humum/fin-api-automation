#!/usr/bin/env bash
# List Generic Country Codes (ISO 3166-1 alpha-3) – https://developer.fin.com/api-reference/catalogue/list-generic-country-codes
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/countries?per_page=10&current_page=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
