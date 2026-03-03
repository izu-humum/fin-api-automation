#!/usr/bin/env python3
"""
Fin.com API – Full Business Account flow automation.

Preconfigured for business customer:
- Customer ID: fa4d375d-2cce-42df-9bd4-dc9dc2136818
- Customer Name: QA Alliance
- Customer Email: humam.izu@gmail.com

Usage:
  ./run_business_account_flow.py

You can still override via env:
  export FIN_CLIENT_ID="your_client_id"
  export FIN_CLIENT_SECRET="your_client_secret"
  export FIN_CUSTOMER_ID="your_customer_uuid"
  export FIN_CUSTOMER_NAME="Your Name"
  export FIN_CUSTOMER_EMAIL="your@email"
"""

from run_individual_account_flow import main as _base_main  # type: ignore
import os


def main() -> int:
    # Override customer-specific defaults for this flow
    os.environ.setdefault("FIN_CUSTOMER_ID", "fa4d375d-2cce-42df-9bd4-dc9dc2136818")
    os.environ.setdefault("FIN_CUSTOMER_NAME", "QA Alliance")
    os.environ.setdefault("FIN_CUSTOMER_EMAIL", "humam.izu@gmail.com")
    # Reuse the existing full flow logic
    return _base_main()


if __name__ == "__main__":
    raise SystemExit(main())

