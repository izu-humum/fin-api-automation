#!/usr/bin/env bash
# Calculate Exchange Rates – https://developer.fin.com/api-reference/fees-&-fx-rates/calculate-exchange-rates
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/fee-calculation" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_currency":"USD","source_amount":10000,"destination_currency":"CAD"}'
