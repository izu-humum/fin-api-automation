#!/usr/bin/env bash
# Create Business Customer – https://developer.fin.com/api-reference/customers/create-business-customer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/business" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "basic_info":{"business_name":"Acme Ltd","description":"Trading","entity_type":"PRIVATE_LIMITED","website":"https://acme.example.com","email":"contact@acme.example.com","incorporation_date":"2020-01-15","phone":"+1234567890","country_of_incorporation":"SGP","registration_number":"123","tax_id":"T123"},
    "financial_profile":{"monthly_volume_usd":10000,"purpose_id":1,"source_of_fund_id":1},
    "addresses":[{"type":"REGISTERED","street":"1 Main St","city":"Singapore","state":"SG-01","postal_code":"010001","country":"SGP"}],
    "associated_parties":[{"type":"INDIVIDUAL","email":"ubo@example.com","ownership_percent":100}]
  }'
