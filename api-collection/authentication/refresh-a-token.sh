#!/usr/bin/env bash
# Refresh a Token – https://developer.fin.com/api-reference/authentication/refresh-a-token
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/oauth/refresh-token" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
