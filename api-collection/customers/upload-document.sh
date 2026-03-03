#!/usr/bin/env bash
# Upload Document – https://developer.fin.com/api-reference/customers/upload-document
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "poi=@/path/to/poi.pdf" \
  -F "poa=@/path/to/poa.pdf"
