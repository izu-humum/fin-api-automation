#!/usr/bin/env bash
# Execute Batch Transfer – https://developer.fin.com/api-reference/transactions/execute-batch-transfer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/batch/transactions/commit" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"beneficiary_id":"BENEFICIARY_UUID","source_currency":"USD","deduct_from":"PREFUNDED_BALANCE","source_amount":500,"remarks":"Batch item 1"}
  ]'
