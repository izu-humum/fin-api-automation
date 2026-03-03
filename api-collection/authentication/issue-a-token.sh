#!/usr/bin/env bash
# Issue a Token – https://developer.fin.com/api-reference/authentication/issue-a-token
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v1/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
