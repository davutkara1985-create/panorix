from __future__ import annotations

import hashlib
import os
import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from common import init_firebase

SEARCH_BASE_URL = "https://ekapv2.kik.gov.tr/ekap/search/"
SOURCE_NAME = "EKAP Kamu İhale Kurumu - Genel İhale Arama"
DEFAULT_KEYWORDS = [
    "billboard",
    "açık hava reklam",
    "reklam alanı",
    "reklam panosu",
    "durak reklamı",
    "kent mobilyaları",
    "LED ekran",
    "CLP",
    "raket reklam",
    "megalight",
    "tanıtım alanı",
]
KEYWORD_LABELS = {
    "billboard": "Billboard",
    "açık hava reklam": "Açık Hava Reklam",
    "reklam alanı": "Açık Hava Reklam",
    "reklam panosu": "Reklam Panosu",
    "durak reklamı": "Durak Reklamı",
    "kent mobilyaları": "Kent Mobilyaları",
    "led ekran": "LED",
    "clp": "CLP",
    "raket reklam": "Raket",
    "megalight": "Megalight",
    "tanıtım alanı": "Tanıtım Alanı",
}
IKN_RE = re.compile(r"\b(20\d{2})[\/_](\d{3,})\b")
DATE_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})(?:\s+(\d{1,2}):(\d{2}))?\b")
PROVINCES = [
    "ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AMASYA", "ANKARA", "ANTALYA", "ARTVİN",
    "AYDIN", "BALIKESİR", "BİLECİK", "BİNGÖL", "BİTLİS", "BOLU", "BURDUR", "BURSA", "ÇANAKKALE",
    "ÇANKIRI", "ÇORUM", "DENİZLİ", "DİYARBAKIR", "EDİRNE", "ELAZIĞ", "ERZİNCAN", "ERZURUM",
    "ESKİŞEHİR", "GAZİANTEP", "GİRESUN", "GÜMÜŞHANE", "HAKKARİ", "HATAY", "ISPARTA", "MERSİN",
    "İSTANBUL", "İZMİR", "KARS", "KASTAMONU", "KAYSERİ", "KIRKLARELİ", "KIRŞEHİR", "KOCAELİ",
    "KONYA", "KÜTAHYA", "MALATYA", "MANİSA", "KAHRAMANMARAŞ", "MARDİN", "MUĞLA", "MUŞ",
    "NEVŞEHİR", "NİĞDE", "ORDU", "RİZE", "SAKARYA", "SAMSUN", "SİİRT", "SİNOP", "SİVAS",
    "TEKİRDAĞ", "TOKAT", "TRABZON", "TUNCELİ", "ŞANLIURFA", "UŞAK", "VAN", "YOZGAT", "ZONGULDAK",
    "AKSARAY", "BAYBURT", "KARAMAN", "KIRIKKALE", "BATMAN", "ŞIRNAK", "BARTIN", "ARDAHAN",
    "IĞDIR", "YALOVA", "KARABÜK", "KİLİS", "OSMANİYE", "DÜZCE",
]
LABELS = {
    "İhale Detayı",
    "İhale Bilgileri",
    "İhale Tarih - Saati",
    "İhaleyi Yapan İdare Adı",
    "Kapsam",
    "İhale Türü",
    "İhale Usulü",
    "İhale Durumu",
    "İhale İli",
    "İşin Yapılacağı Yer",
    "İhale Yeri",
    "İlan Tarihi",
    "İhale Kayıt Numarası",
    "İKN",
}


@dataclass(frozen=True)
class TenderDetail:
    ikn: str
    title: str
    authority: str
    city: str
    tender_type: str
    procedure: str
    tender_status: str
    tender_date: str
    publication_date: str
    work_place: str
    source_url: str
    source_text: str


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_marks.replace("ı", "i").casefold()


def normalize_ikn(value: str) -> str:
    match = IKN_RE.search(value or "")
    return f"{match.group(1)}/{match.group(2)}" if match else ""


