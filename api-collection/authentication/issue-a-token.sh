#!/usr/bin/env bash
# Issue a Token – https://developer.fin.com/api-reference/authentication/issue-a-token
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

if [ -z "$FIN_CLIENT_ID" ] || [ -z "$FIN_CLIENT_SECRET" ]; then
  echo "Set FIN_CLIENT_ID and FIN_CLIENT_SECRET (e.g. via .env) before running this script." >&2
  exit 1
fi

RAW_JSON="$(
  curl -s -X POST "${BASE_URL}/v1/oauth/token" \
    -H "Content-Type: application/json" \
    -d "{\"client_id\":\"${FIN_CLIENT_ID}\",\"client_secret\":\"${FIN_CLIENT_SECRET}\"}"
)"

echo "Raw token response:"
echo "$RAW_JSON"

ACCESS_TOKEN="$(printf '%s' "$RAW_JSON" | jq -r '.data.access_token // .access_token')"

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
  echo "Failed to extract access_token from response." >&2
  exit 1
fi

echo ""
echo "Access token:"
echo "$ACCESS_TOKEN"
