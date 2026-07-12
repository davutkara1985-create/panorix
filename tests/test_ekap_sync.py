from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    fake_common = types.ModuleType("common")
    fake_common.init_firebase = lambda: None
    sys.modules["common"] = fake_common
    spec = importlib.util.spec_from_file_location("panorix_ekap_sync", ROOT / "jobs" / "ekap_sync.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_discover_ikns_from_public_search_html() -> None:
    module = load_module()
    html = """
    <html><body>
      <a href="/ekap/search/2026_1095497">2026/1095497 BAHÇE MAKİNELERİ</a>
      <a href="/ekap/ihale-detay?ikn=2026%2F774580">2026/774580</a>
      <div>İKN: 2026/888888</div>
    </body></html>
    """
    assert module.discover_ikns(html) == {"2026/1095497", "2026/774580", "2026/888888"}


def test_parse_detail_from_public_ekap_labels() -> None:
    module = load_module()
    html = """
    <html><body>
      <h2>İhale Detayı</h2>
      <div>2026/1095497</div>
      <h1>BILLBOARD VE AÇIK HAVA REKLAM ALANLARININ KİRALANMASI</h1>
      <div>İhale Bilgileri</div>
      <div>İhale Tarih - Saati</div><div>13.07.2026 10:00</div>
      <div>İhaleyi Yapan İdare Adı</div><div>ÖRNEK BELEDİYE BAŞKANLIĞI - ANKARA</div>
      <div>İhale Türü</div><div>Hizmet</div>
      <div>İhale Usulü</div><div>Açık İhale</div>
      <div>İhale Durumu</div><div>İhale İlanı Yayımlanmış, Katılıma Açık</div>
      <div>İşin Yapılacağı Yer</div><div>Çankaya / Ankara</div>
    </body></html>
    """
    detail = module.parse_detail(
        html,
        "2026/1095497",
        "https://ekapv2.kik.gov.tr/ekap/search/2026_1095497",
    )
    assert detail.ikn == "2026/1095497"
    assert detail.title == "BILLBOARD VE AÇIK HAVA REKLAM ALANLARININ KİRALANMASI"
    assert detail.authority == "ÖRNEK BELEDİYE BAŞKANLIĞI - ANKARA"
    assert detail.city == "Ankara"
    assert detail.tender_type == "Hizmet"
    assert detail.procedure == "Açık İhale"
    assert detail.tender_date == "2026-07-13"
    assert module.should_keep(detail) is True


def test_result_and_cancelled_status_filter() -> None:
    module = load_module()
    open_detail = module.TenderDetail(
        ikn="2026/1",
        title="Açık hava reklam alanları",
        authority="Belediye",
        city="Ankara",
        tender_type="Hizmet",
        procedure="Açık İhale",
        tender_status="Katılıma Açık",
        tender_date="2026-07-13",
        publication_date="",
        work_place="Ankara",
        source_url="https://example.invalid",
        source_text="",
    )
    cancelled = module.TenderDetail(**{**open_detail.__dict__, "tender_status": "İhale İptal Edildi"})
    assert module.should_keep(open_detail) is True
    assert module.should_keep(cancelled) is False


def test_workflow_uses_public_search_without_feed_secrets() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ekap-sync.yml").read_text(encoding="utf-8")
    assert "PANORIX Otomatik EKAP Takibi" in workflow
    assert "EKAP_FEED_URL" not in workflow
    assert "EKAP_FEED_TOKEN" not in workflow
    assert "ORGANIZATION_ID" in workflow
    assert "FIREBASE_SERVICE_ACCOUNT_JSON" in workflow


def test_ui_has_ekap_sync_status_panel() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "function ekapSyncPanelHtml()" in html
    assert 'key==="ekapTenders"?await ekapSyncPanelHtml()' in html
    assert "Otomatik EKAP Takibi" in html
