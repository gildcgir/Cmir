"""Unit-тесты логики разрешения USB device id (парсинг из JS-совместимых данных)."""
from __future__ import annotations


def device_id_from_camera(cam: dict) -> str:
    if cam.get("device_id"):
        return cam["device_id"]
    url = cam.get("stream_url") or ""
    if url.startswith("local://"):
        return url[8:]
    return ""


def test_device_id_from_device_id_field():
    assert device_id_from_camera({"device_id": "abc-123"}) == "abc-123"


def test_device_id_from_local_stream_url():
    assert device_id_from_camera({"stream_url": "local://usb-cam-1"}) == "usb-cam-1"


def test_device_id_empty():
    assert device_id_from_camera({}) == ""
    assert device_id_from_camera({"stream_url": "rtsp://x"}) == ""


def test_preview_camera_selection():
    """Логика getPreviewCamera: general preview, затем любая активная."""
    pois_cams = [
        {"id": "1", "role": "consent", "is_active": True, "is_preview": False},
        {"id": "2", "role": "general", "is_active": True, "is_preview": True},
        {"id": "3", "role": "performance", "is_active": True, "is_preview": False},
    ]

    def get_preview_camera(cameras):
        active = [c for c in cameras if c.get("is_active")]
        general = [c for c in active if c.get("role") == "general"]
        return (
            next((c for c in general if c.get("is_preview")), None)
            or (general[0] if general else None)
            or next((c for c in active if c.get("is_preview")), None)
            or (active[0] if active else None)
        )

    cam = get_preview_camera(pois_cams)
    assert cam["id"] == "2"

    only_perf = [{"id": "p", "role": "performance", "is_active": True, "is_preview": True}]
    assert get_preview_camera(only_perf)["id"] == "p"
