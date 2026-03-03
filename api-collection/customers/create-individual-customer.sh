#!/usr/bin/env bash
# Create Individual Customer – https://developer.fin.com/api-reference/customers/create-individual-customer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/individual" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "verification_type":"STANDARD",
    "basic_info":{"first_name":"John","last_name":"Doe","dob":"1990-01-15","email":"john.doe@example.com","phone":"+1234567890","country_of_residence":"USA","nationality":"USA","tin":"123-45-6789"},
    "address":{"street":"123 Main St","city":"New York","state":"US-NY","postal_code":"10001","country":"USA"},
    "financial_profile":{"occupation_id":1,"source_of_fund_id":1,"purpose_id":1,"monthly_volume_usd":5000}
  }'
