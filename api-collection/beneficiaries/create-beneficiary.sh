#!/usr/bin/env bash
# Create Beneficiary – https://developer.fin.com/api-reference/beneficiaries/create-beneficiary
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v2/beneficiaries" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id":"CUSTOMER_UUID",
    "country":"USA",
    "currency":"USD",
    "account_holder":{"type":"INDIVIDUAL","first_name":"John","last_name":"Doe","email":"john.doe@example.com","phone":"+1234567890"},
    "account_holder_address":{"street_line_1":"456 Main Street","city":"Brooklyn","state":"US-NY","postcode":"11201","country":"USA"},
    "receiver_meta_data":{"transaction_purpose_id":1,"occupation_id":1,"relationship":"FAMILY_MEMBER","nationality":"USA"},
    "developer_fee":{"fixed":1.25,"percentage":0.45},
    "deposit_instruction":{"currency":"USDC","rail":"POLYGON"},
    "refund_instruction":{"wallet_address":"0x...","currency":"USDC","rail":"POLYGON"},
    "bank_account":{"scheme":"LOCAL","number":"12345678"},
    "bank_routing":[{"scheme":"BANK_IDENTIFIER","number":"021000021"}],
    "bank_address":{"street_line_1":"","city":"","state":"","postcode":"","country":"USA"}
  }'
