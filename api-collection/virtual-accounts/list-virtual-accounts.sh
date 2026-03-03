#!/usr/bin/env bash
# List Virtual Accounts – https://developer.fin.com/api-reference/virtual-accounts/list-virtual-accounts
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/customers/virtual-account?customer_id=CUSTOMER_UUID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
