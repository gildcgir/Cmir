"""Функциональные тесты статики веб-приложения."""
from __future__ import annotations


def test_index_has_map(web_root):
    html = (web_root / "index.html").read_text(encoding="utf-8")
    assert 'id="map"' in html
    assert 'id="mapView"' in html
    assert "leaflet" in html.lower()


def test_user_js_exports_init(web_root):
    js = (web_root / "js" / "user.js").read_text(encoding="utf-8")
    assert "export async function initUser" in js
    assert "initMap" in js


def test_live_camera_module(web_root):
    js = (web_root / "js" / "live-camera.js").read_text(encoding="utf-8")
    assert "export class LiveCameraView" in js
    assert "resolveUsbDeviceIdAsync" in js
    assert "ensureCameraPermission" in js


def test_admin_html_loads_admin_js(web_root):
    html = (web_root / "admin.html").read_text(encoding="utf-8")
    assert 'from "./js/admin.js"' in html
    assert 'id="btnRefreshStats"' in html
    assert 'id="panelStats"' in html


def test_index_has_map_status(web_root):
    html = (web_root / "index.html").read_text(encoding="utf-8")
    assert 'id="mapStatus"' in html


def test_map_css_fixed_layout(web_root):
    css = (web_root / "css" / "app.css").read_text(encoding="utf-8")
    assert "#mapView" in css
    assert "position: fixed" in css
    assert ".map-status" in css
