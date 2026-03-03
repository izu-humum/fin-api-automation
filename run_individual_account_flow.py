#!/usr/bin/env python3
"""
Fin.com API – Full Individual Account flow automation.
Runs the API collection for an individual customer with logging per endpoint.

Usage:
  export FIN_CLIENT_ID="your_client_id"
  export FIN_CLIENT_SECRET="your_client_secret"
  export FIN_CUSTOMER_ID="your_customer_uuid"   # optional, defaults below
  ./run_individual_account_flow.py

Or use a .env file (see .env.example).
"""

import json
import logging
import os
import sys
from typing import Any, Optional

try:
    import requests
except ImportError:
    print("Install dependencies: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# -----------------------------------------------------------------------------
# Config (override via env)
# -----------------------------------------------------------------------------
BASE_URL = os.environ.get("FIN_BASE_URL", "https://sandbox.api.fin.com")
CLIENT_ID = os.environ.get("FIN_CLIENT_ID", "jttPLRHlUyVMGdsWfXql")
CLIENT_SECRET = os.environ.get("FIN_CLIENT_SECRET", "xwpyipC3QAhKP6bAtZCtsHv0jSkg4QiM6z9BwPkGZ7I4cCiMMssG6eSR1Rv6EJJdTeVHoodzj9Ne7su6KuN23Nwn9weSlaBotUyJ")
CUSTOMER_ID = os.environ.get("FIN_CUSTOMER_ID", "0c237aaa-4c6e-411f-aca6-785dacbe5545")
CUSTOMER_NAME = os.environ.get("FIN_CUSTOMER_NAME", "Izu Humam")
CUSTOMER_EMAIL = os.environ.get("FIN_CUSTOMER_EMAIL", "humam.izu@gmail.com")
EXISTING_BENEFICIARY_ID = os.environ.get("FIN_BENEFICIARY_ID", "")

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)

# Collected per-endpoint results for end-of-run summary
API_RESULTS: list[dict[str, Any]] = []

def log_endpoint(name: str, method: str, path: str, response: requests.Response, body: Optional[Any] = None) -> None:
    """Log request and response for an endpoint."""
    log.info("=== Endpoint: %s ===", name)
    log.debug("Request: %s %s%s", method, BASE_URL, path)
    if body is not None:
        safe_body = body
        if isinstance(body, dict):
            # Redact any sensitive fields before logging
            safe_body = dict(body)
            if "client_secret" in safe_body:
                safe_body["client_secret"] = "***REDACTED***"
        log.debug("Request body: %s", json.dumps(safe_body, indent=2) if isinstance(safe_body, dict) else safe_body)
    log.info("Response status: %s", response.status_code)
    try:
        rj = response.json()
        log.debug("Response body: %s", json.dumps(rj, indent=2))
    except Exception:
        log.debug("Response text: %s", response.text[:500] if response.text else "(empty)")
    log.info("---")


def api_call(
    name: str,
    method: str,
    path: str,
    session: requests.Session,
    json_body: Optional[dict] = None,
    params: Optional[dict] = None,
    **kwargs: Any,
) -> requests.Response:
    """Make request and log."""
    url = BASE_URL.rstrip("/") + path
    # Big, visible banner for the API name in terminal logs
    banner = f"[ {name} ]"
    log.info("")
    log.info("############################################################")
    log.info("%s", banner.upper())
    log.info("Method: %s  Path: %s", method, path)
    log.info("############################################################")
    if method == "GET":
        r = session.get(url, params=params, **kwargs)
    elif method == "POST":
        r = session.post(url, json=json_body, **kwargs)
    elif method == "PATCH":
        r = session.patch(url, json=json_body, **kwargs)
    elif method == "PUT":
        r = session.put(url, json=json_body, **kwargs)
    else:
        raise ValueError("Unsupported method: %s", method)
    API_RESULTS.append({"name": name, "method": method, "path": path, "status": r.status_code})
    log_endpoint(name, method, path, r, json_body)
    return r


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split(None, 1)
    if len(parts) == 0:
        return "Izu", "Humam"
    if len(parts) == 1:
        return parts[0], "Humam"
    return parts[0], parts[1]


