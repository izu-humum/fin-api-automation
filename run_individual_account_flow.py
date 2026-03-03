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
# Wallet address to receive USDC (virtual account destination); we update virtual account to send here
TARGET_WALLET_ADDRESS = os.environ.get("FIN_TARGET_WALLET_ADDRESS", "0xef7f82e4c116d52d57021ee774d193b540653e59").strip()
# Your wallet address from API or after update; shown in summary for faucet
MY_WALLET_ADDRESS: Optional[str] = None

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

# Last access token issued in this run (for summary logging)
LAST_ACCESS_TOKEN: Optional[str] = None

# Any beneficiary_ids created/used during this run (for summary logging)
BENEFICIARY_IDS: list[str] = []
# Map beneficiary_id -> currency (used to prefer non-USD for transfer-payout)
BENEFICIARY_ID_TO_CURRENCY: dict[str, str] = {}
# Map beneficiary_id -> liquidation_address (for auto_settlement deposit flow)
BENEFICIARY_ID_TO_LIQ_ADDR: dict[str, str] = {}
# Liquidation addresses from beneficiary details (for summary / faucet USDC)
LIQUIDATION_ADDRESSES: set[str] = set()
# Account suffixes for beneficiaries created by Path B (manual transfer, auto_settlement=false)
MANUAL_TRANSFER_ACCT_SUFFIXES = ("0978",)
# Populated during step 15 if we detect Path-B beneficiaries from previous runs
KNOWN_MANUAL_BEN_IDS: set[str] = set()
# Beneficiary IDs that are corrupted on the Fin dashboard (exclude from all flows)
CORRUPTED_BEN_IDS: set[str] = {
    "4651bc42-74c6-402f-8b93-83ac5c0e44c3",
    "f459f273-8190-4578-989b-1d1b3c2195f4",
    "ee2afebf-8dd4-4976-8fde-5656ef89196c",
    "2f4d7207-1f9f-4ee5-b0bb-ea869e425467",
}

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
    # Print the access token so it is visible in the terminal run
    log.info("Access token: %s", access_token)
    global LAST_ACCESS_TOKEN, MY_WALLET_ADDRESS
    LAST_ACCESS_TOKEN = access_token

    # -------------------------------------------------------------------------
    # 2. Balances – Fetch Prefunded Balance
    #    Skipped when using auto settlement: prefund balance is not required to run
    #    transactions when settlement_config.auto_settlement is true.
    # -------------------------------------------------------------------------
    log.info(">>> 2. Balances – Fetch Prefunded Balance (skipped; not required for auto settlement)")

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
    # 3b. Virtual Accounts – List Virtual Accounts (your wallet for faucet)
    # -------------------------------------------------------------------------
    log.info(">>> 3b. Virtual Accounts – List Virtual Accounts")
    r_va = api_call(
        "List Virtual Accounts",
        "GET",
        "/v1/customers/virtual-account",
        session,
        params={"customer_id": CUSTOMER_ID},
    )
    first_va_id: Optional[str] = None
    if r_va.status_code == 200:
        try:
            payload = r_va.json()
            data = payload.get("data") or payload
            accounts = data.get("virtual_accounts") or []
            for va in accounts:
                if isinstance(va, dict):
                    if va.get("id") and not first_va_id:
                        first_va_id = va["id"]
                    dest = va.get("destination")
                    if isinstance(dest, dict) and dest.get("address"):
                        MY_WALLET_ADDRESS = dest["address"]
                        break
        except Exception as exc:
            log.debug("Could not parse virtual account destination from response: %s", exc)

    # -------------------------------------------------------------------------
    # 3c. Virtual Accounts – Create (if none) or Update (send USDC to your wallet)
    #     You faucet this wallet, then send to beneficiaries.
    # -------------------------------------------------------------------------
    if not first_va_id and TARGET_WALLET_ADDRESS:
        log.info(">>> 3c. Virtual Accounts – Create Virtual Account (customer %s, destination: your wallet)", CUSTOMER_ID)
        r_create_va = api_call(
            "Create Virtual Account",
            "POST",
            "/v1/customers/virtual-account",
            session,
            json_body={
                "customer_id": CUSTOMER_ID,
                "destination_currency": "USDC",
                "destination_chain": "POLYGON",
                "source_rail": "ACH",
                "source_currency": "USD",
                "destination_wallet_address": TARGET_WALLET_ADDRESS,
                "developer_fee_percentage": 1.5,
            },
        )
        if r_create_va.status_code == 200:
            try:
                create_data = (r_create_va.json().get("data") or r_create_va.json())
                if isinstance(create_data, dict) and create_data.get("id"):
                    first_va_id = create_data["id"]
                MY_WALLET_ADDRESS = TARGET_WALLET_ADDRESS
                log.info("Virtual account created for customer %s; faucet this address then send to beneficiaries: %s", CUSTOMER_ID, TARGET_WALLET_ADDRESS)
            except Exception as exc:
                log.debug("Could not parse Create Virtual Account response: %s", exc)
        else:
            log.warning("Create Virtual Account returned %s.", r_create_va.status_code)
    elif first_va_id and TARGET_WALLET_ADDRESS and MY_WALLET_ADDRESS != TARGET_WALLET_ADDRESS:
        log.info(">>> 3c. Virtual Accounts – Update Virtual Account (destination: your wallet %s...)", TARGET_WALLET_ADDRESS[:18])
        r_update_va = api_call(
            "Update Virtual Account",
            "PUT",
            "/v1/customers/virtual-account",
            session,
            json_body={
                "id": first_va_id,
                "customer_id": CUSTOMER_ID,
                "destination_wallet_address": TARGET_WALLET_ADDRESS,
            },
        )
        if r_update_va.status_code == 200:
            MY_WALLET_ADDRESS = TARGET_WALLET_ADDRESS
            log.info("Virtual account updated; faucet this address then send to beneficiaries: %s", TARGET_WALLET_ADDRESS)
        else:
            log.warning("Update Virtual Account returned %s; summary may show previous destination.", r_update_va.status_code)

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
    r_list_ben = api_call(
        "List Beneficiaries For Customer",
        "GET",
        f"/v1/customers/{CUSTOMER_ID}/beneficiaries",
        session,
    )
    # Pre-populate BENEFICIARY_IDS from existing beneficiaries (if any)
    if r_list_ben.status_code == 200:
        try:
            body = r_list_ben.json().get("data") or r_list_ben.json()
            existing_bens = body.get("beneficiaries") or []
            for ben in existing_bens:
                if isinstance(ben, dict):
                    bid = ben.get("id") or ben.get("beneficiary_id")
                    if bid:
                        bid_str = str(bid)
                        if bid_str in CORRUPTED_BEN_IDS:
                            log.info("Skipping corrupted beneficiary: %s", bid_str)
                            continue
                        if bid_str not in BENEFICIARY_IDS:
                            BENEFICIARY_IDS.append(bid_str)
                        cur = ben.get("currency") or "USD"
                        BENEFICIARY_ID_TO_CURRENCY[bid_str] = cur
                        liq = ben.get("liquidation_address")
                        if liq:
                            LIQUIDATION_ADDRESSES.add(liq)
                            BENEFICIARY_ID_TO_LIQ_ADDR[bid_str] = liq
                        acct = ben.get("account_number") or ""
                        if any(acct.endswith(s) for s in MANUAL_TRANSFER_ACCT_SUFFIXES):
                            KNOWN_MANUAL_BEN_IDS.add(bid_str)
                            log.info("Detected Path-B (manual-transfer) beneficiary from previous run: %s", bid_str)
            if BENEFICIARY_IDS:
                log.info(
                    "Found %d existing beneficiary id(s) for customer; ids: %s",
                    len(BENEFICIARY_IDS),
                    ", ".join(BENEFICIARY_IDS),
                )
        except Exception:
            # If parsing fails, just continue; dummy creation logic will still work.
            pass

    # -------------------------------------------------------------------------
    # 15a. Beneficiaries – Create dummy beneficiaries (for testing, USA/ACH)
    # -------------------------------------------------------------------------
    if customer_approved:
        # If we already have beneficiaries for this customer, avoid creating duplicates.
        if BENEFICIARY_IDS:
            log.info(
                "Skipping creation of dummy beneficiaries because %d beneficiary id(s) already exist for customer.",
                len(BENEFICIARY_IDS),
            )
        else:
            log.info(">>> 15a. Beneficiaries – Create dummy beneficiaries for customer (USA/ACH)")
            base_first, base_last = _split_name(CUSTOMER_NAME)
            dummy_account_numbers = ["1234567890", "1234567891"]
            for idx, acc_no in enumerate(dummy_account_numbers, start=1):
                dummy_body = {
                "customer_id": CUSTOMER_ID,
                "country": "USA",
                "currency": "USD",
                "account_holder": {
                    "type": "INDIVIDUAL",
                    "first_name": base_first,
                    "last_name": base_last,
                    "email": CUSTOMER_EMAIL,
                    "phone": "+12025551234",
                },
                "account_holder_address": {
                    "street_line_1": "456 Main Street",
                    "city": "Brooklyn",
                    "state": "US-NY",
                    "postcode": "11201",
                    "country": "USA",
                    "street_line_2": "Apt 5B",
                },
                "receiver_meta_data": {
                    "transaction_purpose_id": 1,
                    "occupation_remarks": "Software Engineer",
                    "relationship": "EMPLOYEE",
                    "nationality": "USA",
                    "transaction_purpose_remarks": "Monthly salary payment",
                    "occupation_id": 5,
                    "relationship_remarks": "Long-term contractor",
                    "govt_id_number": "JG1121316A",
                    "govt_id_issue_date": "2024-12-30",
                    "govt_id_expire_date": "2027-12-30",
                },
                "developer_fee": {
                    "fixed": 5,
                    "percentage": 2.5,
                },
                "deposit_instruction": {
                    "currency": "USDC",
                    "rail": "POLYGON",
                },
                "refund_instruction": {
                    "wallet_address": "0x1b577931c1cc2765024bfbafad97bce14ff2e87f",
                    "currency": "USDC",
                    "rail": "POLYGON",
                },
                "bank_account": {
                    "bank_name": "Chase Bank",
                    "number": acc_no,
                    "scheme": "LOCAL",
                    "type": "CHECKING",
                },
                "bank_routing": [
                    {
                        "scheme": "ACH",
                        "number": "021000021",
                    },
                    {
                        "scheme": "BANK_IDENTIFIER",
                        "number": "1",
                    },
                ],
                "bank_address": {
                    "street_line_1": "123 Bank Street",
                    "city": "New York",
                    "state": "US-NY",
                    "postcode": "10001",
                    "country": "USA",
                    "street_line_2": "Suite 100",
                },
                    "settlement_config": {
                        "auto_settlement": True,
                    },
                }
                r_dummy = api_call(
                    f"Create Dummy Beneficiary {idx}",
                    "POST",
                    "/v2/beneficiaries",
                    session,
                    json_body=dummy_body,
                )
                if r_dummy.status_code == 200:
                    try:
                        ben_payload = r_dummy.json().get("data") or r_dummy.json()
                        ben_id = ben_payload.get("id") or ben_payload.get("beneficiary_id")
                        if ben_id:
                            ben_id_str = str(ben_id)
                            BENEFICIARY_IDS.append(ben_id_str)
                            BENEFICIARY_ID_TO_CURRENCY[ben_id_str] = "USD"
                            log.info(
                                "Captured dummy beneficiary %s id: %s",
                                idx,
                                ben_id_str,
                            )
                            # Ensure beneficiary is active per Update Beneficiary Active Status API
                            api_call(
                                f"Activate Dummy Beneficiary {idx}",
                                "PATCH",
                                "/v1/beneficiaries",
                                session,
                                json_body={"beneficiary_id": ben_id_str, "active": True},
                            )
                    except Exception:
                        log.warning(
                            "Could not parse beneficiary id from dummy beneficiary %s response.",
                            idx,
                        )
                else:
                    log_422_errors(f"Create Dummy Beneficiary {idx}", r_dummy)
    else:
        log.info(
            "Skipping creation of dummy beneficiaries because customer is not APPROVED."
        )

    # -------------------------------------------------------------------------
    # 15b. Beneficiaries – Create non-USD dummy beneficiaries (GBP, EUR) for transfer
    #      Sandbox transfer-payout rejects "unsupported beneficiary currency: USD";
    #      create GBP/EUR beneficiaries and use one for the transfer.
    # -------------------------------------------------------------------------
    if customer_approved:
        # If there is already at least one non-USD beneficiary, avoid creating more
        # to respect the \"no duplicate destination\" rule and reduce 409s.
        existing_non_usd = [
            (bid, cur)
            for bid, cur in BENEFICIARY_ID_TO_CURRENCY.items()
            if cur and cur.upper() != "USD"
        ]
        if existing_non_usd:
            log.info(
                "Skipping creation of non-USD beneficiaries because %d non-USD beneficiary(ies) already exist for customer.",
                len(existing_non_usd),
            )
        else:
            base_first, base_last = _split_name(CUSTOMER_NAME)
            non_usd_beneficiaries = [
                {
                    "label": "GBR/GBP",
                    "country": "GBR",
                    "currency": "GBP",
                    # Germany/GBR phone formats use fixed national lengths;
                    # this number matches the +44 pattern and expected length.
                    "phone": "+447700900123",
                    "postcode": "SW1A 1AA",
                    "state": "GB-LND",
                    "bank_name": "Barclays",
                    "account_number": "12345678",
                    # Use allowed routing schemes for GBR: e.g. SWIFT + BANK_IDENTIFIER
                    "bank_routing": [
                        {"scheme": "SWIFT", "number": "BARCGB22"},
                        {"scheme": "BANK_IDENTIFIER", "number": "123456"},
                    ],
                    "city": "London",
                    "street_line_1": "10 Downing Street",
                },
                {
                    "label": "DEU/EUR",
                    "country": "DEU",
                    "currency": "EUR",
                    # Ensure digit count within DEU range (10–11 digits excluding '+').
                    "phone": "+49301234567",
                    "postcode": "10115",
                    "state": "DE-BE",
                    "bank_name": "Deutsche Bank",
                    "account_number": "32013000",
                    # DEU requires 'bank_identifier' routing; include both IBAN and BANK_IDENTIFIER.
                    "bank_routing": [
                        {"scheme": "IBAN", "number": "DE89370400440532013000"},
                        {"scheme": "BANK_IDENTIFIER", "number": "10070000"},
                    ],
                    "city": "Berlin",
                    "street_line_1": "Unter den Linden 1",
                },
            ]
            for spec in non_usd_beneficiaries:
                log.info(">>> 15b. Create non-USD beneficiary (%s)", spec["label"])
            body_15b = {
                "customer_id": CUSTOMER_ID,
                "country": spec["country"],
                "currency": spec["currency"],
                "account_holder": {
                    "type": "INDIVIDUAL",
                    "first_name": base_first,
                    "last_name": base_last,
                    "email": CUSTOMER_EMAIL,
                    "phone": spec["phone"],
                },
                "account_holder_address": {
                    "street_line_1": spec["street_line_1"],
                    "city": spec["city"],
                    "postcode": spec["postcode"],
                    "country": spec["country"],
                },
                "receiver_meta_data": {
                    "transaction_purpose_id": 1,
                    "occupation_remarks": "Software Engineer",
                    "relationship": "EMPLOYEE",
                    "nationality": spec["country"],
                    "transaction_purpose_remarks": "Monthly salary payment",
                    "occupation_id": 5,
                    "relationship_remarks": "Long-term contractor",
                    "govt_id_number": "JG1121316A",
                    "govt_id_issue_date": "2024-12-30",
                    "govt_id_expire_date": "2027-12-30",
                },
                "developer_fee": {"fixed": 5, "percentage": 2.5},
                "deposit_instruction": {"currency": "USDC", "rail": "POLYGON"},
                "refund_instruction": {
                    "wallet_address": "0x1b577931c1cc2765024bfbafad97bce14ff2e87f",
                    "currency": "USDC",
                    "rail": "POLYGON",
                },
                "bank_account": {
                    "bank_name": spec["bank_name"],
                    "number": spec["account_number"],
                    "scheme": "LOCAL",
                    "type": "CHECKING",
                },
                "bank_routing": spec["bank_routing"],
                "bank_address": {
                    "street_line_1": spec["street_line_1"],
                    "city": spec["city"],
                    "postcode": spec["postcode"],
                    "country": spec["country"],
                },
                "settlement_config": {"auto_settlement": True},
            }
            if spec.get("state"):
                body_15b["account_holder_address"]["state"] = spec["state"]
                body_15b["bank_address"]["state"] = spec["state"]
            r_15b = api_call(
                f"Create non-USD Beneficiary ({spec['label']})",
                "POST",
                "/v2/beneficiaries",
                session,
                json_body=body_15b,
            )
            if r_15b.status_code == 200:
                try:
                    ben_payload = r_15b.json().get("data") or r_15b.json()
                    ben_id = ben_payload.get("id") or ben_payload.get("beneficiary_id")
                    if ben_id:
                        ben_id_str = str(ben_id)
                        BENEFICIARY_IDS.append(ben_id_str)
                        BENEFICIARY_ID_TO_CURRENCY[ben_id_str] = spec["currency"]
                        log.info(
                            "Created non-USD beneficiary %s id: %s",
                            spec["label"],
                            ben_id_str,
                        )
                        api_call(
                            f"Activate non-USD Beneficiary ({spec['label']})",
                            "PATCH",
                            "/v1/beneficiaries",
                            session,
                            json_body={"beneficiary_id": ben_id_str, "active": True},
                        )
                except Exception:
                    log.warning(
                        "Could not parse beneficiary id from non-USD %s response.",
                        spec["label"],
                    )
            elif r_15b.status_code == 409:
                log.info(
                    "Non-USD beneficiary %s already exists (409 Conflict); skipping.",
                    spec["label"],
                )
            else:
                log_422_errors(f"Create non-USD Beneficiary ({spec['label']})", r_15b)

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
    # 19. Off-ramp flow – Reuse Beneficiary, Transfer, Settle, Inspect
    # -------------------------------------------------------------------------
    beneficiary_id: Optional[str] = None

    if not customer_approved:
        log.info(
            "Skipping off-ramp flow because customer is not in APPROVED status."
        )
    else:
        # Priority for off-ramp:
        # 1) FIN_BENEFICIARY_ID if provided
        # 2) Any previously created beneficiary id from this run (e.g. dummy beneficiaries)
        # 3) (fallback) create a new off-ramp beneficiary
        if EXISTING_BENEFICIARY_ID:
            log.info(
                "Using existing beneficiary id from FIN_BENEFICIARY_ID = %s for off-ramp flow",
                EXISTING_BENEFICIARY_ID,
            )
            beneficiary_id = EXISTING_BENEFICIARY_ID
            if EXISTING_BENEFICIARY_ID not in BENEFICIARY_IDS:
                BENEFICIARY_IDS.append(EXISTING_BENEFICIARY_ID)
            api_call(
                "Activate Existing Beneficiary",
                "PATCH",
                "/v1/beneficiaries",
                session,
                json_body={"beneficiary_id": EXISTING_BENEFICIARY_ID, "active": True},
            )
        elif BENEFICIARY_IDS:
            # Selection priority for off-ramp Path A (auto_settlement=true demo):
            #   1) non-USD with liquidation_address (best for auto_settlement deposit flow)
            #   2) any with liquidation_address (auto_settlement works via on-chain deposit)
            #   3) non-USD without liquidation_address (can attempt transfer-payout)
            #   4) fallback to first beneficiary
            # Exclude KNOWN_MANUAL_BEN_IDS (Path B's auto_settlement=false beneficiaries)
            beneficiary_id = None
            pool = [b for b in BENEFICIARY_IDS if b not in KNOWN_MANUAL_BEN_IDS]
            non_usd_with_liq = [b for b in pool if BENEFICIARY_ID_TO_CURRENCY.get(b, "USD") != "USD" and b in BENEFICIARY_ID_TO_LIQ_ADDR]
            any_with_liq = [b for b in pool if b in BENEFICIARY_ID_TO_LIQ_ADDR]
            non_usd_any = [b for b in pool if BENEFICIARY_ID_TO_CURRENCY.get(b, "USD") != "USD"]

            if non_usd_with_liq:
                beneficiary_id = non_usd_with_liq[0]
                log.info("Using non-USD beneficiary with liquidation_address: %s (currency=%s, liq=%s)",
                         beneficiary_id, BENEFICIARY_ID_TO_CURRENCY.get(beneficiary_id), BENEFICIARY_ID_TO_LIQ_ADDR.get(beneficiary_id))
            elif any_with_liq:
                beneficiary_id = any_with_liq[0]
                log.info("Using beneficiary with liquidation_address: %s (currency=%s, liq=%s)",
                         beneficiary_id, BENEFICIARY_ID_TO_CURRENCY.get(beneficiary_id), BENEFICIARY_ID_TO_LIQ_ADDR.get(beneficiary_id))
            elif non_usd_any:
                beneficiary_id = non_usd_any[0]
                log.info("Using non-USD beneficiary (no liquidation_address): %s (currency=%s)",
                         beneficiary_id, BENEFICIARY_ID_TO_CURRENCY.get(beneficiary_id))
            else:
                beneficiary_id = pool[0] if pool else BENEFICIARY_IDS[0]
                log.info("Reusing first beneficiary_id=%s for off-ramp transfer.", beneficiary_id)
            api_call(
                "Activate Reused Beneficiary for Off-ramp",
                "PATCH",
                "/v1/beneficiaries",
                session,
                json_body={"beneficiary_id": beneficiary_id, "active": True},
            )
        else:
            log.info(">>> 19.1 Beneficiaries – Create Beneficiary (off-ramp test, GBR/GBP)")
            first_name, last_name = _split_name(CUSTOMER_NAME)
            create_beneficiary_body = {
                "customer_id": CUSTOMER_ID,
                "country": "GBR",
                "currency": "GBP",
                "account_holder": {
                    "type": "INDIVIDUAL",
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": CUSTOMER_EMAIL,
                    "phone": "+441234567890",
                },
                "account_holder_address": {
                    "street_line_1": "10 Downing Street",
                    "city": "London",
                    "postcode": "SW1A 1AA",
                    "country": "GBR",
                },
                "receiver_meta_data": {
                    "transaction_purpose_id": 1,
                    "occupation_remarks": "Software Engineer",
                    "relationship": "EMPLOYEE",
                    "nationality": "GBR",
                    "transaction_purpose_remarks": "Monthly salary payment",
                    "occupation_id": 5,
                    "relationship_remarks": "Long-term contractor",
                    "govt_id_number": "JG1121316A",
                    "govt_id_issue_date": "2024-12-30",
                    "govt_id_expire_date": "2027-12-30",
                },
                "developer_fee": {"fixed": 5, "percentage": 2.5},
                "deposit_instruction": {"currency": "USDC", "rail": "POLYGON"},
                "refund_instruction": {
                    "wallet_address": "0x1b577931c1cc2765024bfbafad97bce14ff2e87f",
                    "currency": "USDC",
                    "rail": "POLYGON",
                },
                "bank_account": {
                    "bank_name": "Barclays",
                    "number": "87654321",
                    "scheme": "LOCAL",
                    "type": "CHECKING",
                },
                "bank_routing": [{"scheme": "BRANCH_CODE", "number": "654321"}],
                "bank_address": {
                    "street_line_1": "10 Downing Street",
                    "city": "London",
                    "postcode": "SW1A 1AA",
                    "country": "GBR",
                },
                "settlement_config": {"auto_settlement": True},
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
                    if beneficiary_id:
                        beneficiary_id_str = str(beneficiary_id)
                        BENEFICIARY_IDS.append(beneficiary_id_str)
                        BENEFICIARY_ID_TO_CURRENCY[beneficiary_id_str] = "GBP"
                        log.info("Captured off-ramp beneficiary id: %s", beneficiary_id_str)
                        api_call(
                            "Activate Off-ramp Beneficiary",
                            "PATCH",
                            "/v1/beneficiaries",
                            session,
                            json_body={
                                "beneficiary_id": beneficiary_id_str,
                                "active": True,
                            },
                        )
                except Exception:
                    beneficiary_id = None
            else:
                log_422_errors("Create Beneficiary (Off-ramp Test)", r_ben)
                log.warning(
                    "Create Beneficiary (Off-ramp Test) failed with status %s; skipping transfer flow.",
                    r_ben.status_code,
                )

    if beneficiary_id and customer_approved:
        log.info("Using beneficiary_id=%s for off-ramp transfer flow.", beneficiary_id)

        # 19.2 – Fetch Beneficiary Details v1
        log.info(">>> 19.2 Beneficiaries – Fetch Beneficiary Details v1")
        r_ben_details = api_call(
            "Fetch Beneficiary Details v1 (Off-ramp Test)",
            "GET",
            "/v1/beneficiaries/details",
            session,
            params={"customer_id": CUSTOMER_ID, "beneficiary_id": beneficiary_id},
        )
        # Update currency map from authoritative beneficiary details so that
        # off-ramp transfer uses the actual beneficiary currency (often non-USD).
        ben_auto_settlement: Optional[bool] = None
        liq_addr: Optional[str] = None
        try:
            d_body = r_ben_details.json().get("data") or r_ben_details.json()
            ben_currency = d_body.get("currency")
            if ben_currency:
                BENEFICIARY_ID_TO_CURRENCY[beneficiary_id] = ben_currency
                log.info(
                    "Beneficiary %s has currency=%s (from details).",
                    beneficiary_id,
                    ben_currency,
                )
            ben_auto_settlement = d_body.get("auto_settlement")
            if ben_auto_settlement is not None:
                log.info(
                    "Beneficiary %s auto_settlement=%s (from details).",
                    beneficiary_id,
                    ben_auto_settlement,
                )
            # Remind user: transactions require USDC at the liquidation address.
            liq_addr = d_body.get("liquidation_address")
            if liq_addr:
                LIQUIDATION_ADDRESSES.add(liq_addr)
                BENEFICIARY_ID_TO_LIQ_ADDR[beneficiary_id] = liq_addr
                log.info("Beneficiary liquidation_address: %s", liq_addr)
        except Exception:
            # If parsing fails we will fall back to existing mapping/defaults.
            ben_auto_settlement = None

        # auto_settlement (beneficiary-level, pay-per-transaction model):
        # - true:  Fin auto-initiates fiat payout when crypto is received at the beneficiary's liquidation_address.
        #          You CANNOT call transfer-payout; deposit USDC to the liquidation_address instead.
        # - false: Fin holds crypto until you trigger payout via Create Transfer + Settle a Transfer (or Execute Batch Transfer).
        # Note: With prefunded balance, auto_settlement has no effect — payouts must always be triggered programmatically.

        transfer_id: Optional[str] = None
        transaction_id: Optional[str] = None

        if ben_auto_settlement:
            # --- auto_settlement=true path: deposit USDC to liquidation_address ---
            ben_liq = liq_addr or BENEFICIARY_ID_TO_LIQ_ADDR.get(beneficiary_id)
            if ben_liq:
                log.info(">>> 19.3 Auto-Settlement Flow (beneficiary %s)", beneficiary_id)
                log.info(
                    "auto_settlement=true – transfer-payout is blocked by the API. "
                    "Deposit USDC to the beneficiary's liquidation_address and Fin auto-creates the payout."
                )
                log.info("Liquidation address for deposits: %s", ben_liq)
            else:
                log.warning(
                    "auto_settlement=true but beneficiary %s has no liquidation_address. "
                    "Cannot create transfers via API or via deposit. "
                    "This beneficiary may need to be re-created with deposit_instruction to get a liquidation_address.",
                    beneficiary_id,
                )
        else:
            # --- auto_settlement=false (or unknown) path: Create Transfer + Settle ---
            transfer_currency = "USDC"
            log.info(">>> 19.3 Transactions – Create a Transfer (currency=%s)", transfer_currency)
            transfer_body = {
                "beneficiary_id": beneficiary_id,
                "reference_id": "OFFRAMP-TEST-REF-1",
                "amount": 500,
                "currency": transfer_currency,
                "remarks": "Off-ramp test transfer from automation script",
            }
            r_transfer = api_call(
                "Create a Transfer (Off-ramp Test)",
                "POST",
                "/v1/transactions/transfer-payout",
                session,
                json_body=transfer_body,
            )
            if r_transfer.status_code == 200:
                try:
                    t_data = r_transfer.json().get("data") or r_transfer.json()
                    transfer_id = t_data.get("transfer_id")
                except Exception:
                    transfer_id = None
            else:
                log.warning("Create Transfer failed with status %s; skipping settle + transaction detail.", r_transfer.status_code)

            # 19.4 – Settle a Transfer
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
    # 20. Off-ramp Path B – Manual Transfer (auto_settlement=false beneficiary)
    #     Create a new GBP beneficiary with auto_settlement disabled,
    #     then run the full programmatic transfer-payout + settle flow.
    #     NOTE: The sandbox may reject transfer-payout if the beneficiary's
    #     liquidation address was not yet provisioned (wallet service timeout).
    # -------------------------------------------------------------------------
    manual_beneficiary_id: Optional[str] = None
    manual_transfer_id: Optional[str] = None
    manual_transaction_id: Optional[str] = None

    if customer_approved:
        # 20.1 – Create GBP beneficiary with auto_settlement=false
        log.info(">>> 20.1 Beneficiaries – Create GBP Beneficiary (auto_settlement=false)")
        first_name, last_name = _split_name(CUSTOMER_NAME)
        manual_ben_body = {
            "customer_id": CUSTOMER_ID,
            "country": "GBR",
            "currency": "GBP",
            "account_holder": {
                "type": "INDIVIDUAL",
                "first_name": first_name,
                "last_name": last_name,
                "email": CUSTOMER_EMAIL,
                "phone": "+442012345678",
            },
            "account_holder_address": {
                "street_line_1": "221B Baker Street",
                "city": "London",
                "state": "GB-LND",
                "postcode": "NW1 6XE",
                "country": "GBR",
            },
            "receiver_meta_data": {
                "transaction_purpose_id": 1,
                "occupation_remarks": "Software Engineer",
                "relationship": "EMPLOYEE",
                "nationality": "GBR",
                "transaction_purpose_remarks": "Monthly salary payment",
                "occupation_id": 5,
                "relationship_remarks": "Long-term contractor",
                "govt_id_number": "JG1121316A",
                "govt_id_issue_date": "2024-12-30",
                "govt_id_expire_date": "2027-12-30",
            },
            "developer_fee": {"fixed": 5, "percentage": 2.5},
            "deposit_instruction": {"currency": "USDC", "rail": "POLYGON"},
            "refund_instruction": {
                "wallet_address": "0x87d7eD4285FE9512d2dC9e0B4B993D377eB0d155",
                "currency": "USDC",
                "rail": "POLYGON",
            },
            "bank_account": {
                "bank_name": "HSBC UK",
                "number": "41520978",
                "scheme": "LOCAL",
                "type": "CHECKING",
            },
            "bank_routing": [
                {"scheme": "IBAN", "number": "GB82HBUK40127641520978"},
                {"scheme": "BANK_IDENTIFIER", "number": "275"},
            ],
            "bank_address": {
                "street_line_1": "8 Canada Square",
                "city": "London",
                "state": "GB-LND",
                "postcode": "E14 5HQ",
                "country": "GBR",
            },
            "settlement_config": {"auto_settlement": False},
        }
        r_manual_ben = api_call(
            "Create GBP Beneficiary (auto_settlement=false)",
            "POST",
            "/v2/beneficiaries",
            session,
            json_body=manual_ben_body,
        )

        def _extract_manual_ben_id(resp) -> Optional[str]:
            """Try to extract beneficiary_id from various response shapes."""
            try:
                body = resp.json()
                # 200 with data.beneficiary_id
                d = body.get("data") or body
                bid = d.get("id") or d.get("beneficiary_id")
                if bid:
                    return str(bid)
                # 409/422 with error.beneficiary_id
                err = body.get("error") or {}
                if isinstance(err, dict) and "beneficiary_id" in err:
                    return str(err["beneficiary_id"])
                for e in (body.get("errors") or []):
                    if isinstance(e, dict) and "beneficiary_id" in e:
                        return str(e["beneficiary_id"])
            except Exception:
                pass
            return None

        if r_manual_ben.status_code in (200, 409, 422):
            manual_beneficiary_id = _extract_manual_ben_id(r_manual_ben)
            if manual_beneficiary_id and manual_beneficiary_id in CORRUPTED_BEN_IDS:
                log.warning("Extracted beneficiary %s is corrupted; ignoring.", manual_beneficiary_id)
                manual_beneficiary_id = None
            if manual_beneficiary_id:
                if manual_beneficiary_id not in BENEFICIARY_IDS:
                    BENEFICIARY_IDS.append(manual_beneficiary_id)
                BENEFICIARY_ID_TO_CURRENCY[manual_beneficiary_id] = "GBP"
                log.info("Manual-transfer beneficiary: %s (status=%s)", manual_beneficiary_id, r_manual_ben.status_code)
            elif KNOWN_MANUAL_BEN_IDS:
                # Prefer a GBP one from the known set
                gbp_candidates = [b for b in KNOWN_MANUAL_BEN_IDS if BENEFICIARY_ID_TO_CURRENCY.get(b) == "GBP"]
                manual_beneficiary_id = gbp_candidates[0] if gbp_candidates else next(iter(KNOWN_MANUAL_BEN_IDS))
                log.info("Using known manual-transfer beneficiary from step 15: %s", manual_beneficiary_id)
            else:
                # Last resort: re-list and find GBP with account ending in "6819"
                log.info("Beneficiary ID not in response; searching via List Beneficiaries...")
                r_relist = api_call(
                    "Re-list Beneficiaries (find manual-transfer ben)",
                    "GET",
                    f"/v1/customers/{CUSTOMER_ID}/beneficiaries",
                    session,
                )
                if r_relist.status_code == 200:
                    try:
                        rl_body = r_relist.json().get("data") or r_relist.json()
                        for b in (rl_body.get("beneficiaries") or []):
                            bid = str(b.get("id") or "")
                            acct = b.get("account_number") or ""
                            if b.get("currency") == "GBP" and acct.endswith("0978") and bid not in CORRUPTED_BEN_IDS:
                                manual_beneficiary_id = bid
                                if bid not in BENEFICIARY_IDS:
                                    BENEFICIARY_IDS.append(bid)
                                BENEFICIARY_ID_TO_CURRENCY[bid] = "GBP"
                                log.info("Found manual-transfer beneficiary from re-list: %s", bid)
                                break
                    except Exception:
                        pass
            if r_manual_ben.status_code == 422 and not manual_beneficiary_id:
                log_422_errors("Create GBP Beneficiary (auto_settlement=false)", r_manual_ben)
        elif r_manual_ben.status_code == 500:
            log.warning("Sandbox wallet service timed out (500). The beneficiary may still be created.")
            # Try to find it via re-list
            r_relist = api_call(
                "Re-list Beneficiaries (find manual-transfer ben after 500)",
                "GET",
                f"/v1/customers/{CUSTOMER_ID}/beneficiaries",
                session,
            )
            if r_relist.status_code == 200:
                try:
                    rl_body = r_relist.json().get("data") or r_relist.json()
                    for b in (rl_body.get("beneficiaries") or []):
                        bid = str(b.get("id") or "")
                        acct = b.get("account_number") or ""
                        if b.get("currency") == "GBP" and acct.endswith("0978") and bid not in CORRUPTED_BEN_IDS:
                            manual_beneficiary_id = bid
                            if bid not in BENEFICIARY_IDS:
                                BENEFICIARY_IDS.append(bid)
                            BENEFICIARY_ID_TO_CURRENCY[bid] = "GBP"
                            log.info("Found manual-transfer beneficiary despite 500: %s", bid)
                            break
                except Exception:
                    pass
        else:
            log.warning("Create GBP Beneficiary failed with status %s.", r_manual_ben.status_code)

        if manual_beneficiary_id:
            api_call(
                "Activate Manual-Transfer Beneficiary",
                "PATCH",
                "/v1/beneficiaries",
                session,
                json_body={"beneficiary_id": manual_beneficiary_id, "active": True},
            )

    if manual_beneficiary_id and customer_approved:
        # 20.2 – Fetch Beneficiary Details v1
        log.info(">>> 20.2 Beneficiaries – Fetch Beneficiary Details v1 (manual transfer)")
        r_mb_details = api_call(
            "Fetch Beneficiary Details v1 (Manual Transfer)",
            "GET",
            "/v1/beneficiaries/details",
            session,
            params={"customer_id": CUSTOMER_ID, "beneficiary_id": manual_beneficiary_id},
        )
        manual_currency = "GBP"
        try:
            mb_d = r_mb_details.json().get("data") or r_mb_details.json()
            manual_currency = mb_d.get("currency") or manual_currency
            mb_auto = mb_d.get("auto_settlement")
            log.info("Manual-transfer beneficiary auto_settlement=%s, currency=%s", mb_auto, manual_currency)
            mb_liq = mb_d.get("liquidation_address")
            if mb_liq:
                BENEFICIARY_ID_TO_LIQ_ADDR[manual_beneficiary_id] = mb_liq
                LIQUIDATION_ADDRESSES.add(mb_liq)
                log.info("Manual-transfer beneficiary liquidation_address: %s", mb_liq)
            else:
                log.warning("No liquidation_address for manual-transfer beneficiary yet (sandbox wallet provisioning may be delayed).")
        except Exception:
            pass

        # 20.3 – Create Transfer (transfer-payout)
        manual_transfer_currency = "USDC"
        log.info(">>> 20.3 Transactions – Create a Transfer (currency=%s, auto_settlement=false)", manual_transfer_currency)
        r_mt = api_call(
            "Create a Transfer (Manual)",
            "POST",
            "/v1/transactions/transfer-payout",
            session,
            json_body={
                "beneficiary_id": manual_beneficiary_id,
                "reference_id": "MANUAL-OFFRAMP-REF-1",
                "amount": 500,
                "currency": manual_transfer_currency,
                "remarks": "Manual off-ramp transfer (auto_settlement=false)",
            },
        )
        if r_mt.status_code == 200:
            try:
                mt_data = r_mt.json().get("data") or r_mt.json()
                manual_transfer_id = mt_data.get("transfer_id")
                log.info("Transfer created: transfer_id=%s", manual_transfer_id)
            except Exception:
                manual_transfer_id = None
        elif r_mt.status_code == 422:
            try:
                err_msg = r_mt.json().get("error") or r_mt.json().get("message") or ""
            except Exception:
                err_msg = ""
            if "liquidation address" in str(err_msg).lower():
                log.warning("Transfer-payout blocked: beneficiary liquidation address not yet provisioned (sandbox limitation).")
                log.info("In production, the liquidation address is provisioned at beneficiary creation time.")
            elif "unsupported" in str(err_msg).lower():
                log.warning("Transfer-payout blocked: sandbox does not support this currency for transfer-payout.")
            else:
                log.warning("Create Transfer (Manual) 422: %s", err_msg)
        else:
            log.warning("Create Transfer (Manual) failed with status %s.", r_mt.status_code)

        # 20.4 – Settle Transfer
        if manual_transfer_id:
            log.info(">>> 20.4 Transactions – Settle a Transfer (transfer_id=%s)", manual_transfer_id)
            r_ms = api_call(
                "Settle a Transfer (Manual)",
                "POST",
                "/v1/transactions/transfer-payout/settle",
                session,
                json_body={"transfer_id": manual_transfer_id},
            )
            if r_ms.status_code == 200:
                try:
                    ms_data = r_ms.json().get("data") or r_ms.json()
                    manual_transaction_id = ms_data.get("transaction_id")
                    log.info("Transfer settled: transaction_id=%s", manual_transaction_id)
                except Exception:
                    manual_transaction_id = None
            else:
                log.warning("Settle Transfer (Manual) failed with status %s.", r_ms.status_code)
        else:
            log.warning("No manual transfer_id; skipping settle.")

        # 20.5 – Transaction Details
        if manual_transaction_id:
            log.info(">>> 20.5 Transactions – Transaction Details (manual)")
            api_call(
                "Transaction Details (Manual)",
                "GET",
                f"/v1/beneficiaries/{manual_beneficiary_id}/transactions/{manual_transaction_id}",
                session,
            )
        else:
            log.warning("No manual transaction_id; skipping Transaction Details.")

        # 20.6 – List Beneficiary Transactions
        log.info(">>> 20.6 Transactions – List Beneficiary Transactions (manual)")
        api_call(
            "List Beneficiary Transactions (Manual)",
            "GET",
            f"/v1/beneficiaries/{manual_beneficiary_id}/transactions",
            session,
            params={"page": 1, "limit": 10},
        )

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
    if LAST_ACCESS_TOKEN:
        log.info("Access token (full): %s", LAST_ACCESS_TOKEN)
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

    # Beneficiary ids summary (if any)
    if BENEFICIARY_IDS:
        log.info("")
        log.info("Beneficiary IDs involved in this run:")
        for bid in BENEFICIARY_IDS:
            log.info("- %s", bid)

    # Your wallet address (from virtual account)
    if MY_WALLET_ADDRESS:
        log.info("")
        log.info("Your wallet address:")
        log.info("  %s", MY_WALLET_ADDRESS)

    # Beneficiary liquidation addresses (for auto_settlement deposit)
    if BENEFICIARY_ID_TO_LIQ_ADDR:
        log.info("")
        log.info("Beneficiary liquidation addresses:")
        for bid, laddr in BENEFICIARY_ID_TO_LIQ_ADDR.items():
            cur = BENEFICIARY_ID_TO_CURRENCY.get(bid, "?")
            log.info("  %s (currency=%s): %s", bid, cur, laddr)
    log.info("")
    log.info(">>> Individual Customer API flow finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
