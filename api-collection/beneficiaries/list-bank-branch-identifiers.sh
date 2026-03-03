#!/usr/bin/env bash
# List Bank Branch Identifiers – https://developer.fin.com/api-reference/beneficiaries/list-bank-branch-identifiers
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X GET "${BASE_URL}/v1/beneficiaries/methods/1472/branches" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
