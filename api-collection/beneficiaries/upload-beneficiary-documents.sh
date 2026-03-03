#!/usr/bin/env bash
# Upload Beneficiary Documents – https://developer.fin.com/api-reference/beneficiaries/upload-beneficiary-documents
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/beneficiaries/BENEFICIARY_UUID/documents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf"
