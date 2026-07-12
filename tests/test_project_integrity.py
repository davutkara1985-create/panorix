from __future__ import annotations

import json
import py_compile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_files_exist() -> None:
    required = [
        "app.py",
        "index.html",
        "logo.png",
        "background.png",
        "firestore.rules",
        "storage.rules",
        "firestore.indexes.json",
        "firebase.json",
        ".streamlit/config.toml",
        ".streamlit/secrets.toml.example",
    ]
    missing = [name for name in required if not (ROOT / name).exists()]
    assert not missing, f"Eksik dosyalar: {missing}"


def test_python_files_compile() -> None:
    files = [ROOT / "app.py", *sorted((ROOT / "jobs").glob("*.py"))]
    for path in files:
        py_compile.compile(str(path), doraise=True)


def test_json_files_are_valid() -> None:
    for name in ("firebase.json", "firestore.indexes.json"):
        with (ROOT / name).open(encoding="utf-8") as handle:
            json.load(handle)


def test_panorix_modules_are_present() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    required_tokens = [
        'municipalities:"municipalities"',
        'tenders:"tenders"',
        'ekapTenders:"ekapTenders"',
        'billboards:"billboards"',
        'customers:"customers"',
        'leads:"leads"',
        'offers:"offers"',
        'reservations:"reservations"',
        'contracts:"contracts"',
        'documents:"documents"',
        'invoices:"invoices"',
        'payments:"payments"',
        'expenses:"expenses"',
        'operations:"operations"',
        'tasks:"tasks"',
        'vehicles:"vehicles"',
        'competitors:"competitors"',
        'messages:"messages"',
        'notifications:"notifications"',
    ]
    missing = [token for token in required_tokens if token not in html]
    assert not missing, f"Eksik modül tanımları: {missing}"


def test_reference_design_assets_are_used() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'src="logo.png"' in html
    assert 'url("background.png")' in html
    assert "app-bg.png" not in html
    assert "login-bg.jpg" not in html
    assert "logo.jpg" not in html


def test_local_storage_and_old_brand_are_removed() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "localStorage" not in html
    assert "EVENTIX" not in html
    assert "SD Kongre" not in html


def test_no_real_secret_in_repository() -> None:
    allowed_example = ROOT / ".streamlit" / "secrets.toml.example"
    text = allowed_example.read_text(encoding="utf-8")
    assert "-----BEGIN PRIVATE KEY-----" not in text

    patterns = [
        re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
        re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ]
    for path in ROOT.rglob("*"):
        if "tests" in path.parts:
            continue
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip", ".pyc", ".md"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            assert not pattern.search(content), f"Olası gerçek sır bulundu: {path}"


def test_service_account_is_not_sent_to_frontend() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "firebase_service_account" not in html
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'for static_name in ("index.html", "logo.png", "background.png")' in app


def test_security_rules_have_tenant_isolation_and_default_deny() -> None:
    rules = (ROOT / "firestore.rules").read_text(encoding="utf-8")
    assert "function sameOrganization" in rules
    assert "function validCreate" in rules
    assert "function validUpdate" in rules
    assert "allow read, write: if false;" in rules
    for collection in (
        "municipalities",
        "tenders",
        "ekapTenders",
        "billboards",
        "customers",
        "leads",
        "offers",
        "reservations",
        "contracts",
        "documents",
        "invoices",
        "payments",
        "expenses",
        "operations",
        "tasks",
        "vehicles",
        "competitors",
    ):
        assert f"match /{collection}/{{id}}" in rules


def test_storage_rules_are_scoped() -> None:
    rules = (ROOT / "storage.rules").read_text(encoding="utf-8")
    assert "organizations/{orgId}/{module}/{recordId}/{fileName}" in rules
    assert "request.auth.token.organizationId == orgId" in rules
    assert "20 * 1024 * 1024" in rules
    assert "allow read, write: if false;" in rules


def test_browser_integrations_and_exports_are_wired() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for token in (
        "firebase-app-compat.js",
        "firebase-auth-compat.js",
        "firebase-firestore-compat.js",
        "firebase-storage-compat.js",
        "xlsx.full.min.js",
        "function exportCsv(key)",
        "function loadOpenStreetMap()",
        "leaflet.markercluster",
        "function geocodeBillboard(data,old)",
        "function ekapSyncPanelHtml()",
        'id="loginFormWrap"',
    ):
        assert token in html


def test_sensitive_workflow_imports_are_blocked() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert '["reservations","contracts","payments","billboards"].includes(key)' in html
    assert "iş akışı ve çakışma kontrolleri" in html


def test_no_demo_or_interactive_bootstrap_account() -> None:
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    secrets = (ROOT / ".streamlit" / "secrets.toml.example").read_text(encoding="utf-8")

    forbidden = [
        "BOOTSTRAP_CODE",
        "bootstrap_super_admin",
        "showBootstrap",
        "bootstrapSuperAdmin",
        "demo@",
        "PanorixDemo",
    ]
    combined = "\n".join([app, html, secrets])
    for token in forbidden:
        assert token not in combined

    assert "INITIAL_ADMIN_EMAIL" in app
    assert "INITIAL_ADMIN_PASSWORD" in app
    assert "initial_admin_status" in app
    assert 'INITIAL_ADMIN_EMAIL = "davutkara1985@gmail.com"' in secrets


def test_real_initial_admin_password_is_not_committed() -> None:
    sensitive_fragment = "".join(["Panorix", "213"])
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip", ".pyc"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert sensitive_fragment not in content, f"Yönetici parolası repository içinde bulundu: {path}"


def test_billboard_address_is_geocoded_on_save() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'await geocodeBillboard(data,old)' in html
    assert 'backendCall("geocode_address"' in html
    assert 'nominatim.openstreetmap.org/search' in app
    assert 'countrycodes' in app
    assert 'OpenStreetMap Nominatim' in app
