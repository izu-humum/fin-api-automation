#!/usr/bin/env bash
# Fetch Batch Details – https://developer.fin.com/api-reference/transactions/fetch-batch-details
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/batch/transactions/commit/BATCH_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
