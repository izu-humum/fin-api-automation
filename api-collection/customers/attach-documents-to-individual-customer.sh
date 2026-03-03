#!/usr/bin/env bash
# Attach Documents to Individual Customer – https://developer.fin.com/api-reference/customers/attach-documents-to-individual-customer
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/individual/attach" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUSTOMER_UUID","documents":{"poi":"DOCUMENT_URI","poa":"DOCUMENT_URI"}}'
