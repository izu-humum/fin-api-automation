#!/usr/bin/env bash
# Attach Documents to Business Customer – https://developer.fin.com/api-reference/customers/attach-documents-to-business-customer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/business/attach" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUSTOMER_UUID","documents":{"ownership_structure":"DOCUMENT_URI","company_details":"DOCUMENT_URI","legal_presence":"DOCUMENT_URI"}}'
