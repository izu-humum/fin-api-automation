#!/usr/bin/env bash
# Enable USD Features – https://developer.fin.com/api-reference/customers/enable-usd-features
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/enable-preference" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUSTOMER_UUID"}'