def record_id(ikn: str) -> str:
    return hashlib.sha256(ikn.encode("utf-8")).hexdigest()[:40]


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    repository = os.environ.get("GITHUB_REPOSITORY", "PANORIX/PANORIX")
    contact = os.environ.get("EKAP_CONTACT_EMAIL", "").strip()
    agent = f"PANORIX-EKAP-Monitor/1.0 (+https://github.com/{repository}"
    if contact:
        agent += f"; {contact}"
    agent += ")"
    session.headers.update(
        {
            "User-Agent": agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
            "Cache-Control": "no-cache",
        }
    )
    return session


def get_html(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=(15, 60), allow_redirects=True)
    if response.status_code in (401, 403):
        raise RuntimeError(f"EKAP erişimi reddetti ({response.status_code}). Otomatik tarama durduruldu.")
    if response.status_code == 429:
        raise RuntimeError("EKAP çok fazla istek uyarısı verdi (429). Otomatik tarama durduruldu.")
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and "text" not in content_type:
        raise RuntimeError(f"Beklenmeyen EKAP yanıt türü: {content_type or 'bilinmiyor'}")
    return response.text


def discover_ikns(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: set[str] = set()
    for tag in soup.find_all(href=True):
        href = str(tag.get("href") or "")
        for match in IKN_RE.finditer(href):
            candidates.add(f"{match.group(1)}/{match.group(2)}")
    visible_text = " ".join(soup.stripped_strings)
    for match in IKN_RE.finditer(visible_text):
        candidates.add(f"{match.group(1)}/{match.group(2)}")
    return candidates


def token_list(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    return [normalize_space(item) for item in soup.stripped_strings if normalize_space(item)]


def is_label(value: str) -> bool:
    normalized = normalize_space(value).rstrip(":")
    return normalized in LABELS


def find_value(tokens: list[str], labels: Iterable[str], *, start: int = 0) -> str:
    label_set = {normalize_space(label).rstrip(":") for label in labels}
    for index in range(start, len(tokens)):
        token = normalize_space(tokens[index]).rstrip(":")
        if token not in label_set:
            continue
        for candidate in tokens[index + 1 : index + 6]:
            candidate = normalize_space(candidate)
            if not candidate or is_label(candidate):
                continue
            if candidate in {"Seçiniz", "Hepsini Gör", "Göster"}:
                continue
            return candidate
    return ""


def parse_date(value: str) -> str:
    match = DATE_RE.search(value or "")
    if not match:
        return ""
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return ""


def infer_city(*values: str) -> str:
    combined = " ".join(normalize_space(value).upper() for value in values if value)
    for province in sorted(PROVINCES, key=len, reverse=True):
        if re.search(rf"(?<![A-ZÇĞİÖŞÜ]){re.escape(province)}(?![A-ZÇĞİÖŞÜ])", combined):
            return province.title().replace("İ", "İ")
    return ""


def title_after_detail(tokens: list[str], ikn: str) -> str:
    detail_index = next((i for i, value in enumerate(tokens) if normalize_space(value) == "İhale Detayı"), -1)
    search_start = detail_index + 1 if detail_index >= 0 else 0
    for index in range(search_start, len(tokens)):
        if normalize_ikn(tokens[index]) != ikn:
            continue
        for candidate in tokens[index + 1 : index + 8]:
            candidate = normalize_space(candidate)
            if not candidate or is_label(candidate) or normalize_ikn(candidate):
                continue
            if candidate.lower().startswith("ihale") and len(candidate) < 20:
                continue
            return candidate
    return ""


def parse_detail(html: str, ikn: str, source_url: str) -> TenderDetail:
    tokens = token_list(html)
    detail_index = next((i for i, value in enumerate(tokens) if normalize_space(value) == "İhale Detayı"), 0)
    title = title_after_detail(tokens, ikn)
    authority = find_value(tokens, ["İhaleyi Yapan İdare Adı"], start=detail_index)
    tender_date_raw = find_value(tokens, ["İhale Tarih - Saati"], start=detail_index)
    tender_type = find_value(tokens, ["İhale Türü"], start=detail_index)
    procedure = find_value(tokens, ["İhale Usulü"], start=detail_index)
    tender_status = find_value(tokens, ["İhale Durumu"], start=detail_index)
    city_label = find_value(tokens, ["İhale İli"], start=detail_index)
    work_place = find_value(tokens, ["İşin Yapılacağı Yer"], start=detail_index)
    publication_raw = find_value(tokens, ["İlan Tarihi"], start=detail_index)
    source_text = normalize_space(" ".join(tokens[detail_index : detail_index + 100]))[:8000]
    city = city_label or infer_city(authority, work_place, source_text)
    return TenderDetail(
        ikn=ikn,
        title=title,
        authority=authority,
        city=city,
        tender_type=tender_type,
        procedure=procedure,
        tender_status=tender_status,
        tender_date=parse_date(tender_date_raw),
        publication_date=parse_date(publication_raw),
        work_place=work_place,
        source_url=source_url,
        source_text=source_text,
    )


def should_keep(detail: TenderDetail) -> bool:
    status = fold_text(detail.tender_status)
    if any(term in status for term in ("iptal", "sonuç", "sözleşme imzalandı", "tamamlandı")):
        return False
    return bool(detail.title or detail.authority)


def get_keywords() -> list[str]:
    raw = os.environ.get("EKAP_KEYWORDS", "").strip()
    if not raw:
        return DEFAULT_KEYWORDS
    return [normalize_space(item) for item in raw.split("|") if normalize_space(item)]


def write_sync_status(db, organization_id: str, **values) -> None:
    payload = {
        "status": values.get("status", "unknown"),
        "source": SOURCE_NAME,
        "lastRunAt": datetime.now(timezone.utc),
        "checkedKeywordCount": values.get("checked_keyword_count", 0),
        "successfulKeywordCount": values.get("successful_keyword_count", 0),
        "discoveredIknCount": values.get("discovered_ikn_count", 0),
        "matchedCount": values.get("matched_count", 0),
        "newCount": values.get("new_count", 0),
        "updatedCount": values.get("updated_count", 0),
        "errors": list(values.get("errors", []))[:10],
    }
    db.collection("settings").document(organization_id).set(
        {"organizationId": organization_id, "ekapSync": payload}, merge=True
    )


def active_recipient_ids(db, organization_id: str) -> list[str]:
    recipients: list[str] = []
    for snapshot in db.collection("users").where("organizationId", "==", organization_id).stream():
        data = snapshot.to_dict() or {}
        if data.get("active") is True and data.get("isDeleted") is not True:
            recipients.append(snapshot.id)
    return recipients


def create_summary_notification(db, organization_id: str, new_count: int, total_count: int) -> None:
    if new_count <= 0:
        return
    recipients = active_recipient_ids(db, organization_id)
    if not recipients:
        return
    now = datetime.now(timezone.utc)
    notification_id = f"ekap_sync_{now.strftime('%Y%m%d_%H%M%S')}"
    db.collection("notifications").document(notification_id).set(
        {
            "organizationId": organization_id,
            "recipientIds": recipients,
            "readBy": [],
            "type": "İhale",
            "title": f"{new_count} yeni EKAP ilanı bulundu",
            "message": f"Otomatik EKAP taramasında {total_count} uygun kayıt işlendi. EKAP Takip sayfasını kontrol edin.",
            "sourceModule": "ekapTenders",
            "isDeleted": False,
            "createdBy": "system_ekap_sync",
            "updatedBy": "system_ekap_sync",
            "createdAt": now,
            "updatedAt": now,
        }
    )


def upsert_tender(db, organization_id: str, detail: TenderDetail, keywords: list[str]) -> bool:
    doc_id = record_id(detail.ikn)
    ref = db.collection("ekapTenders").document(doc_id)
    snapshot = ref.get()
    now = datetime.now(timezone.utc)
    canonical_keywords = [KEYWORD_LABELS.get(fold_text(item), item) for item in keywords]
    matched_keyword = canonical_keywords[0] if canonical_keywords else ""
    source_fields = {
        "organizationId": organization_id,
        "no": f"EKAP-{detail.ikn.replace('/', '-')}",
        "sourceId": detail.ikn,
        "ikn": detail.ikn,
        "title": detail.title or f"EKAP İlanı {detail.ikn}",
        "municipalityName": detail.authority,
        "city": detail.city,
        "district": "",
        "keyword": matched_keyword,
        "matchedKeywords": canonical_keywords,
        "sourceUrl": detail.source_url,
        "sourceName": SOURCE_NAME,
        "publicationDate": detail.publication_date,
        "deadline": detail.tender_date,
        "tenderType": detail.tender_type,
        "procedure": detail.procedure,
        "sourceStatus": detail.tender_status,
        "workPlace": detail.work_place,
        "matched": "Evet",
        "lastSeenAt": now,
        "updatedBy": "system_ekap_sync",
        "updatedAt": now,
        "isDeleted": False,
    }
    if snapshot.exists:
        ref.set(source_fields, merge=True)
        return False

    notes = " • ".join(
        part
        for part in (
            detail.tender_status,
            detail.tender_type,
            detail.procedure,
            detail.work_place,
        )
        if part
    )
    ref.set(
        {
            **source_fields,
            "estimatedValue": 0,
            "status": "Yeni",
            "assignedTo": "",
            "notes": notes,
            "createdBy": "system_ekap_sync",
            "createdAt": now,
        }
    )
    return True


def main() -> None:
    organization_id = os.environ.get("ORGANIZATION_ID", "panorix").strip() or "panorix"
    max_records = max(1, min(int(os.environ.get("EKAP_MAX_RECORDS", "100")), 300))
    request_delay = max(1.0, float(os.environ.get("EKAP_REQUEST_DELAY_SECONDS", "2")))
    keywords = get_keywords()
    db = init_firebase()
    session = build_session()

    discovered: dict[str, set[str]] = defaultdict(set)
    errors: list[str] = []
    successful_keywords = 0

    for keyword in keywords:
        url = urljoin(SEARCH_BASE_URL, quote(keyword, safe=""))
        try:
            html = get_html(session, url)
            successful_keywords += 1
            found_ikns = discover_ikns(html)
            for ikn in found_ikns:
                discovered[ikn].add(keyword)
            print(f"[EKAP] '{keyword}' sorgusu: {len(found_ikns)} İKN bulundu.")
        except Exception as exc:  # noqa: BLE001 - workflow summary must continue on partial source errors
            message = f"{keyword}: {exc}"
            errors.append(message)
            print(f"[EKAP][UYARI] {message}")
        time.sleep(request_delay)

    if successful_keywords == 0:
        write_sync_status(
            db,
            organization_id,
            status="error",
            checked_keyword_count=len(keywords),
            successful_keyword_count=0,
            errors=errors or ["EKAP sorgularının tamamı başarısız oldu."],
        )
        raise RuntimeError("EKAP sorgularının tamamı başarısız oldu. GitHub Actions kayıtlarını kontrol edin.")

    new_count = 0
    updated_count = 0
    matched_count = 0
    for ikn in sorted(discovered)[:max_records]:
        detail_url = urljoin(SEARCH_BASE_URL, ikn.replace("/", "_"))
        try:
            detail_html = get_html(session, detail_url)
            detail = parse_detail(detail_html, ikn, detail_url)
            if not should_keep(detail):
                continue
            is_new = upsert_tender(db, organization_id, detail, sorted(discovered[ikn]))
            matched_count += 1
            if is_new:
                new_count += 1
            else:
                updated_count += 1
            print(f"[EKAP] {'YENİ' if is_new else 'GÜNCELLENDİ'}: {ikn} - {detail.title[:100]}")
        except Exception as exc:  # noqa: BLE001 - one malformed tender must not stop the complete run
            message = f"{ikn}: {exc}"
            errors.append(message)
            print(f"[EKAP][UYARI] {message}")
        time.sleep(request_delay)

    status = "success" if not errors else "partial"
    write_sync_status(
        db,
        organization_id,
        status=status,
        checked_keyword_count=len(keywords),
        successful_keyword_count=successful_keywords,
        discovered_ikn_count=len(discovered),
        matched_count=matched_count,
        new_count=new_count,
        updated_count=updated_count,
        errors=errors,
    )
    create_summary_notification(db, organization_id, new_count, matched_count)
    print(
        f"[EKAP] Tamamlandı. Durum={status}, bulunan İKN={len(discovered)}, "
        f"işlenen={matched_count}, yeni={new_count}, güncellenen={updated_count}."
    )


if __name__ == "__main__":
    main()
