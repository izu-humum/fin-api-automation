#!/usr/bin/env bash
# Attach Document To Associated Party – https://developer.fin.com/api-reference/customers/attach-document-to-associated-party
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/customers/associated-parties/individual/attach" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUSTOMER_UUID","associated_party_id":"ASSOCIATED_PARTY_UUID","documents":{"poi":"DOCUMENT_URI","poa":"DOCUMENT_URI"}}'
