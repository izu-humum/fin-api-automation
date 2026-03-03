#!/usr/bin/env bash
# Create Virtual Account – https://developer.fin.com/api-reference/virtual-accounts/create-virtual-account
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/virtual-account" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUSTOMER_UUID","destination_currency":"USDC","destination_chain":"POLYGON","source_rail":"ACH","source_currency":"USD","destination_wallet_address":"0x7f1568190e318da16a9ef5a46cba19d5b97d9b29","developer_fee_percentage":1.5}'
