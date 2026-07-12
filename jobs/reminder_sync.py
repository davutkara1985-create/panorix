from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from typing import Any, Iterable

from common import init_firebase

ALERT_DAYS = {365, 180, 90, 30, 7, 1, 0}


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            pass
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def notification_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:40]


def active_user_ids(db, organization_id: str) -> list[str]:
    query = db.collection("users").where("organizationId", "==", organization_id).where("active", "==", True)
    return [doc.id for doc in query.stream() if not (doc.to_dict() or {}).get("isDeleted")]


def upsert_notification(
    db,
    *,
    organization_id: str,
    recipients: list[str],
    category: str,
    record_id: str,
    title: str,
    message: str,
    target_date: date,
    days_left: int,
) -> None:
    if not recipients:
        return
    nid = notification_id(organization_id, category, record_id, target_date.isoformat(), str(days_left))
    db.collection("notifications").document(nid).set(
        {
            "organizationId": organization_id,
            "recipientIds": recipients,
            "readBy": [],
            "type": category,
            "title": title,
            "message": message,
            "recordId": record_id,
            "targetDate": target_date.isoformat(),
            "daysLeft": days_left,
            "isDeleted": False,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
        },
        merge=True,
    )


def organization_ids(db) -> Iterable[str]:
    seen: set[str] = set()
    for doc in db.collection("users").stream():
        data = doc.to_dict() or {}
        org = str(data.get("organizationId") or "")
        if org and org not in seen:
            seen.add(org)
            yield org


def process_collection(db, org: str, recipients: list[str], collection: str, fields: list[tuple[str, str, str]]) -> int:
    count = 0
    for snap in db.collection(collection).where("organizationId", "==", org).stream():
        data = snap.to_dict() or {}
        if data.get("isDeleted"):
            continue
        for field, category, label in fields:
            target = parse_date(data.get(field))
            if not target:
                continue
            days = (target - date.today()).days
            if days not in ALERT_DAYS:
                continue
            name = data.get("title") or data.get("invoiceNo") or data.get("plate") or data.get("no") or snap.id
            upsert_notification(
                db,
                organization_id=org,
                recipients=recipients,
                category=category,
                record_id=snap.id,
                title=f"{label}: {name}",
                message=f"{target.strftime('%d.%m.%Y')} tarihine {days} gün kaldı.",
                target_date=target,
                days_left=days,
            )
            count += 1
    return count


def main() -> None:
    db = init_firebase()
    total = 0
    for org in organization_ids(db):
        recipients = active_user_ids(db, org)
        total += process_collection(
            db,
            org,
            recipients,
            "tenders",
            [("tenderDate", "İhale", "Yaklaşan ihale"), ("guaranteeEndDate", "Teminat", "Teminat süresi")],
        )
        total += process_collection(db, org, recipients, "contracts", [("endDate", "Sözleşme", "Sözleşme bitişi")])
        total += process_collection(db, org, recipients, "invoices", [("dueDate", "Tahsilat", "Fatura vadesi")])
        total += process_collection(db, org, recipients, "tasks", [("dueDate", "Görev", "Görev hedefi")])
        total += process_collection(
            db,
            org,
            recipients,
            "vehicles",
            [
                ("insuranceEnd", "Araç", "Sigorta bitişi"),
                ("inspectionEnd", "Araç", "Muayene bitişi"),
                ("cascoEnd", "Araç", "Kasko bitişi"),
                ("nextMaintenance", "Araç", "Bakım tarihi"),
            ],
        )
    print(f"{total} hatırlatma kontrol edildi/oluşturuldu.")


if __name__ == "__main__":
    main()
