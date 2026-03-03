# Fin.com API Collection

This repo contains **curl scripts** for the [Fin.com Orchestration API](https://developer.fin.com), grouped by category under **`api-collection/`**. Each script calls one API endpoint.

**Full documentation index:** https://developer.fin.com/llms.txt  
**OpenAPI spec:** https://developer.fin.com/api-reference/spec/openapi.yaml

---

## Layout

All curl scripts live under **`api-collection/`**, one file per endpoint:

| Category | Folder | Endpoints |
|----------|--------|-----------|
| **Authentication** | `api-collection/authentication/` | issue-a-token, refresh-a-token |
| **Balances** | `api-collection/balances/` | fetch-prefunded-balance |
| **Beneficiaries** | `api-collection/beneficiaries/` | create-beneficiary, fetch-beneficiary-details-v1, fetch-beneficiary-details-v2, list-available-countries, list-bank-branch-identifiers, list-bank-identifiers, list-beneficiaries-for-a-customer, update-beneficiary-active-status, upload-beneficiary-documents |
| **Catalogue** | `api-collection/catalogue/` | list-account-purposes, list-generic-country-codes, list-industries, list-occupations, list-source-of-funds, list-subdivision-codes, list-transaction-purposes |
| **Customers** | `api-collection/customers/` | attach-document-to-associated-party, attach-documents-to-business-customer, attach-documents-to-individual-customer, create-business-customer, create-individual-customer, enable-usd-features, get-customer-details, list-customers, upload-document |
| **Fees & FX Rates** | `api-collection/fees-and-fx-rates/` | calculate-exchange-rates, fetch-exchange-rates |
| **Transactions** | `api-collection/transactions/` | create-a-transfer, execute-batch-transfer, fetch-batch-details, fetch-transaction-details, list-beneficiary-transactions, list-transactions-for-beneficiary, settle-a-transfer, transaction-details |
| **Virtual Accounts** | `api-collection/virtual-accounts/` | create-virtual-account, fetch-virtual-account-transactions, list-virtual-accounts, update-virtual-account |
| **Webhooks** | `api-collection/webhooks/` | batch-transaction-item-status, beneficiary-created, beneficiary-liquidation-deposit, beneficiary-status, customer-created, customer-status, transaction-status, virtual-account-created, virtual-account-status |

---

## Usage

1. **Get a token** (no auth header):
   ```bash
   ./api-collection/authentication/issue-a-token.sh
   ```
   Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` in the script (or set env vars and adjust the script to use them).

2. **Call any other endpoint** (Bearer token required): set `YOUR_ACCESS_TOKEN` in the script or export it and use `"Authorization: Bearer $ACCESS_TOKEN"` in the script.

3. **Override base URL** (e.g. production):
   ```bash
   BASE_URL="https://api.fin.com" ./api-collection/balances/fetch-prefunded-balance.sh
   ```

Each `.sh` file has a comment with the official doc link. Replace placeholders (e.g. `CUSTOMER_UUID`, `BENEFICIARY_UUID`, file paths) before running.

**Webhooks:** The files in `api-collection/webhooks/` describe events that Fin.com sends to your endpoint (no curl to run). Use them as reference and see [Verifying Webhooks](https://developer.fin.com/guides/webhooks/verifying-webhooks) to validate signatures.

---

## Python automation (Individual Customer flow)

To run the full API collection for an individual customer with logging:

```bash
pip install -r requirements.txt
./run_individual_customer_flow.py
```

Optional: copy `.env.example` to `.env` and set `FIN_CLIENT_ID`, `FIN_CLIENT_SECRET`, `FIN_CUSTOMER_ID`, etc. The script uses defaults for the configured customer (Humam Izu, `humam.izu@gmail.com`, customer ID `c7620e2d-e2a0-47c7-86a9-40966599d456`). Logs are printed to the terminal at DEBUG level for each endpoint.

---

*Collected from [developer.fin.com](https://developer.fin.com). For the latest specs and examples, use the links in each script or the official portal.*
