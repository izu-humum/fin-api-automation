#!/usr/bin/env bash
# Create Beneficiary – https://developer.fin.com/api-reference/beneficiaries/create-beneficiary
BASE_URL="${BASE_URL:-https://sandbox.api.fin.com}"

curl -s -X POST "${BASE_URL}/v2/beneficiaries" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUSTOMER_UUID",
    "country": "USA",
    "currency": "USD",
    "account_holder": {
      "type": "INDIVIDUAL",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+12025551234"
    },
    "account_holder_address": {
      "street_line_1": "456 Main Street",
      "street_line_2": "Apt 5B",
      "city": "Brooklyn",
      "state": "US-NY",
      "postcode": "11201",
      "country": "USA"
    },
    "receiver_meta_data": {
      "transaction_purpose_id": 1,
      "transaction_purpose_remarks": "Monthly salary payment",
      "occupation_id": 5,
      "occupation_remarks": "Software Engineer",
      "relationship": "EMPLOYEE",
      "relationship_remarks": "Long-term contractor",
      "nationality": "USA",
      "govt_id_number": "JG1121316A",
      "govt_id_issue_date": "2024-12-30",
      "govt_id_expire_date": "2027-12-30"
    },
    "developer_fee": {
      "fixed": 5,
      "percentage": 2.5
    },
    "deposit_instruction": {
      "currency": "USDC",
      "rail": "POLYGON"
    },
    "refund_instruction": {
      "wallet_address": "0x1b577931c1cc2765024bfbafad97bce14ff2e87f",
      "currency": "USDC",
      "rail": "POLYGON"
    },
    "bank_account": {
      "bank_name": "Chase Bank",
      "number": "1234567890",
      "scheme": "LOCAL",
      "type": "CHECKING"
    },
    "bank_routing": [
      {
        "scheme": "ACH",
        "number": "021000021"
      },
      {
        "scheme": "BANK_IDENTIFIER",
        "number": "1"
      }
    ],
    "bank_address": {
      "street_line_1": "123 Bank Street",
      "street_line_2": "Suite 100",
      "city": "New York",
      "state": "US-NY",
      "postcode": "10001",
      "country": "USA"
    },
    "settlement_config": {
      "auto_settlement": true
    }
  }'
