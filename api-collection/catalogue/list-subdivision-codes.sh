#!/usr/bin/env bash
# List Subdivision Codes (ISO 3166-1 alpha-2) – https://developer.fin.com/api-reference/catalogue/list-subdivision-codes
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/countries/USA/subdivisions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
