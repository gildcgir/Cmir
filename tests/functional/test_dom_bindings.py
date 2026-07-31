"""Регрессионные тесты: HTML должен содержать все id, к которым привязывает JS."""
from __future__ import annotations

import re
from pathlib import Path


def _html_ids(html: str) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', html))


def _js_block(js: str, start_marker: str, end_marker: str) -> str:
    start = js.find(start_marker)
    end = js.find(end_marker, start)
    assert start >= 0, f"marker not found: {start_marker}"
    assert end > start, f"end marker not found: {end_marker}"
    return js[start:end]


def _get_element_ids(js: str) -> set[str]:
    return set(re.findall(r'getElementById\("([^"]+)"\)', js))


def _onclick_ids(js: str) -> set[str]:
    return set(re.findall(r'getElementById\("([^"]+)"\)\.onclick', js))


def _bind_click_ids(js: str) -> set[str]:
    return set(re.findall(r'bindClick\("([^"]+)"', js))


def test_admin_bind_events_ids_exist_in_html(web_root: Path):
    html = (web_root / "admin.html").read_text(encoding="utf-8")
    js = (web_root / "js" / "admin.js").read_text(encoding="utf-8")
    block = _js_block(js, "function bindEvents()", "export async function initAdmin")
    html_ids = _html_ids(html)

    required = _bind_click_ids(block) | {
        m for m in _get_element_ids(block)
        if m in {
            "poiSelect", "maskFile", "formAddPoi", "addPoiModal",
        }
    }
    missing = sorted(required - html_ids)
    assert not missing, f"admin.html missing ids referenced in bindEvents: {missing}"


def test_admin_no_raw_onclick_without_bind_helper(web_root: Path):
    """bindEvents должен использовать bindClick, а не голый .onclick на null."""
    js = (web_root / "js" / "admin.js").read_text(encoding="utf-8")
    block = _js_block(js, "function bindEvents()", "export async function initAdmin")
    raw = _onclick_ids(block)
    assert not raw, f"bindEvents still uses raw .onclick for: {raw}"


def test_admin_stats_panel_elements(web_root: Path):
    html = (web_root / "admin.html").read_text(encoding="utf-8")
    for el_id in (
        "panelStats", "btnRefreshStats", "statsCards",
        "statsCameras", "statsTopPois", "statsQuality",
    ):
        assert f'id="{el_id}"' in html, f"admin.html missing #{el_id}"


def test_index_preview_elements(web_root: Path):
    html = (web_root / "index.html").read_text(encoding="utf-8")
    for el_id in (
        "previewVideo", "previewMaskCanvas", "map", "mapView", "poiPanel",
        "consentsList", "consentsSection", "kioskLink",
    ):
        assert f'id="{el_id}"' in html, f"index.html missing #{el_id}"
    assert "Email или телефон" in html


def test_user_js_uses_async_usb_resolve(web_root: Path):
    js = (web_root / "js" / "user.js").read_text(encoding="utf-8")
    assert "resolveUsbDeviceIdAsync" in js
    assert "getPreviewCamera" in js
    assert "renderConsents" in js
    assert "/consent/" in js
    assert "updateKioskLink" in js


def test_live_camera_exports_async_resolve(web_root: Path):
    js = (web_root / "js" / "live-camera.js").read_text(encoding="utf-8")
    assert "export async function resolveUsbDeviceIdAsync" in js
    assert "export async function startMaskedPageCamera" in js
    assert "pickPreferredVideoDevice" in js
    assert "gopro" in js.lower()


def test_performance_page_camera_elements(web_root: Path):
    html = (web_root / "performance.html").read_text(encoding="utf-8")
    js = (web_root / "performance.html").read_text(encoding="utf-8")
    for el_id in (
        "live", "liveMaskCanvas", "liveLabel", "btnRegister",
        "btnStart", "btnStop", "fullName", "phone", "menuItem",
    ):
        assert f'id="{el_id}"' in html, f"performance.html missing #{el_id}"
    assert "startMaskedPageCamera" in js
    assert "getLastFaceSignature" in js
    assert "bindPoi" not in html
    assert "signature-bind" not in html


def test_kiosk_locks_after_registration(web_root: Path):
    html = (web_root / "kiosk" / "index.html").read_text(encoding="utf-8")
    for needle in (
        "lockKioskRegistered",
        "checkExistingRegistration",
        "getLastFaceSignature",
        "getToken",
        "kioskLocked",
        "wireLiveView",
        "panelRegister",
        "face_embeddings",
        "PoseEnrollment",
        "face-enroll.js",
        "enrollBox",
    ):
        assert needle in html, f"kiosk missing {needle}"


def test_face_enroll_module(web_root: Path):
    js = (web_root / "js" / "face-enroll.js").read_text(encoding="utf-8")
    assert "ENROLL_POSES" in js
    assert "PoseEnrollment" in js
    assert "left" in js and "right" in js and "up" in js and "down" in js


def test_user_hides_kiosk_when_consented(web_root: Path):
    js = (web_root / "js" / "user.js").read_text(encoding="utf-8")
    assert "updateKioskLink" in js
    assert "userHasConsent" in js
    assert "face-match" in (web_root / "js" / "live-camera.js").read_text(encoding="utf-8")
    assert "renderConsents" in js


def test_use_cases_doc_exists(web_root: Path):
    docs = web_root.parent.parent / "docs" / "USE_CASES.md"
    text = docs.read_text(encoding="utf-8")
    for uc in ("UC-01", "UC-02", "UC-06", "UC-09", "UC-10"):
        assert uc in text


def test_live_camera_privacy_before_display(web_root: Path):
    js = (web_root / "js" / "live-camera.js").read_text(encoding="utf-8")
    assert "firstDetectDone" in js
    block = js[js.find("drawFrame(ts)") : js.find("function matchFaceTrack")]
    assert "if (this.compositeMode && !this.firstDetectDone) return" in block
    assert "this.ctx.drawImage(video" in block


def test_live_camera_face_filter(web_root: Path):
    js = (web_root / "js" / "live-camera.js").read_text(encoding="utf-8")
    assert "export function isLikelyFaceDetection" in js
    assert "compositeMode" in js
    assert "MIN_MASK_CONFIRM_FRAMES" in js
    assert "blendSignature" in js
    block = js[js.find("drawFrame(ts)") : js.find("function matchFaceTrack")]
    assert "if (ts - this.lastTs < 33) return" not in block
    assert "for (const state of this.faceSmooth.values())" in block


def test_mask_overlay_opaque_backing(web_root: Path):
    js = (web_root / "js" / "mask-preview.js").read_text(encoding="utf-8")
    assert "export function drawDefaultPrivacyBar" in js
    assert "ctx.fillStyle = \"#000\"" in js
    assert "ctx.globalAlpha = 1" in js
    html = (web_root / "kiosk" / "index.html").read_text(encoding="utf-8")
    assert "startMaskedPageCamera" in html


def test_performance_no_sync_resolve_only(web_root: Path):
    html = (web_root / "performance.html").read_text(encoding="utf-8")
    assert "resolveUsbDeviceId(perfCamera)" not in html
    assert "startMaskedPageCamera" in html
