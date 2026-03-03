#!/usr/bin/env bash
# Get Customer Details – https://developer.fin.com/api-reference/customers/get-customer-details
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/customers/CUSTOMER_UUID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
