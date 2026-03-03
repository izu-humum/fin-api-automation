#!/usr/bin/env bash
# Fetch Exchange Rates – https://developer.fin.com/api-reference/fees-&-fx-rates/fetch-exchange-rates
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/fx-rate?currency_code=BDT" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
