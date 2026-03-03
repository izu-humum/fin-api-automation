#!/usr/bin/env bash
# Create a Transfer – https://developer.fin.com/api-reference/transactions/create-a-transfer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/transactions/transfer-payout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"beneficiary_id":"BENEFICIARY_UUID","reference_id":"REF-12345","amount":10000,"remarks":"Monthly payment"}'
