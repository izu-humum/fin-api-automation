#!/usr/bin/env bash
# Update Virtual Account – https://developer.fin.com/api-reference/virtual-accounts/update-virtual-account
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X PUT "${BASE_URL}/v1/customers/virtual-account" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"VIRTUAL_ACCOUNT_UUID","customer_id":"CUSTOMER_UUID","developer_fee_percentage":1.25,"destination_wallet_address":"0x7f1568190e318da16a9ef5a46cba19d5b97d9b29"}'
