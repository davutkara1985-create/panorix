from __future__ import annotations

import json
import os
from typing import Any

from firebase_admin import credentials, firestore, get_app, initialize_app


def init_firebase() -> firestore.Client:
    try:
        get_app()
    except ValueError:
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        if not raw:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON GitHub Secret tanımlı değil.")
        service_account: dict[str, Any] = json.loads(raw)
        if "private_key" in service_account:
            service_account["private_key"] = str(service_account["private_key"]).replace("\\n", "\n")
        initialize_app(credentials.Certificate(service_account))
    return firestore.client()
