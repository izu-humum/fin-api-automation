#!/usr/bin/env bash
# Fetch Prefunded Balance – https://developer.fin.com/api-reference/balances/fetch-prefunded-balance
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

if [ -z "$FIN_CLIENT_ID" ] || [ -z "$FIN_CLIENT_SECRET" ]; then
  echo "Set FIN_CLIENT_ID and FIN_CLIENT_SECRET (e.g. via .env) before running this script." >&2
  exit 1
fi

# 1) Obtain an access token using client credentials
ACCESS_TOKEN="$(
  curl -s -X POST "${BASE_URL}/v1/oauth/token" \
    -H "Content-Type: application/json" \
    -d "{\"client_id\":\"${FIN_CLIENT_ID}\",\"client_secret\":\"${FIN_CLIENT_SECRET}\"}" \
  | jq -r '.data.access_token // .access_token'
)"

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
  echo "Failed to obtain access token from /v1/oauth/token" >&2
  exit 1
fi

echo "Using access token (truncated): ${ACCESS_TOKEN:0:16}..."

# 2) Call Fetch Prefunded Balance with the bearer token
curl -s -X GET "${BASE_URL}/v1/wallet/balances" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
