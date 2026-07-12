from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shutil
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from firebase_admin import auth, credentials, firestore, get_app, initialize_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import qrcode


APP_TITLE = "PANORIX"
APP_SLOGAN = "Şehir Reklamlarının Tüm Gücü Tek Merkezde"


_GEOCODE_LOCK = threading.Lock()
_GEOCODE_LAST_REQUEST = 0.0
_GEOCODE_CACHE: dict[str, dict[str, Any]] = {}


def _geocode_address(payload: dict[str, Any]) -> dict[str, Any]:
    """Resolve one user-submitted Turkish address with the public Nominatim API.

    The call is made only when the user saves a billboard record. Results are
    stored in Firestore with the billboard, so the same address is not queried
    on every map view.
    """
    raw_address = str(payload.get("address") or "").strip()
    if len(raw_address) < 8:
        raise ValueError(
            "Harita konumu bulunabilmesi için açık adres, ilçe ve il bilgilerini eksiksiz girin."
        )

    normalized = " ".join(raw_address.split()).casefold()
    cached = _GEOCODE_CACHE.get(normalized)
    if cached:
        return cached

    params = urllib.parse.urlencode(
        {
            "q": raw_address,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "tr",
            "addressdetails": 1,
            "accept-language": "tr",
        }
    )
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    app_url = str(_secret("APP_PUBLIC_URL", "") or "https://streamlit.io").strip()
    contact = str(_secret("INITIAL_ADMIN_EMAIL", "") or "admin@panorix.local").strip()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"PANORIX/1.0 ({app_url}; contact: {contact})",
            "Accept": "application/json",
            "Accept-Language": "tr",
            "Referer": app_url if app_url.startswith(("http://", "https://")) else "",
        },
    )

    global _GEOCODE_LAST_REQUEST
    with _GEOCODE_LOCK:
        wait_seconds = 1.05 - (time.monotonic() - _GEOCODE_LAST_REQUEST)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(
                "Adres harita servisinde aranamadı. İnternet bağlantısını kontrol edip tekrar deneyin."
            ) from exc
        finally:
            _GEOCODE_LAST_REQUEST = time.monotonic()

    if not isinstance(data, list) or not data:
        raise ValueError(
            "Adres haritada bulunamadı. Mahalle, cadde/sokak, bina numarası, ilçe ve il bilgilerini kontrol edin."
        )

    item = data[0]
    try:
        latitude = float(item["lat"])
        longitude = float(item["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Harita servisi geçerli bir koordinat döndürmedi.") from exc

    result = {
        "latitude": latitude,
        "longitude": longitude,
        "displayName": str(item.get("display_name") or raw_address),
        "source": "OpenStreetMap Nominatim",
    }
    _GEOCODE_CACHE[normalized] = result
    return result


ALLOWED_ROLES = {
    "super_admin",
    "admin",
    "manager",
    "sales_manager",
    "sales_rep",
    "accounting",
    "operations_manager",
    "operations_staff",
    "field_staff",
    "guest",
}

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
html, body, .stApp, [data-testid="stAppViewContainer"] {
    width: 100vw !important;
    height: 100vh !important;
    min-height: 100dvh !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"], footer, #MainMenu {
    display: none !important;
}
[data-testid="stIFrame"], iframe {
    display: block !important;
    width: 100vw !important;
    min-width: 100vw !important;
    height: 100vh !important;
    height: 100dvh !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    border: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.stApp, .main, .block-container, section.main,
div[data-testid="stVerticalBlock"], div[data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    border: 0 !important;
    background: transparent !important;
}
div[data-testid="stIFrame"] {
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
[data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"],
section[data-testid="stSidebar"], section.main, main, .stMain,
.stAppViewContainer, .stMainBlockContainer {
    margin: 0 !important;
    padding: 0 !important;
    width: 100vw !important;
    max-width: 100vw !important;
    height: 100vh !important;
    height: 100dvh !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    overflow: hidden !important;
}
iframe[title="panorix_erp"] {
    width: 100vw !important;
    height: 100vh !important;
    height: 100dvh !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def _secret(name: str, default: Any = "") -> Any:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def _section(name: str) -> dict[str, Any]:
    try:
        value = st.secrets.get(name, {})
        return dict(value) if value else {}
    except Exception:
        return {}


def _firebase_web_config() -> dict[str, str]:
    section = _section("firebase_web")
    return {
        "apiKey": str(section.get("api_key", "")),
        "authDomain": str(section.get("auth_domain", "")),
        "projectId": str(section.get("project_id", "")),
        "storageBucket": str(section.get("storage_bucket", "")),
        "messagingSenderId": str(section.get("messaging_sender_id", "")),
        "appId": str(section.get("app_id", "")),
        "measurementId": str(section.get("measurement_id", "")),
    }


def _service_account_dict() -> dict[str, Any]:
    section = _section("firebase_service_account")
    if not section:
        raw = str(_secret("FIREBASE_SERVICE_ACCOUNT_JSON", "") or "").strip()
        if raw:
            try:
                section = json.loads(raw)
            except json.JSONDecodeError:
                return {}
    if "private_key" in section:
        section["private_key"] = str(section["private_key"]).replace("\\n", "\n")
    return section


def _firebase_admin_ready() -> bool:
    try:
        get_app()
        return True
    except ValueError:
        service_account = _service_account_dict()
        if not service_account:
            return False
        initialize_app(credentials.Certificate(service_account))
        return True


def _verify_id_token(token: str) -> dict[str, Any]:
    if not token:
        raise PermissionError("Kimlik doğrulama jetonu bulunamadı.")
    if not _firebase_admin_ready():
        raise RuntimeError("Firebase Service Account yapılandırılmamış.")
    return auth.verify_id_token(token, check_revoked=True)


def _db() -> firestore.Client:
    if not _firebase_admin_ready():
        raise RuntimeError("Firebase Service Account yapılandırılmamış.")
    return firestore.client()


def _profile(uid: str) -> dict[str, Any]:
    snap = _db().collection("users").document(uid).get()
    if not snap.exists:
        return {}
    return {"id": snap.id, **(snap.to_dict() or {})}


def _assert_admin(decoded: dict[str, Any]) -> dict[str, Any]:
    uid = str(decoded.get("uid", ""))
    profile = _profile(uid)
    if not profile or profile.get("isDeleted") or not profile.get("active", True):
        raise PermissionError("Aktif kullanıcı profili bulunamadı.")
    if profile.get("role") not in {"super_admin", "admin"}:
        raise PermissionError("Bu işlem için yönetici yetkisi gerekir.")
    return profile


def _audit(
    *,
    uid: str,
    organization_id: str,
    user_name: str,
    action: str,
    module: str,
    record_id: str,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
) -> None:
    _db().collection("auditLogs").add(
        {
            "organizationId": organization_id,
            "userId": uid,
            "userName": user_name,
            "action": action,
            "module": module,
            "recordId": record_id,
            "oldData": old_data or {},
            "newData": new_data or {},
            "source": "streamlit_admin_bridge",
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
    )


def _initial_admin_config() -> dict[str, str]:
    return {
        "email": str(_secret("INITIAL_ADMIN_EMAIL", "") or "").strip().lower(),
        "password": str(_secret("INITIAL_ADMIN_PASSWORD", "") or ""),
        "full_name": str(_secret("INITIAL_ADMIN_NAME", "Davut Kara") or "Davut Kara").strip(),
        "organization_name": str(_secret("INITIAL_ORGANIZATION_NAME", "PANORIX") or "PANORIX").strip(),
        "organization_id": str(_secret("INITIAL_ORGANIZATION_ID", "") or "").strip(),
    }


def _ensure_initial_admin() -> dict[str, Any]:
    config = _initial_admin_config()
    email = config["email"]
    if not email:
        return {
            "ok": False,
            "configured": False,
            "message": "INITIAL_ADMIN_EMAIL Streamlit Secrets içinde tanımlanmamış.",
        }
    if not _firebase_admin_ready():
        return {
            "ok": False,
            "configured": True,
            "email": email,
            "message": "Firebase Service Account yapılandırılmamış.",
        }

    created_auth_user = False
    try:
        user_record = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        password = config["password"]
        if len(password) < 8:
            return {
                "ok": False,
                "configured": True,
                "email": email,
                "message": "İlk yönetici Firebase kullanıcısı bulunamadı. INITIAL_ADMIN_PASSWORD alanını Streamlit Secrets içinde tanımlayın.",
            }
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=config["full_name"],
            disabled=False,
        )
        created_auth_user = True

    if user_record.disabled:
        user_record = auth.update_user(user_record.uid, disabled=False)

    database = _db()
    profile_ref = database.collection("users").document(user_record.uid)
    profile_snap = profile_ref.get()
    profile = profile_snap.to_dict() or {} if profile_snap.exists else {}

    active_super_admins = []
    for snap in database.collection("users").where("role", "==", "super_admin").stream():
        data = snap.to_dict() or {}
        if not data.get("isDeleted") and data.get("active", True):
            active_super_admins.append((snap.id, data))
    foreign_super_admins = [item for item in active_super_admins if item[0] != user_record.uid]
    if foreign_super_admins:
        return {
            "ok": False,
            "configured": True,
            "email": email,
            "message": "Başka bir aktif Super Admin hesabı bulundu. Otomatik yönetici oluşturma durduruldu.",
        }

    organization_id = str(profile.get("organizationId") or config["organization_id"])
    if not organization_id:
        organization_id = "org_" + hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]
    organization_name = str(profile.get("organizationName") or config["organization_name"] or "PANORIX")
    full_name = str(profile.get("fullName") or config["full_name"] or email.split("@")[0])

    current_claims = dict(user_record.custom_claims or {})
    desired_claims = {
        **current_claims,
        "role": "super_admin",
        "organizationId": organization_id,
        "isSuperAdmin": True,
    }
    claims_changed = any(current_claims.get(key) != value for key, value in desired_claims.items())
    if claims_changed:
        auth.set_custom_user_claims(user_record.uid, desired_claims)

    profile_requires_update = (
        not profile_snap.exists
        or profile.get("email") != email
        or profile.get("fullName") != full_name
        or profile.get("role") != "super_admin"
        or profile.get("organizationId") != organization_id
        or profile.get("organizationName") != organization_name
        or profile.get("active") is not True
        or profile.get("isDeleted") is True
        or profile.get("isSuperAdmin") is not True
    )
    if profile_requires_update:
        profile_ref.set(
            {
                "email": email,
                "fullName": full_name,
                "role": "super_admin",
                "organizationId": organization_id,
                "organizationName": organization_name,
                "active": True,
                "isDeleted": False,
                "isSuperAdmin": True,
                "permissions": profile.get("permissions", {}),
                "createdAt": profile.get("createdAt", firestore.SERVER_TIMESTAMP),
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    settings_ref = database.collection("settings").document(organization_id)
    settings_snap = settings_ref.get()
    if not settings_snap.exists:
        settings_ref.set(
            {
                "organizationId": organization_id,
                "organizationName": organization_name,
                "currency": "TRY",
                "economy": {},
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    if created_auth_user or not profile_snap.exists:
        _audit(
            uid=user_record.uid,
            organization_id=organization_id,
            user_name=full_name,
            action="initial_super_admin_created",
            module="users",
            record_id=user_record.uid,
            new_data={"email": email, "role": "super_admin", "organizationId": organization_id},
        )

    return {
        "ok": True,
        "configured": True,
        "email": email,
        "created": created_auth_user or not profile_snap.exists,
        "message": "İlk Super Admin hesabı hazır.",
    }

def _admin_create_user(decoded: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    caller = _assert_admin(decoded)
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    full_name = str(payload.get("fullName", "")).strip()
    role = str(payload.get("role", "guest"))
    if role not in ALLOWED_ROLES:
        raise ValueError("Geçersiz kullanıcı rolü.")
    if not email or not password or not full_name:
        raise ValueError("E-posta, ad soyad ve geçici şifre zorunludur.")
    if len(password) < 8:
        raise ValueError("Geçici şifre en az 8 karakter olmalıdır.")
    if role == "super_admin" and caller.get("role") != "super_admin":
        raise PermissionError("Super Admin rolünü yalnız mevcut Super Admin verebilir.")

    organization_id = str(caller.get("organizationId", ""))
    record = auth.create_user(email=email, password=password, display_name=full_name, disabled=False)
    try:
        auth.set_custom_user_claims(
            record.uid,
            {
                "role": role,
                "organizationId": organization_id,
                "isSuperAdmin": role == "super_admin",
            },
        )
    except Exception:
        auth.delete_user(record.uid)
        raise
    user_data = {
        "email": email,
        "fullName": full_name,
        "role": role,
        "organizationId": organization_id,
        "organizationName": caller.get("organizationName", ""),
        "department": str(payload.get("department", "")),
        "title": str(payload.get("title", "")),
        "phone": str(payload.get("phone", "")),
        "active": True,
        "isDeleted": False,
        "isSuperAdmin": role == "super_admin",
        "permissions": payload.get("permissions") or {},
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    try:
        _db().collection("users").document(record.uid).set(user_data)
    except Exception:
        auth.delete_user(record.uid)
        raise
    _audit(
        uid=str(decoded["uid"]),
        organization_id=organization_id,
        user_name=str(caller.get("fullName", "")),
        action="create",
        module="users",
        record_id=record.uid,
        new_data={k: v for k, v in user_data.items() if k not in {"createdAt", "updatedAt"}},
    )
    return {"uid": record.uid, "message": "Kullanıcı oluşturuldu."}


def _admin_update_user(decoded: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    caller = _assert_admin(decoded)
    target_uid = str(payload.get("uid", ""))
    if not target_uid:
        raise ValueError("Kullanıcı kimliği eksik.")
    old = _profile(target_uid)
    if not old:
        raise ValueError("Kullanıcı profili bulunamadı.")
    if old.get("organizationId") != caller.get("organizationId"):
        raise PermissionError("Başka bir şirketin kullanıcısı güncellenemez.")
    if old.get("isSuperAdmin") and caller.get("role") != "super_admin":
        raise PermissionError("Super Admin hesabı yalnız Super Admin tarafından güncellenebilir.")

    new_role = str(payload.get("role") or old.get("role") or "guest")
    if new_role not in ALLOWED_ROLES:
        raise ValueError("Geçersiz kullanıcı rolü.")
    if old.get("isSuperAdmin") and new_role != "super_admin":
        raise PermissionError("Super Admin rolü kaldırılamaz.")
    if new_role == "super_admin" and caller.get("role") != "super_admin":
        raise PermissionError("Super Admin rolünü yalnız Super Admin verebilir.")

    email = str(payload.get("email") or old.get("email") or "").strip().lower()
    full_name = str(payload.get("fullName") or old.get("fullName") or "").strip()
    auth.update_user(target_uid, email=email or None, display_name=full_name or None)
    claims = {
        "role": new_role,
        "organizationId": old.get("organizationId") or caller.get("organizationId"),
        "isSuperAdmin": new_role == "super_admin",
    }
    auth.set_custom_user_claims(target_uid, claims)
    update_data = {
        "email": email,
        "fullName": full_name,
        "role": new_role,
        "department": str(payload.get("department", old.get("department", ""))),
        "title": str(payload.get("title", old.get("title", ""))),
        "phone": str(payload.get("phone", old.get("phone", ""))),
        "permissions": payload.get("permissions") if isinstance(payload.get("permissions"), dict) else old.get("permissions", {}),
        "isSuperAdmin": new_role == "super_admin",
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    _db().collection("users").document(target_uid).set(update_data, merge=True)
    _audit(
        uid=str(decoded["uid"]),
        organization_id=str(old.get("organizationId", "")),
        user_name=str(caller.get("fullName", "")),
        action="update",
        module="users",
        record_id=target_uid,
        old_data={k: old.get(k) for k in update_data if k != "updatedAt"},
        new_data={k: v for k, v in update_data.items() if k != "updatedAt"},
    )
    return {"message": "Kullanıcı güncellendi."}


def _admin_toggle_user(decoded: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    caller = _assert_admin(decoded)
    target_uid = str(payload.get("uid", ""))
    active = bool(payload.get("active", True))
    old = _profile(target_uid)
    if not old:
        raise ValueError("Kullanıcı bulunamadı.")
    if old.get("organizationId") != caller.get("organizationId"):
        raise PermissionError("Başka bir şirketin kullanıcısı değiştirilemez.")
    if old.get("isSuperAdmin") and not active:
        raise PermissionError("Super Admin pasife alınamaz.")
    if target_uid == decoded.get("uid") and not active:
        raise PermissionError("Aktif oturumdaki kullanıcı pasife alınamaz.")
    auth.update_user(target_uid, disabled=not active)
    _db().collection("users").document(target_uid).set(
        {"active": active, "updatedAt": firestore.SERVER_TIMESTAMP}, merge=True
    )
    if not active:
        auth.revoke_refresh_tokens(target_uid)
    _audit(
        uid=str(decoded["uid"]),
        organization_id=str(old.get("organizationId", "")),
        user_name=str(caller.get("fullName", "")),
        action="activate" if active else "deactivate",
        module="users",
        record_id=target_uid,
        old_data={"active": old.get("active", True)},
        new_data={"active": active},
    )
    return {"message": "Kullanıcı durumu güncellendi."}


def _admin_soft_delete_user(decoded: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    caller = _assert_admin(decoded)
    target_uid = str(payload.get("uid", ""))
    old = _profile(target_uid)
    if not old:
        raise ValueError("Kullanıcı bulunamadı.")
    if old.get("organizationId") != caller.get("organizationId"):
        raise PermissionError("Başka bir şirketin kullanıcısı silinemez.")
    if old.get("isSuperAdmin"):
        raise PermissionError("Super Admin silinemez.")
    if target_uid == decoded.get("uid"):
        raise PermissionError("Aktif oturumdaki kullanıcı silinemez.")
    auth.update_user(target_uid, disabled=True)
    auth.revoke_refresh_tokens(target_uid)
    _db().collection("users").document(target_uid).set(
        {
            "active": False,
            "isDeleted": True,
            "deletedAt": firestore.SERVER_TIMESTAMP,
            "deletedBy": decoded.get("uid"),
            "updatedAt": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )
    _audit(
        uid=str(decoded["uid"]),
        organization_id=str(old.get("organizationId", "")),
        user_name=str(caller.get("fullName", "")),
        action="soft_delete",
        module="users",
        record_id=target_uid,
        old_data={"active": old.get("active"), "isDeleted": old.get("isDeleted")},
        new_data={"active": False, "isDeleted": True},
    )
    return {"message": "Kullanıcı pasife alınarak arşivlendi."}


def _register_font() -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("PanorixFont", path))
                return "PanorixFont"
            except Exception:
                continue
    return "Helvetica"


def _pdf_report(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title") or "PANORIX Raporu")[:150]
    subtitle = str(payload.get("subtitle") or "")[:300]
    columns = payload.get("columns") or []
    rows = payload.get("rows") or []
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ValueError("PDF verisi geçersiz.")
    columns = columns[:14]
    rows = rows[:1000]

    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    font_name = _register_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PanorixTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F4C81"),
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        "PanorixBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=7.5,
        leading=9,
    )
    story: list[Any] = [Paragraph(title, title_style)]
    if subtitle:
        story.extend([Spacer(1, 2 * mm), Paragraph(subtitle, body_style)])
    story.append(Spacer(1, 5 * mm))

    header = [Paragraph(str(col.get("label", col.get("key", ""))), body_style) for col in columns]
    table_data = [header]
    for row in rows:
        table_data.append(
            [Paragraph(str(row.get(str(col.get("key", "")), "-")), body_style) for col in columns]
        )
    if not table_data[0]:
        table_data = [[Paragraph("Kayıt bulunamadı.", body_style)]]
    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF4FC")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DFE3E8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    data = base64.b64encode(output.getvalue()).decode("ascii")
    return {"filename": str(payload.get("filename") or "panorix-rapor.pdf"), "base64": data}



def _generate_qr(payload: dict[str, Any]) -> dict[str, Any]:
    url = str(payload.get("url") or "").strip()
    if not url.startswith(("https://", "http://")):
        raise ValueError("QR bağlantısı geçersiz.")
    image = qrcode.make(url)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return {
        "filename": str(payload.get("filename") or "panorix-qr.png"),
        "base64": base64.b64encode(output.getvalue()).decode("ascii"),
        "url": url,
    }

def _handle_backend_request(value: object) -> None:
    if not isinstance(value, dict) or value.get("type") != "backend_request":
        return
    request_id = str(value.get("requestId") or "")
    if not request_id:
        return

    processed = st.session_state.setdefault("processed_backend_request_ids", [])
    if request_id in processed:
        return

    action = str(value.get("action") or "")
    payload = value.get("payload") or {}
    token = str(value.get("idToken") or "")
    response: dict[str, Any]
    try:
        decoded = _verify_id_token(token)
        if action == "admin_create_user":
            result = _admin_create_user(decoded, payload)
        elif action == "admin_update_user":
            result = _admin_update_user(decoded, payload)
        elif action == "admin_toggle_user":
            result = _admin_toggle_user(decoded, payload)
        elif action == "admin_soft_delete_user":
            result = _admin_soft_delete_user(decoded, payload)
        elif action == "generate_pdf":
            result = _pdf_report(payload)
        elif action == "generate_qr":
            result = _generate_qr(payload)
        elif action == "geocode_address":
            result = _geocode_address(payload)
        else:
            raise ValueError("Desteklenmeyen sunucu işlemi.")
        response = {"type": "backend_response", "requestId": request_id, "ok": True, "result": result}
    except Exception as exc:
        response = {"type": "backend_response", "requestId": request_id, "ok": False, "error": str(exc)}

    processed.append(request_id)
    st.session_state["processed_backend_request_ids"] = processed[-50:]
    st.session_state["backend_response"] = response
    st.rerun()


project_dir = Path(__file__).parent.resolve()
component_dir = Path(tempfile.gettempdir()) / "panorix_component_frontend"
component_dir.mkdir(parents=True, exist_ok=True)
for static_name in ("index.html", "logo.png", "background.png"):
    source = project_dir / static_name
    target = component_dir / static_name
    if not source.exists():
        raise FileNotFoundError(f"Gerekli arayüz dosyası bulunamadı: {static_name}")
    if not target.exists() or source.stat().st_mtime_ns != target.stat().st_mtime_ns or source.stat().st_size != target.stat().st_size:
        shutil.copy2(source, target)

panorix_component = components.declare_component("panorix_erp", path=str(component_dir))
try:
    firebase_admin_available = _firebase_admin_ready()
except Exception as exc:
    firebase_admin_available = False
    initial_admin_status = {
        "ok": False,
        "configured": True,
        "message": f"Firebase Admin başlatılamadı: {exc}",
    }
else:
    try:
        initial_admin_status = _ensure_initial_admin()
    except Exception as exc:
        initial_admin_status = {
            "ok": False,
            "configured": True,
            "message": f"İlk yönetici hesabı hazırlanamadı: {exc}",
        }

component_value = panorix_component(
    key="panorix_erp",
    default=None,
    firebase_config=_firebase_web_config(),
    app_public_url=str(_secret("APP_PUBLIC_URL", "") or ""),
    deep_link_billboard=str(st.query_params.get("billboard", "") or ""),
    app_name=APP_TITLE,
    app_slogan=APP_SLOGAN,
    initial_admin_email=str(_secret("INITIAL_ADMIN_EMAIL", "") or "").strip().lower(),
    initial_admin_status=initial_admin_status,
    session_timeout_minutes=int(_secret("SESSION_TIMEOUT_MINUTES", 60) or 60),
    backend_available=firebase_admin_available,
    backend_response=st.session_state.get("backend_response"),
)
_handle_backend_request(component_value)
