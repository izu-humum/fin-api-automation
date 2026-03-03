#!/usr/bin/env bash
# Settle a Transfer – https://developer.fin.com/api-reference/transactions/settle-a-transfer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/transactions/transfer-payout/settle" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transfer_id":"TRANSFER_UUID"}'
