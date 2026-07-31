"""Имена потоков MediaMTX для мест и камер."""
from __future__ import annotations

RTMP_HOST = "127.0.0.1"
RTMP_PORT = 1935
HLS_HOST = "127.0.0.1"
HLS_PORT = 8888


def poi_stream_name(poi_id: str) -> str:
    return "poi_" + poi_id.replace("-", "")


def poi_rtmp_url(poi_id: str) -> str:
    return f"rtmp://{RTMP_HOST}:{RTMP_PORT}/{poi_stream_name(poi_id)}"


def poi_hls_url(poi_id: str) -> str:
    return f"http://{HLS_HOST}:{HLS_PORT}/{poi_stream_name(poi_id)}/index.m3u8"


def poi_masked_hls_url(poi_id: str) -> str:
    return f"http://{HLS_HOST}:{HLS_PORT}/{poi_stream_name(poi_id)}_avatar/index.m3u8"


def hls_proxy_url(stream_rel: str, api_port: int = 8090) -> str:
    """Same-origin HLS через API (обход cookie MediaMTX в браузере)."""
    rel = stream_rel.lstrip("/")
    return f"http://127.0.0.1:{api_port}/api/v1/hls/{rel}"


def poi_hls_proxy_url(poi_id: str, api_port: int = 8090) -> str:
    return hls_proxy_url(f"{poi_stream_name(poi_id)}/index.m3u8", api_port)


def poi_masked_hls_proxy_url(poi_id: str, api_port: int = 8090) -> str:
    return hls_proxy_url(f"{poi_stream_name(poi_id)}_avatar/index.m3u8", api_port)


def hls_direct_to_proxy(direct_url: str | None, api_port: int = 8090) -> str | None:
    """http://127.0.0.1:8888/gopro_main/index.m3u8 → API-прокси."""
    if not direct_url:
        return None
    from urllib.parse import urlparse

    parsed = urlparse(direct_url)
    rel = parsed.path.lstrip("/")
    if parsed.query:
        rel += "?" + parsed.query
    return hls_proxy_url(rel, api_port)


def stream_url_to_hls(stream_url: str, poi_id: str = "") -> str | None:
    if not stream_url:
        return None
    if stream_url.startswith("local://") and poi_id:
        return poi_hls_url(poi_id)
    if stream_url.startswith("rtmp://"):
        from urllib.parse import urlparse

        path = urlparse(stream_url).path.strip("/")
        if not path:
            return None
        host = urlparse(stream_url).hostname or HLS_HOST
        return f"http://{host}:{HLS_PORT}/{path}/index.m3u8"
    if "8554/" in stream_url:
        from urllib.parse import urlparse

        path = stream_url.split("8554/", 1)[1].split("?")[0].strip("/")
        host = urlparse(stream_url).hostname or HLS_HOST
        return f"http://{host}:{HLS_PORT}/{path}/index.m3u8"
    if stream_url.endswith(".m3u8"):
        return stream_url
    return None


def masked_stream_hls(stream_url: str, poi_id: str = "") -> str | None:
    if stream_url.startswith("local://") and poi_id:
        return poi_masked_hls_url(poi_id)
    if stream_url.startswith("rtmp://"):
        from urllib.parse import urlparse

        path = urlparse(stream_url).path.strip("/")
        if not path:
            return None
        host = urlparse(stream_url).hostname or HLS_HOST
        if path.endswith("_main"):
            masked = path[:-5] + "_avatar"
        else:
            masked = path + "_avatar"
        return f"http://{host}:{HLS_PORT}/{masked}/index.m3u8"
    if "8554/" not in stream_url:
        return None
    from urllib.parse import urlparse

    path = stream_url.split("8554/", 1)[1].split("?")[0].strip("/")
    if path.endswith("_main"):
        masked = path[:-5] + "_avatar"
    elif path == "gopro_main":
        masked = "gopro_avatar"
    else:
        masked = path + "_masked"
    host = urlparse(stream_url).hostname or HLS_HOST
    return f"http://{host}:{HLS_PORT}/{masked}/index.m3u8"


def hls_playlist_ready(url: str, timeout: float = 2.0) -> bool:
    if not url:
        return False
    import http.cookiejar
    import urllib.error
    import urllib.request
    from urllib.parse import urljoin

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        with opener.open(url, timeout=timeout) as resp:
            chunk = resp.read(256)
            return b"EXTM3U" in chunk
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            loc = e.headers["Location"]
            if loc.startswith("/"):
                loc = urljoin(url, loc)
            try:
                with opener.open(loc, timeout=timeout) as resp:
                    return b"EXTM3U" in resp.read(256)
            except (urllib.error.URLError, OSError, TimeoutError, urllib.error.HTTPError):
                return False
        if e.code == 404:
            return False
        try:
            return b"EXTM3U" in e.read(256)
        except Exception:
            return False
    except (urllib.error.URLError, OSError, TimeoutError):
        return False
