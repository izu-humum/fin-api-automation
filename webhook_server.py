#!/usr/bin/env python3
"""
Webhook listener for Fin.com – handles ALL event types on a single endpoint.

Usage:
  1) Install deps (once):
       python -m pip install flask
  2) Run this server:
       python webhook_server.py
  3) In the Fin dashboard, configure the webhook Target URL to:
       https://<your-public-url>/webhooks
  4) Deposit USDC to the beneficiary's liquidation_address.
  5) Watch this terminal and the log file to see incoming events.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WEBHOOK] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DEBUG_LOG_PATH = Path("/Users/izu/fin-api-collection/.cursor/debug-d693d3.log")
DEBUG_SESSION_ID = "d693d3"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _agent_log(hypothesis_id: str, message: str, data: Dict[str, Any]) -> None:
    # region agent log
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": DEBUG_SESSION_ID,
            "id": f"log_{_now_ms()}_{hypothesis_id}",
            "timestamp": _now_ms(),
            "location": "webhook_server.py:handle_webhook",
            "message": message,
            "data": data,
            "runId": "webhook",
            "hypothesisId": hypothesis_id,
        }
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
    # endregion


@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    """Single handler for ALL Fin.com webhook event types.

    Fin sends all subscribed events to one Target URL. We accept them all,
    log them, and return 200 so Fin marks delivery as successful.
    """
    payload = request.get_json(silent=True) or {}

    event_type = payload.get("event_type") or payload.get("type") or "unknown"
    data = payload.get("data") or payload
    reference_id = payload.get("reference_id") or data.get("reference_id")

    safe_data = {
        "event_type": event_type,
        "reference_id": reference_id,
        "beneficiary_id": data.get("beneficiary_id"),
        "liquidation_address": data.get("liquidation_address"),
        "amount": data.get("amount"),
        "currency": data.get("currency"),
        "status": data.get("status"),
        "tx_hash": data.get("tx_hash") or data.get("transaction_hash"),
        "raw_keys": list(payload.keys()),
    }

    log.info("Event: %s | ref=%s | data_keys=%s", event_type, reference_id, list(data.keys()))
    log.info("Payload: %s", json.dumps(payload, indent=2, default=str)[:2000])

    _agent_log(
        hypothesis_id="webhook_received",
        message=f"Received webhook: {event_type}",
        data=safe_data,
    )

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    log.info("Starting Fin.com webhook listener on port 5050...")
    log.info("Configure Fin webhook Target URL to: https://<your-public-url>/webhooks")
    app.run(host="0.0.0.0", port=5050, debug=False)
