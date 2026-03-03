#!/usr/bin/env bash
# Fetch Virtual Account Transactions – https://developer.fin.com/api-reference/virtual-accounts/fetch-virtual-account-transactions
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/virtual-account/VIRTUAL_ACCOUNT_UUID/transactions?page=1&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
