from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any

import requests

from common import init_firebase

KEYWORDS = [
    "billboard",
    "clp",
    "raket",
    "megalight",
    "led",
    "açık hava reklam",
    "kent mobilyaları",
    "durak reklamı",
    "reklam panosu",
    "tanıtım alanı",
]


def normalize_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("items", "records", "results", "data"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
    return []


def record_id(source_id: str, title: str, url: str) -> str:
    raw = source_id or f"{title}|{url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


def main() -> None:
    feed_url = os.environ.get("EKAP_FEED_URL", "").strip()
    organization_id = os.environ.get("ORGANIZATION_ID", "").strip()
    if not feed_url or not organization_id:
        print("EKAP_FEED_URL veya ORGANIZATION_ID tanımlı değil; yasal/verilen veri akışı olmadığı için tarama yapılmadı.")
        return

    headers: dict[str, str] = {"Accept": "application/json"}
    token = os.environ.get("EKAP_FEED_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(feed_url, headers=headers, timeout=45)
    response.raise_for_status()
    records = normalize_records(response.json())
    db = init_firebase()
    matched = 0

    for item in records:
        title = str(item.get("title") or item.get("name") or "").strip()
        description = str(item.get("description") or item.get("summary") or "").strip()
        haystack = f"{title} {description}".lower()
        keyword = next((word for word in KEYWORDS if word in haystack), "")
        if not keyword:
            continue
        source_url = str(item.get("url") or item.get("sourceUrl") or "")
        source_id = str(item.get("id") or item.get("sourceId") or "")
        doc_id = record_id(source_id, title, source_url)
        db.collection("ekapTenders").document(doc_id).set(
            {
                "organizationId": organization_id,
                "no": f"EKAP-{doc_id[:10].upper()}",
                "sourceId": source_id,
                "title": title,
                "municipalityName": item.get("municipality") or item.get("authority") or "",
                "city": item.get("city") or "",
                "district": item.get("district") or "",
                "keyword": keyword,
                "sourceUrl": source_url,
                "publicationDate": item.get("publicationDate") or item.get("publishedAt") or "",
                "deadline": item.get("deadline") or item.get("tenderDate") or "",
                "estimatedValue": item.get("estimatedValue") or 0,
                "status": "Yeni",
                "matched": "Evet",
                "notes": description,
                "isDeleted": False,
                "createdBy": "system_ekap_sync",
                "updatedBy": "system_ekap_sync",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            },
            merge=True,
        )
        matched += 1
    print(f"{matched} uygun EKAP/veri akışı kaydı işlendi.")


if __name__ == "__main__":
    main()