def log_422_errors(context: str, response: requests.Response) -> None:
    """When a request fails with 422, log a compact human-readable cause."""
    if response.status_code != 422:
        return
    try:
        body = response.json()
    except Exception:
        log.warning(
            "%s failed with 422; non-JSON response body: %s",
            context,
            (response.text or "")[:200],
        )
        return

    message = body.get("message") or "Validation failed"
    log.warning("%s failed with 422. Message: %s", context, message)

    errors = body.get("errors") or []
    for err in errors:
        if isinstance(err, dict):
            parts = [f"{k}={v}" for k, v in err.items()]
            log.warning("%s 422 detail: %s", context, "; ".join(parts))
        else:
            log.warning("%s 422 detail: %s", context, err)


def main() -> int:
    if not CLIENT_ID or not CLIENT_SECRET:
        log.error("Set FIN_CLIENT_ID and FIN_CLIENT_SECRET (env or .env)")
        return 1

    session = requests.Session()
    session.headers["Content-Type"] = "application/json"

    customer_approved = False

    # -------------------------------------------------------------------------
    # 1. Authentication – Issue a Token
    # -------------------------------------------------------------------------
    log.info(">>> 1. Authentication – Issue a Token")
    r = api_call(
        "Issue a Token",
        "POST",
        "/v1/oauth/token",
        session,
        json_body={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
    )
    if r.status_code != 200:
        log.error("Failed to get token. Aborting.")
        return 1
    data = r.json()
    # API returns { "data": { "access_token": "...", ... } }
    payload = data.get("data") or data
    access_token = payload.get("access_token")
    if not access_token:
        log.error("No access_token in response.")
        return 1
    session.headers["Authorization"] = f"Bearer {access_token}"
    log.info("Token obtained successfully.")

    # -------------------------------------------------------------------------
    # 2. Balances – Fetch Prefunded Balance
    # -------------------------------------------------------------------------
    log.info(">>> 2. Balances – Fetch Prefunded Balance")
    r_bal = api_call("Fetch Prefunded Balance", "GET", "/v1/wallet/balances", session)
    log_422_errors("Fetch Prefunded Balance", r_bal)

    # -------------------------------------------------------------------------
    # 3. Customers – Get Customer Details
    # -------------------------------------------------------------------------
    log.info(">>> 3. Customers – Get Customer Details")
    r_cust = api_call("Get Customer Details", "GET", f"/v1/customers/{CUSTOMER_ID}", session)
    if r_cust.status_code == 200:
        try:
            cust_payload = r_cust.json().get("data") or r_cust.json()
            status = (cust_payload.get("customer_status") or "").upper()
            if status == "APPROVED":
                customer_approved = True
                log.info("Customer %s is in APPROVED status – off-ramp flow enabled.", CUSTOMER_ID)
            else:
                log.warning(
                    "Customer %s is not APPROVED (status=%s). "
                    "Will skip beneficiary creation and off-ramp transfer flow.",
                    CUSTOMER_ID,
                    status or "UNKNOWN",
                )
        except Exception as exc:
            log.warning(
                "Could not determine customer_status from Get Customer Details response: %s",
                exc,
            )

    # -------------------------------------------------------------------------
    # 4. Customers – List Customers (INDIVIDUAL)
    # -------------------------------------------------------------------------
    log.info(">>> 4. Customers – List Customers")
    api_call(
        "List Customers",
        "GET",
        "/v1/customers",
        session,
        params={"type": "INDIVIDUAL", "per_page": "10", "current_page": "1"},
    )

    # -------------------------------------------------------------------------
    # 5. Catalogue – List Account Purposes
    # -------------------------------------------------------------------------
    log.info(">>> 5. Catalogue – List Account Purposes")
    api_call(
        "List Account Purposes",
        "GET",
        "/v1/purposes",
        session,
        params={"type": "INDIVIDUAL", "per_page": "10", "current_page": "1"},
    )

    # -------------------------------------------------------------------------
    # 6. Catalogue – List Generic Country Codes
    # -------------------------------------------------------------------------
    log.info(">>> 6. Catalogue – List Generic Country Codes")
    api_call(
        "List Generic Country Codes",
        "GET",
        "/v1/countries",
        session,
        params={"per_page": "10", "current_page": "1"},
    )

    # -------------------------------------------------------------------------
    # 7. Catalogue – List Industries
    # -------------------------------------------------------------------------
    log.info(">>> 7. Catalogue – List Industries")
    api_call(
        "List Industries",
        "GET",
        "/v1/industries",
        session,
        params={"per_page": "10", "current_page": "1"},
    )

    # -------------------------------------------------------------------------
    # 8. Catalogue – List Occupations
    # -------------------------------------------------------------------------
    log.info(">>> 8. Catalogue – List Occupations")
    api_call(
        "List Occupations",
        "GET",
        "/v1/occupations",
        session,
        params={"per_page": "10", "current_page": "1"},
    )

    # -------------------------------------------------------------------------
    # 9. Catalogue – List Source of Funds
    # -------------------------------------------------------------------------
    log.info(">>> 9. Catalogue – List Source of Funds")
    api_call(
        "List Source of Funds",
        "GET",
        "/v1/source-of-funds",
        session,
        params={"type": "INDIVIDUAL", "per_page": "10", "current_page": "1"},
    )

    # -------------------------------------------------------------------------
    # 10. Catalogue – List Subdivision Codes
    # -------------------------------------------------------------------------
    log.info(">>> 10. Catalogue – List Subdivision Codes")
    api_call("List Subdivision Codes", "GET", "/v1/countries/USA/subdivisions", session)

    # -------------------------------------------------------------------------
    # 11. Catalogue – List Transaction Purposes
    # -------------------------------------------------------------------------
    log.info(">>> 11. Catalogue – List Transaction Purposes")
    api_call(
        "List Transaction Purposes",
        "GET",
        "/v1/transaction-purposes",
        session,
        params={"type": "INDIVIDUAL", "per_page": "10", "current_page": "1"},
    )

    # -------------------------------------------------------------------------
    # 12. Beneficiaries – List Available Countries
    # -------------------------------------------------------------------------
    log.info(">>> 12. Beneficiaries – List Available Countries")
    api_call("List Available Countries", "GET", "/v1/beneficiaries/countries", session)

    # -------------------------------------------------------------------------
    # 13. Beneficiaries – List Bank Identifiers
    # -------------------------------------------------------------------------
    log.info(">>> 13. Beneficiaries – List Bank Identifiers")
    api_call(
        "List Bank Identifiers",
        "GET",
        "/v1/beneficiaries/methods",
        session,
        params={"country_code": "BGD", "method": "BANK"},
    )

    # -------------------------------------------------------------------------
    # 14. Beneficiaries – List Bank Branch Identifiers
    # -------------------------------------------------------------------------
    log.info(">>> 14. Beneficiaries – List Bank Branch Identifiers")
    api_call(
        "List Bank Branch Identifiers",
        "GET",
        "/v1/beneficiaries/methods/1472/branches",
        session,
    )

    # -------------------------------------------------------------------------
    # 15. Beneficiaries – List Beneficiaries For Customer
    # -------------------------------------------------------------------------
    log.info(">>> 15. Beneficiaries – List Beneficiaries For Customer")
    api_call(
        "List Beneficiaries For Customer",
        "GET",
        f"/v1/customers/{CUSTOMER_ID}/beneficiaries",
        session,
    )

    # -------------------------------------------------------------------------
    # 15a. Beneficiaries – Create dummy beneficiaries (for testing)
    # -------------------------------------------------------------------------
    if customer_approved:
        log.info(">>> 15a. Beneficiaries – Create dummy beneficiaries for customer")
        base_first, base_last = _split_name(CUSTOMER_NAME)
        dummy_account_numbers = ["123456780", "123456781"]
        for idx, acc_no in enumerate(dummy_account_numbers, start=1):
            # Use the actual first name (no suffix) to satisfy validation rules
            dummy_body = {
                "customer_id": CUSTOMER_ID,
                "country": "AUS",
                "currency": "AUD",
                "account_holder": {
                    "type": "INDIVIDUAL",
                    "first_name": base_first,
                    "last_name": base_last,
                    "email": CUSTOMER_EMAIL,
                    "phone": "+61412345678",
                },
                "account_holder_address": {
                    "street_line_1": "42 Wallaby Way",
                    "city": "Queensland",
                    "state": "AU-SA",
                    "postcode": "2000",
                    "country": "AUS",
                },
                "receiver_meta_data": {
                    "transaction_purpose_id": 1,
                    "transaction_purpose_remarks": "Send to Family & Friends",
                    "occupation_id": 504,
                    "occupation_remarks": "Software engineer",
                    "relationship": "FAMILY_MEMBER",
                    "relationship_remarks": "Family",
                    "nationality": "AUS",
                },
                "developer_fee": {"fixed": 1.25, "percentage": 0.45},
                "deposit_instruction": {
                    "currency": "USDC",
                    "rail": "POLYGON",
                    "liquidation_address": "0xc0470baa27e383a570226298f598fac0612f1143",
                },
                "refund_instruction": {
                    "wallet_address": "0x1b577931C1cC2765024bFbafad97bCe14FF2e87F",
                    "currency": "USDC",
                    "rail": "POLYGON",
                },
                "bank_account": {
                    "bank_name": "Commonwealth Bank of Australia",
                    "number": acc_no,
                    "scheme": "LOCAL",
                    "type": "CHECKING",
                },
                # For AUS + LOCAL, both BSB and BANK_IDENTIFIER are required
            "bank_routing": [
                {
                    "scheme": "BSB",
                    "number": "123456",
                },
                {
                    # For AUS, bank_identifier must be digits and cannot start with 0 (^[1-9]\\d*$)
                    "scheme": "BANK_IDENTIFIER",
                    "number": "2157391",
                },
            ],
                "bank_address": {
                    "street_line_1": "Ground Floor Tower 1, 201 Sussex Street",
                    "city": "Sydney",
                    "state": "AU-SA",
                    "postcode": "2000",
                    "country": "AUS",
                },
            }
            r_dummy = api_call(
                f"Create Dummy Beneficiary {idx}",
                "POST",
                "/v2/beneficiaries",
                session,
                json_body=dummy_body,
            )
            log_422_errors(f"Create Dummy Beneficiary {idx}", r_dummy)
    else:
        log.info(
            "Skipping creation of dummy beneficiaries because customer is not APPROVED."
        )

    # -------------------------------------------------------------------------
    # 16. Customers – Enable USD Features
    # -------------------------------------------------------------------------
    log.info(">>> 16. Customers – Enable USD Features")
    api_call(
        "Enable USD Features",
        "POST",
        "/v1/customers/enable-preference",
        session,
        json_body={"customer_id": CUSTOMER_ID},
    )

    # -------------------------------------------------------------------------
    # 17. Fees & FX – Fetch Exchange Rates
    # -------------------------------------------------------------------------
    log.info(">>> 17. Fees & FX – Fetch Exchange Rates")
    api_call(
        "Fetch Exchange Rates",
        "GET",
        "/v1/fx-rate",
        session,
        params={"currency_code": "BDT"},
    )

    # -------------------------------------------------------------------------
    # 18. Fees & FX – Calculate Exchange Rates
    # -------------------------------------------------------------------------
    log.info(">>> 18. Fees & FX – Calculate Exchange Rates")
    api_call(
        "Calculate Exchange Rates",
        "POST",
        "/v1/fee-calculation",
        session,
        json_body={
            "source_currency": "USD",
            "source_amount": 10000,
            "destination_currency": "CAD",
        },
    )

    # -------------------------------------------------------------------------
    # 19. Off-ramp flow – Create Beneficiary, Transfer, Settle, Inspect
    # -------------------------------------------------------------------------
    beneficiary_id: Optional[str] = None

    if not customer_approved:
        log.info(
            "Skipping off-ramp flow because customer is not in APPROVED status."
        )
    else:
        if EXISTING_BENEFICIARY_ID:
            log.info("Using existing beneficiary id from FIN_BENEFICIARY_ID = %s", EXISTING_BENEFICIARY_ID)
            beneficiary_id = EXISTING_BENEFICIARY_ID
        else:
            log.info(">>> 19.1 Beneficiaries – Create Beneficiary (off-ramp test)")
            first_name, last_name = _split_name(CUSTOMER_NAME)
            create_beneficiary_body = {
            "customer_id": CUSTOMER_ID,
            "country": "AUS",
            "currency": "AUD",
            "account_holder": {
                "type": "INDIVIDUAL",
                "first_name": first_name,
                "last_name": last_name,
                "email": CUSTOMER_EMAIL,
                "phone": "+61412345678",
            },
            "account_holder_address": {
                "street_line_1": "42 Wallaby Way",
                "city": "Queensland",
                "state": "AU-SA",
                "postcode": "2000",
                "country": "AUS",
            },
            "receiver_meta_data": {
                "transaction_purpose_id": 1,
                "transaction_purpose_remarks": "Send to Family & Friends",
                "occupation_id": 504,
                "occupation_remarks": "Software engineer",
                "relationship": "FAMILY_MEMBER",
                "relationship_remarks": "Family",
                "nationality": "AUS",
            },
            "developer_fee": {"fixed": 1.25, "percentage": 0.45},
            "deposit_instruction": {
                "currency": "USDC",
                "rail": "POLYGON",
                "liquidation_address": "0xc0470baa27e383a570226298f598fac0612f1143",
            },
            "refund_instruction": {
                "wallet_address": "0x1b577931C1cC2765024bFbafad97bCe14FF2e87F",
                "currency": "USDC",
                "rail": "POLYGON",
            },
            "bank_account": {
                "bank_name": "Commonwealth Bank of Australia",
                "number": "123456782",
                "scheme": "LOCAL",
                "type": "CHECKING",
            },
            # For AUS + LOCAL, both BSB and BANK_IDENTIFIER are required
            "bank_routing": [
                {
                    "scheme": "BSB",
                    "number": "123456",
                },
                {
                    # For AUS, bank_identifier must be digits and cannot start with 0 (^[1-9]\\d*$)
                    "scheme": "BANK_IDENTIFIER",
                    "number": "2157391",
                },
            ],
            "bank_address": {
                "street_line_1": "Ground Floor Tower 1, 201 Sussex Street",
                "city": "Sydney",
                "state": "AU-SA",
                "postcode": "2000",
                "country": "AUS",
            },
        }
            r_ben = api_call(
                "Create Beneficiary (Off-ramp Test)",
                "POST",
                "/v2/beneficiaries",
                session,
                json_body=create_beneficiary_body,
            )
            if r_ben.status_code == 200:
                try:
                    ben_data = r_ben.json().get("data") or r_ben.json()
                    beneficiary_id = ben_data.get("id") or ben_data.get("beneficiary_id")
                except Exception:
                    beneficiary_id = None
            else:
                log_422_errors("Create Beneficiary (Off-ramp Test)", r_ben)
                log.warning("Create Beneficiary failed with status %s; skipping transfer flow.", r_ben.status_code)

    if beneficiary_id and customer_approved:
        log.info("Using beneficiary_id=%s for off-ramp transfer flow.", beneficiary_id)

        # 19.2 – Fetch Beneficiary Details v2
        log.info(">>> 19.2 Beneficiaries – Fetch Beneficiary Details v2")
        api_call(
            "Fetch Beneficiary Details v2 (Off-ramp Test)",
            "GET",
            "/v2/beneficiaries/details",
            session,
            params={"customer_id": CUSTOMER_ID, "beneficiary_id": beneficiary_id},
        )

        # 19.3 – Create a Transfer
        log.info(">>> 19.3 Transactions – Create a Transfer")
        transfer_body = {
            "beneficiary_id": beneficiary_id,
            "reference_id": "OFFRAMP-TEST-REF-1",
            "amount": 500,
            "remarks": "Off-ramp test transfer from automation script",
        }
        r_transfer = api_call(
            "Create a Transfer (Off-ramp Test)",
            "POST",
            "/v1/transactions/transfer-payout",
            session,
            json_body=transfer_body,
        )
        transfer_id: Optional[str] = None
        if r_transfer.status_code == 200:
            try:
                t_data = r_transfer.json().get("data") or r_transfer.json()
                transfer_id = t_data.get("transfer_id")
            except Exception:
                transfer_id = None
        else:
            log.warning("Create Transfer failed with status %s; skipping settle + transaction detail.", r_transfer.status_code)

        # 19.4 – Settle a Transfer
        transaction_id: Optional[str] = None
        if transfer_id:
            log.info(">>> 19.4 Transactions – Settle a Transfer")
            r_settle = api_call(
                "Settle a Transfer (Off-ramp Test)",
                "POST",
                "/v1/transactions/transfer-payout/settle",
                session,
                json_body={"transfer_id": transfer_id},
            )
            if r_settle.status_code == 200:
                try:
                    s_data = r_settle.json().get("data") or r_settle.json()
                    transaction_id = s_data.get("transaction_id")
                except Exception:
                    transaction_id = None
        else:
            log.warning("No transfer_id; skipping settle + transaction detail.")

        # 19.5 – List Beneficiary Transactions
        log.info(">>> 19.5 Transactions – List Beneficiary Transactions")
        api_call(
            "List Beneficiary Transactions (Off-ramp Test)",
            "GET",
            f"/v1/beneficiaries/{beneficiary_id}/transactions",
            session,
            params={"page": 1, "limit": 10},
        )

        # 19.6 – Transaction Details (by beneficiary + transaction id) if available
        if transaction_id:
            log.info(">>> 19.6 Transactions – Transaction Details")
            api_call(
                "Transaction Details (Off-ramp Test)",
                "GET",
                f"/v1/beneficiaries/{beneficiary_id}/transactions/{transaction_id}",
                session,
            )
        else:
            log.warning("No transaction_id available to fetch Transaction Details.")
    else:
        log.warning("No beneficiary_id available; full off-ramp transfer flow was not executed.")

    # -------------------------------------------------------------------------
    # 19. Optional: Create Individual Customer (with Humam Izu data)
    #     Skipped when using existing CUSTOMER_ID; uncomment to test create.
    # -------------------------------------------------------------------------
    # log.info(">>> 19. Customers – Create Individual Customer (optional)")
    # _parts = CUSTOMER_NAME.strip().split(None, 1)
    # _first, _last = (_parts[0], _parts[1]) if len(_parts) > 1 else ("Humam", "Izu")
    # api_call(
    #     "Create Individual Customer",
    #     "POST",
    #     "/v1/customers/individual",
    #     session,
    #     json_body={
    #         "verification_type": "STANDARD",
    #         "basic_info": {
    #             "first_name": _first,
    #             "last_name": _last,
    #             "dob": "1990-01-15",
    #             "email": CUSTOMER_EMAIL,
    #             "phone": "+1234567890",
    #             "country_of_residence": "USA",
    #             "nationality": "USA",
    #             "tin": "123-45-6789",
    #         },
    #         "address": {
    #             "street": "123 Main St",
    #             "city": "New York",
    #             "state": "US-NY",
    #             "postal_code": "10001",
    #             "country": "USA",
    #         },
    #         "financial_profile": {
    #             "occupation_id": 1,
    #             "source_of_fund_id": 1,
    #             "purpose_id": 1,
    #             "monthly_volume_usd": 5000,
    #         },
    #     },
    # )

    # If we had a beneficiary_id we could call:
    # - List Beneficiary Transactions
    # - List Transactions for Beneficiary
    # - Create a Transfer / Settle (need valid beneficiary + amount)

    # -------------------------------------------------------------------------
    # Final API flow summary (all endpoints in order)
    # -------------------------------------------------------------------------
    log.info("")
    log.info("===== INDIVIDUAL CUSTOMER API FLOW – SUMMARY =====")
    for idx, rinfo in enumerate(API_RESULTS, start=1):
        status = int(rinfo.get("status", 0))
        name = rinfo.get("name")
        method = rinfo.get("method")
        path = rinfo.get("path")
        marker = "OK"
        if 400 <= status < 500:
            marker = "CLIENT_ERROR"
        elif 500 <= status < 600:
            marker = "SERVER_ERROR"
        log.info(
            "%02d. [%s] status=%s | %s %s",
            idx,
            marker,
            status,
            method,
            path,
        )
    log.info("==================================================")

    # Summary of any 4xx/5xx errors by API name
    errors = [r for r in API_RESULTS if 400 <= int(r.get("status", 0)) < 600]
    if errors:
        log.info("")
        log.info("===== ENDPOINTS WITH ERRORS (4xx/5xx) =====")
        for err in errors:
            log.info(
                "- %s | status=%s | %s %s",
                err.get("name"),
                err.get("status"),
                err.get("method"),
                err.get("path"),
            )
        log.info("==========================================")
    else:
        log.info("All endpoints returned 2xx/3xx (no 4xx/5xx errors).")

    log.info("")
    log.info(">>> Individual Customer API flow finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
