import { API, api, getToken, setToken } from "./api.js";

let map, markers = [], pois = [], hlsPreview = null, selectedPoi = null;
let previewRetryTimer = null, previewAttempt = 0;
let activeStreamPoi = null;
let liveView = null;
let liveCameraMod = null;
let phonePreviewStream = null;
/** Invalidates in-flight startPoiPreview after close / tab hide. */
let previewEpoch = 0;

const ASSET_V = "camfix10";
let hostRecorder = null;
let hostRecordChunks = [];
const HOST_RECORD_MAX_MS = 5 * 60 * 1000;

function currentUserId() {
  try {
    return JSON.parse(localStorage.getItem("cmir_user") || "{}")?.id || "";
  } catch (_) {
    return "";
  }
}

function isPlaceOwner(poi) {
  const uid = currentUserId();
  return !!(poi?.submitted_by && uid && poi.submitted_by === uid);
}

function updateHostBroadcastUi(poi) {
  const btn = document.getElementById("btnEndBroadcast");
  if (!btn) return;
  const show = !!(poi && isPlaceOwner(poi) && poi.status !== "lingering" && poi.status !== "pending");
  btn.hidden = !show;
}

function stopHostRecorder() {
  return new Promise((resolve) => {
    if (!hostRecorder || hostRecorder.state === "inactive") {
      hostRecorder = null;
      resolve(null);
      return;
    }
    hostRecorder.onstop = () => {
      const type = hostRecorder?.mimeType || "video/webm";
      const blob = hostRecordChunks.length ? new Blob(hostRecordChunks, { type }) : null;
      hostRecorder = null;
      hostRecordChunks = [];
      resolve(blob);
    };
    try {
      hostRecorder.stop();
    } catch (_) {
      hostRecorder = null;
      hostRecordChunks = [];
      resolve(null);
    }
  });
}

function startHostRecorderFromVideo(video) {
  stopHostRecorder();
  const stream = video?.srcObject;
  if (!stream || typeof MediaRecorder === "undefined") return;
  hostRecordChunks = [];
  let mime = "";
  for (const c of ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"]) {
    if (MediaRecorder.isTypeSupported?.(c)) {
      mime = c;
      break;
    }
  }
  try {
    hostRecorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
  } catch (_) {
    return;
  }
  const started = Date.now();
  hostRecorder.ondataavailable = (ev) => {
    if (ev.data && ev.data.size > 0) hostRecordChunks.push(ev.data);
    // Drop oldest chunks roughly beyond 5 minutes (timeslice 5s → keep ~60)
    while (hostRecordChunks.length > 64) hostRecordChunks.shift();
    if (Date.now() - started > HOST_RECORD_MAX_MS + 15000 && hostRecordChunks.length > 70) {
      hostRecordChunks = hostRecordChunks.slice(-60);
    }
  };
  try {
    hostRecorder.start(5000);
  } catch (_) {
    hostRecorder = null;
  }
}

async function endHostBroadcast(poi) {
  if (!poi?.id || !getToken()) return;
  setPreviewStatus("Завершение трансляции…");
  const blob = await stopHostRecorder();
  try {
    let data;
    if (blob && blob.size > 1000) {
      const fd = new FormData();
      fd.append("clip", blob, "linger.webm");
      const res = await fetch(`${API}/api/v1/pois/${poi.id}/broadcast/end`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: fd,
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "end failed");
      data = json.data;
    } else {
      data = (await api("POST", `/api/v1/pois/${poi.id}/broadcast/end`, {})).data;
    }
    selectedPoi = data;
    updateHostBroadcastUi(data);
    await startPoiPreview(data);
    setPreviewStatus(
      data.linger_until
        ? "Трансляция завершена. Точка на карте ещё ~30 мин с записью последних минут."
        : "Трансляция завершена.",
    );
    loadPois().catch(() => {});
  } catch (e) {
    setPreviewStatus(e.message || "Не удалось завершить трансляцию");
  }
}

function isCmirAndroid() {
  return /CmirAndroid/i.test(navigator.userAgent || "");
}

async function ensureLiveCamera() {
  if (!liveCameraMod) {
    liveCameraMod = await import(`./live-camera.js?v=${ASSET_V}`);
  }
  return liveCameraMod;
}

const els = {
  tabMap: () => document.getElementById("tabMap"),
  mapView: () => document.getElementById("mapView"),
  accountView: () => document.getElementById("accountView"),
  poiPanel: () => document.getElementById("poiPanel"),
  panelTitle: () => document.getElementById("panelTitle"),
  panelAddr: () => document.getElementById("panelAddr"),
  panelComment: () => document.getElementById("panelComment"),
  panelPreviewStatus: () => document.getElementById("panelPreviewStatus"),
  previewVideo: () => document.getElementById("previewVideo"),
  authGuest: () => document.getElementById("authGuest"),
  authUser: () => document.getElementById("authUser"),
  authStatus: () => document.getElementById("authStatus"),
  authMsg: () => document.getElementById("authMsg"),
  adminLink: () => document.getElementById("adminLink"),
};

function getClientId() {
  let id = sessionStorage.getItem("cmir_client_id");
  if (!id) {
    id = globalThis.crypto?.randomUUID?.() || `c-${Date.now()}`;
    sessionStorage.setItem("cmir_client_id", id);
  }
  return id;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function showView(name) {
  if (name !== "map" && selectedPoi) {
    closePoiPanel();
  }
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll(".tab-btn[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === name);
  });
  const tabMap = els.tabMap();
  if (tabMap) tabMap.style.display = "";
  const target = document.getElementById(name === "map" ? "mapView" : "accountView");
  if (target) target.classList.add("active");
  if (name === "map" && map) {
    requestAnimationFrame(() => {
      map.invalidateSize();
      setTimeout(() => map?.invalidateSize(), 120);
      setTimeout(() => map?.invalidateSize(), 400);
    });
  }
}

function initMap() {
  const L = globalThis.L;
  if (!L) {
    throw new Error("Leaflet не загружен");
  }
  const el = document.getElementById("map");
  if (!el) throw new Error("Элемент #map не найден");
  if (map) {
    map.remove();
    map = null;
  }
  // Icons next to local leaflet.css
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconUrl: "vendor/leaflet/images/marker-icon.png",
    iconRetinaUrl: "vendor/leaflet/images/marker-icon-2x.png",
    shadowUrl: "vendor/leaflet/images/marker-shadow.png",
  });
  map = L.map(el, { zoomControl: true, preferCanvas: true }).setView([41.7151, 44.8271], 12);
  // Local HTTP tile proxy — Android WebView often fails HTTPS CDN handshakes
  const tileUrl = `${API}/api/v1/map-tiles/{z}/{x}/{y}.png`;
  const tiles = L.tileLayer(tileUrl, {
    attribution: "© OpenStreetMap © CARTO",
    maxZoom: 19,
  });
  tiles.addTo(map);
  map.on("click", (e) => {
    if (typeof window.__cmirOnMapClick === "function" && window.__cmirOnMapClick(e.latlng)) {
      return;
    }
  });
  setTimeout(() => map?.invalidateSize(), 50);
  setTimeout(() => map?.invalidateSize(), 300);
}

function clearMarkers() {
  markers.forEach((m) => map.removeLayer(m));
  markers = [];
}

function showMapStatus(msg, isError = false) {
  const el = document.getElementById("mapStatus");
  if (!el) return;
  el.textContent = msg || "";
  el.classList.toggle("map-status--err", !!(msg && isError));
  el.style.display = msg ? "block" : "none";
}

async function loadPois() {
  if (!map) return;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 8000);
    let res;
    try {
      res = await fetch(`${API}/api/v1/pois`, { signal: ctrl.signal });
    } finally {
      clearTimeout(t);
    }
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || res.statusText);
    pois = json.data || [];
    clearMarkers();
    pois.forEach((poi) => {
      const lat = Number(poi.latitude);
      const lon = Number(poi.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      const m = globalThis.L.marker([lat, lon])
        .addTo(map)
        .bindTooltip(poi.name, { permanent: false })
        .on("click", () => openPoiPanel(poi));
      markers.push(m);
    });
    if (pois.length && !selectedPoi && markers.length) {
      const bounds = globalThis.L.featureGroup(markers).getBounds();
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.2));
    }
    if (selectedPoi) {
      const fresh = pois.find((p) => p.id === selectedPoi.id);
      if (fresh) selectedPoi = fresh;
    }
    if (!pois.length) {
      showMapStatus(
        "Нет мест на карте. Запустите lab: cd cmir && bash scripts/start-lab.sh",
        true,
      );
    } else {
      showMapStatus("");
    }
  } catch (e) {
    console.error("loadPois failed:", e);
    // Don't overwrite a working map with a sticky false alarm (transient reverse/fetch blips)
    if (markers.length || pois.length) return;
    const why = e?.name === "AbortError" ? "таймаут" : (e.message || "ошибка");
    showMapStatus(
      `Нет связи с lab (${API}, ${why}). Подключите USB и на Mac: adb reverse tcp:3000 tcp:3000 && adb reverse tcp:8090 tcp:8090`,
      true,
    );
  }
}

let viewTimer = null, viewCameraId = null;

function getPreviewCamera(poi) {
  const active = (poi?.cameras || []).filter((c) => c.is_active);
  const general = active.filter((c) => c.role === "general");
  return general.find((c) => c.is_preview) || general[0]
    || active.find((c) => c.is_preview) || active[0] || null;
}

function usbFallbackCams(poi, primary) {
  return (poi?.cameras || []).filter(
    (c) => c.is_active && c.id !== primary?.id && (c.source_type === "local_usb" || c.device_id || (c.stream_url || "").startsWith("local://")),
  );
}

function facingFromPoiCam(poi, cam) {
  if (poi?.facing_mode === "environment" || poi?.facing_mode === "user") return poi.facing_mode;
  const url = cam?.stream_url || "";
  if (/facing\/environment/i.test(url)) return "environment";
  if (/facing\/user/i.test(url)) return "user";
  const label = `${cam?.device_label || ""} ${cam?.name || ""}`;
  if (/back|rear|environment|задн/i.test(label)) return "environment";
  return "user";
}

function setPreviewStatus(msg) {
  const el = els.panelPreviewStatus();
  if (el) el.textContent = msg || "";
}

function stopViewTracking() {
  if (viewTimer) { clearInterval(viewTimer); viewTimer = null; }
  viewCameraId = null;
}

async function releaseStream(poiId, { force = false } = {}) {
  if (!poiId) return;
  try {
    await api("POST", `/api/v1/pois/${poiId}/stream/release`, {
      client_id: getClientId(),
      force,
    });
  } catch (_) {}
  if (activeStreamPoi === poiId) activeStreamPoi = null;
}

function stopPreview() {
  previewEpoch += 1;
  stopHostRecorder();
  if (previewRetryTimer) { clearTimeout(previewRetryTimer); previewRetryTimer = null; }
  stopClipPoll();
  stopViewTracking();
  if (liveView) {
    liveView.stop();
    liveView = null;
  }
  if (phonePreviewStream) {
    phonePreviewStream.getTracks().forEach((t) => t.stop());
    phonePreviewStream = null;
  }
  if (hlsPreview) {
    hlsPreview.destroy();
    hlsPreview = null;
  }
  const v = els.previewVideo();
  const canvas = document.getElementById("previewMaskCanvas");
  if (canvas) {
    canvas.style.display = "";
    canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
  }
  if (v) {
    // Critical: clearing srcObject alone does NOT release the hardware camera
    const orphan = v.srcObject;
    if (orphan?.getTracks) {
      orphan.getTracks().forEach((t) => t.stop());
    }
    v.pause();
    v.removeAttribute("src");
    v.srcObject = null;
    v.classList.add("live-source-hidden");
    v.loop = false;
    v.load();
  }
}

function previewStillWanted(poi, epoch) {
  return (
    epoch === previewEpoch
    && selectedPoi
    && selectedPoi.id === poi.id
    && !!els.poiPanel()?.classList.contains("open")
    && document.visibilityState !== "hidden"
  );
}

/** Front camera with same privacy overlay as desktop site (local MediaPipe). */
async function startDeviceCameraPreview({ facingMode = "user", poi = null, cam = null, epoch = previewEpoch } = {}) {
  const video = els.previewVideo();
  const canvas = document.getElementById("previewMaskCanvas");
  if (!video || !canvas) throw new Error("Нет video/canvas для превью");
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("getUserMedia недоступен");
  }
  if (!previewStillWanted(poi || selectedPoi, epoch)) return;

  const mod = await ensureLiveCamera();
  if (!previewStillWanted(poi || selectedPoi, epoch)) return;
  const { LiveCameraView } = mod;
  liveView?.stop();
  liveView = new LiveCameraView(video, canvas);
  canvas.style.display = "";
  const maskUrl = poi?.mask_image_url ? `${API}${poi.mask_image_url}` : "";
  await liveView.start({
    facingMode,
    maskImageUrl: maskUrl,
    apiBase: API,
    cameraId: cam?.id || "",
    compositeMode: true,
  });
  if (!previewStillWanted(poi || selectedPoi, epoch)) {
    liveView?.stop();
    liveView = null;
    return;
  }
  liveView.onRecognized = null;
  setPreviewStatus(
    facingMode === "user"
      ? "Фронтальная камера · маски и подписи"
      : "Камера устройства · маски и подписи",
  );
}

async function tryDeviceCameraFallback(poi = null, cam = null, epoch = previewEpoch) {
  try {
    if (!previewStillWanted(poi, epoch)) return false;
    const facing = facingFromPoiCam(poi, cam);
    setPreviewStatus(
      facing === "environment"
        ? "Подключение задней камеры с масками…"
        : "Подключение фронтальной камеры с масками…",
    );
    await startDeviceCameraPreview({ facingMode: facing, poi, cam, epoch });
    if (!previewStillWanted(poi, epoch)) return false;
    previewAttempt = 0;
    return !!liveView;
  } catch (e) {
    console.error("device camera fallback failed:", e);
    liveView?.stop();
    liveView = null;
    if (previewStillWanted(poi, epoch)) {
      setPreviewStatus(`Камера/маски недоступны: ${e.message || e}`);
    }
    return false;
  }
}

async function closePoiPanel() {
  const poiId = selectedPoi?.id || activeStreamPoi;
  setPoiChatOpen(false);
  els.poiPanel().classList.remove("open");
  els.mapView()?.classList.remove("panel-open");
  stopPreview();
  stopPoiChat();
  setPreviewStatus("");
  selectedPoi = null;
  previewAttempt = 0;
  setTimeout(() => map?.invalidateSize(), 50);
  if (poiId) await releaseStream(poiId, { force: false });
}

function startViewTracking(cameraId) {
  stopViewTracking();
  if (!getToken() || !cameraId) return;
  viewCameraId = cameraId;
  viewTimer = setInterval(async () => {
    try {
      await api("POST", "/api/v1/views", { camera_id: viewCameraId, seconds: 30, ad_revenue: 0.02 });
    } catch (_) {}
  }, 30000);
}

function liveUrls(pb) {
  const d = pb.data || {};
  return [...new Set([d.masked_hls_url, d.live_hls_url].filter(Boolean))];
}

function hlsConfig() {
  return {
    lowLatencyMode: false,
    manifestLoadingTimeOut: 25000,
    manifestLoadingMaxRetry: 8,
    levelLoadingTimeOut: 25000,
    fragLoadingTimeOut: 25000,
    maxBufferLength: 30,
  };
}

function tryHlsUrl(video, url, camId, { trackViews = false } = {}) {
  return new Promise((resolve) => {
    if (!window.Hls || !Hls.isSupported()) {
      if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = url;
        video.loop = false;
        video.play().then(() => {
          if (trackViews) startViewTracking(camId);
          resolve(true);
        }).catch(() => resolve(false));
        return;
      }
      resolve(false);
      return;
    }
    const hls = new Hls(hlsConfig());
    let settled = false;
    const done = (ok) => {
      if (settled) return;
      settled = true;
      if (!ok) {
        hls.destroy();
        resolve(false);
        return;
      }
      if (hlsPreview && hlsPreview !== hls) hlsPreview.destroy();
      hlsPreview = hls;
      resolve(true);
    };
    hls.loadSource(url);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      video.loop = false;
      video.play().then(() => {
        if (trackViews) {
          setPreviewStatus("");
          startViewTracking(camId);
        }
        done(true);
      }).catch(() => done(false));
    });
    hls.on(Hls.Events.ERROR, (_, data) => {
      if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
        hls.startLoad();
        return;
      }
      if (data.fatal) done(false);
    });
    setTimeout(() => done(false), 18000);
  });
}

async function fetchPlayback(cam) {
  const cid = encodeURIComponent(getClientId());
  return api("GET", `/api/v1/cameras/${cam.id}/playback?client_id=${cid}`);
}

function resolveClipUrl(clipUrl) {
  if (!clipUrl) return "";
  if (clipUrl.startsWith("http")) return clipUrl;
  return `${API}${clipUrl}`;
}

function switchToPreviewClip(clipUrl) {
  if (hlsPreview) {
    hlsPreview.destroy();
    hlsPreview = null;
  }
  if (liveView) {
    liveView.stop();
    liveView = null;
  }
  const canvas = document.getElementById("previewMaskCanvas");
  if (canvas) {
    canvas.style.display = "none";
    canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
  }
  const video = els.previewVideo();
  video.classList.remove("live-source-hidden");
  video.loop = true;
  video.srcObject = null;
  video.src = `${resolveClipUrl(clipUrl)}?t=${Date.now()}`;
  video.play().catch(() => {});
  setPreviewStatus("Превью: 10 с записи с эфира (зациклено)");
}

let clipPollTimer = null;

function stopClipPoll() {
  if (clipPollTimer) {
    clearTimeout(clipPollTimer);
    clipPollTimer = null;
  }
}

function pollPreviewClipSwitch(poi) {
  stopClipPoll();
  const poll = async () => {
    if (!selectedPoi || selectedPoi.id !== poi.id) return;
    try {
      const st = await api("GET", `/api/v1/pois/${poi.id}/preview-clip`);
      const d = st.data || {};
      if (d.ready && d.clip_url) {
        switchToPreviewClip(d.clip_url);
        return;
      }
      if (d.error) {
        setPreviewStatus(`Превью: ${d.error}`);
      } else if (d.recording || (d.buffered_seconds || 0) < (d.target_seconds || 10)) {
        setPreviewStatus(`Запись превью… ${d.buffered_seconds || 0}/${d.target_seconds || 10} с`);
      }
    } catch (_) {}
    clipPollTimer = setTimeout(poll, 1000);
  };
  poll();
}

async function startPoiPreview(poi, fromRetry = false) {
  if (!fromRetry) previewAttempt = 0;
  stopPreview();
  const epoch = previewEpoch;
  if (!previewStillWanted(poi, epoch)) return;

  // Post-stream linger: play last ~5 min replay instead of live camera
  if (poi.status === "lingering" && poi.replay_clip_url) {
    const video = els.previewVideo();
    const canvas = document.getElementById("previewMaskCanvas");
    if (canvas) {
      canvas.style.display = "none";
      canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
    }
    if (video) {
      video.classList.remove("live-source-hidden");
      video.loop = true;
      video.srcObject = null;
      video.src = `${API}${poi.replay_clip_url}?t=${Date.now()}`;
      video.play().catch(() => {});
    }
    setPreviewStatus("Запись после эфира (до ~30 мин на карте)");
    updateHostBroadcastUi(poi);
    return;
  }

  const cam = getPreviewCamera(poi);
  const video = els.previewVideo();
  const canvas = document.getElementById("previewMaskCanvas");
  stopClipPoll();
  if (!cam) {
    setPreviewStatus("У места нет активной камеры. Настройте в админке и нажмите «Сохранить камеры».");
    return;
  }

  const looksLocal = cam.source_type === "local_usb"
    || !!cam.device_id
    || (cam.stream_url || "").startsWith("local://");

  // Don't touch getUserMedia for RTSP/HLS cams until fallback — avoids spurious permission prompts
  let deviceId = "";
  if (looksLocal) {
    const mod = await ensureLiveCamera();
    if (!previewStillWanted(poi, epoch)) return;
    deviceId = await mod.resolveUsbDeviceIdAsync(cam, usbFallbackCams(poi, cam));
    if (!previewStillWanted(poi, epoch)) return;
  }
  const isLocal = looksLocal || !!deviceId;

  if (activeStreamPoi && activeStreamPoi !== poi.id) {
    await releaseStream(activeStreamPoi, { force: false });
  }
  if (!previewStillWanted(poi, epoch)) return;
  activeStreamPoi = poi.id;

  // local_usb на iMac: только браузерный getUserMedia — без ffmpeg/acquire
  if (isLocal && canvas) {
    try {
      setPreviewStatus("Подключение камеры…");
      await releaseStream(poi.id, { force: false });
      if (!previewStillWanted(poi, epoch)) return;
      activeStreamPoi = poi.id;
      await new Promise((r) => setTimeout(r, 350));
      if (!previewStillWanted(poi, epoch)) return;
      const mod = await ensureLiveCamera();
      const { LiveCameraView } = mod;
      liveView?.stop();
      liveView = new LiveCameraView(video, canvas);
      canvas.style.display = "";
      const maskUrl = poi.mask_image_url ? `${API}${poi.mask_image_url}` : "";
      await liveView.start({
        deviceId,
        facingMode: facingFromPoiCam(poi, cam),
        maskImageUrl: maskUrl,
        apiBase: API,
        cameraId: cam.id,
        compositeMode: true,
      });
      if (!previewStillWanted(poi, epoch)) {
        liveView?.stop();
        liveView = null;
        return;
      }
      liveView.onRecognized = null;
      setPreviewStatus("Прямой эфир (веб-камера)");
      previewAttempt = 0;
      if (isPlaceOwner(poi)) startHostRecorderFromVideo(video);
      updateHostBroadcastUi(poi);
      return;
    } catch (e) {
      liveView?.stop();
      liveView = null;
      if (!previewStillWanted(poi, epoch)) return;
      // MediaPipe CDN often fails in Android WebView — fall back to raw camera
      if (await tryDeviceCameraFallback(poi, cam, epoch)) return;
      previewAttempt += 1;
      if (previewAttempt < 3 && previewStillWanted(poi, epoch)) {
        setPreviewStatus(`Камера занята, повтор ${previewAttempt}/3…`);
        previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 700);
        return;
      }
      if (previewStillWanted(poi, epoch)) {
        setPreviewStatus(`Камера недоступна: ${e.message}. Закройте FaceTime/Zoom и откройте место снова.`);
      }
      return;
    }
  }

  // Android lab: RTSP/MediaMTX usually offline — open front camera immediately
  if (isCmirAndroid()) {
    if (await tryDeviceCameraFallback(poi, cam, epoch)) return;
    if (previewStillWanted(poi, epoch)) {
      setPreviewStatus("Фронтальная камера недоступна. Проверьте разрешение CAMERA.");
    }
    return;
  }

  setPreviewStatus(previewAttempt ? `Подключение… попытка ${previewAttempt + 1}` : "Запуск камеры…");
  try {
    const pb = await fetchPlayback(cam);
    if (!previewStillWanted(poi, epoch)) return;
    const isLocalNet = pb.data?.source_type === "local_usb";

    if (isLocalNet && !pb.data?.masked_ready) {
      setPreviewStatus("Подготовка защищённого потока…");
      previewAttempt += 1;
      if (previewAttempt >= 8) {
        if (isCmirAndroid() && (await tryDeviceCameraFallback(poi, cam, epoch))) return;
        if (previewStillWanted(poi, epoch)) {
          setPreviewStatus("Защищённый поток не готов. Проверьте камеру и face-worker.");
        }
        return;
      }
      if (previewStillWanted(poi, epoch)) {
        previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 1000);
      }
      return;
    }

    const urls = liveUrls(pb);
    if (!urls.length) {
      // Android lab demo only — do not grab Mac FaceTime when RTSP/HLS is down
      if (isCmirAndroid() && (await tryDeviceCameraFallback(poi, cam, epoch))) return;
      if (!previewStillWanted(poi, epoch)) return;
      setPreviewStatus("Поток недоступен. Запустите start-lab.sh и сохраните камеры в админке.");
      previewAttempt += 1;
      if (previewAttempt < 3) {
        previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 1500);
      }
      return;
    }

    setPreviewStatus("Прямой эфир…");
    for (const url of urls) {
      if (!previewStillWanted(poi, epoch)) return;
      const ok = await tryHlsUrl(video, url, cam.id, { trackViews: !isLocalNet });
      if (!previewStillWanted(poi, epoch)) {
        stopPreview();
        return;
      }
      if (ok) {
        previewAttempt = 0;
        if (isLocalNet) pollPreviewClipSwitch(poi);
        else setPreviewStatus("");
        return;
      }
    }
    if (isCmirAndroid() && (await tryDeviceCameraFallback(poi, cam, epoch))) return;
    if (!previewStillWanted(poi, epoch)) return;
    previewAttempt += 1;
    if (previewAttempt >= 5) {
      setPreviewStatus("Не удалось подключиться. Проверьте MediaMTX (docker) и USB-камеру в админке.");
      return;
    }
    previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 2000);
  } catch (e) {
    if (!previewStillWanted(poi, epoch)) return;
    if (isCmirAndroid() && (await tryDeviceCameraFallback(poi, cam, epoch))) return;
    if (previewStillWanted(poi, epoch)) {
      setPreviewStatus(e.message || "Ошибка загрузки потока");
    }
  }
}

async function openPoiPanel(poi) {
  try {
    const res = await fetch(`${API}/api/v1/pois`);
    const list = (await res.json()).data || [];
    poi = list.find((p) => p.id === poi.id) || poi;
  } catch (_) {}
  selectedPoi = poi;
  setPoiChatOpen(false);
  els.poiPanel().classList.add("open");
  els.mapView()?.classList.add("panel-open");
  els.panelTitle().textContent = poi.name;
  els.panelAddr().textContent = poi.address || `${poi.city || ""} ${poi.country || ""}`.trim() || "—";
  els.panelComment().textContent = poi.comment || poi.description || "";
  updateHostBroadcastUi(poi);
  setTimeout(() => map?.invalidateSize(), 50);
  await startPoiPreview(poi);
  // Prefetch chat in background; UI stays collapsed until user opens it
  startPoiChat(poi.id);
}

function setPoiChatOpen(open) {
  const panel = els.poiPanel();
  const chat = document.getElementById("poiChat");
  const btn = document.getElementById("btnToggleChat");
  if (!panel) return;
  panel.classList.toggle("chat-open", !!open);
  if (chat) {
    if (open) chat.removeAttribute("hidden");
    else chat.setAttribute("hidden", "");
  }
  if (btn) {
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.textContent = open ? "Скрыть чат" : "Чат места";
  }
  setTimeout(() => {
    map?.invalidateSize();
    // Resize mask canvas after sheet height change
    liveView?.resizeCanvas?.();
  }, 240);
}

let chatPollTimer = null;
let chatSince = "";
let chatIsAdmin = false;

function stopPoiChat() {
  if (chatPollTimer) {
    clearInterval(chatPollTimer);
    chatPollTimer = null;
  }
  chatSince = "";
  const log = document.getElementById("poiChatLog");
  if (log) log.innerHTML = "";
}

function renderChatMessage(m) {
  const log = document.getElementById("poiChatLog");
  if (!log || !m?.id) return;
  if (log.querySelector(`[data-id="${m.id}"]`)) return;
  const row = document.createElement("div");
  row.className = "poi-chat-msg";
  row.dataset.id = m.id;
  const who = document.createElement("strong");
  who.textContent = m.display_name || "user";
  const body = document.createElement("span");
  body.textContent = " " + (m.body || "");
  row.appendChild(who);
  row.appendChild(body);
  if (chatIsAdmin) {
    const del = document.createElement("button");
    del.type = "button";
    del.className = "poi-chat-del";
    del.textContent = "×";
    del.title = "Удалить";
    del.addEventListener("click", async () => {
      try {
        await api("DELETE", `/api/v1/pois/${m.poi_id}/chat/${m.id}`);
        row.remove();
      } catch (e) {
        alert(e.message || "Не удалось удалить");
      }
    });
    const mute = document.createElement("button");
    mute.type = "button";
    mute.className = "poi-chat-mute";
    mute.textContent = "⊘";
    mute.title = "Заблокировать чат";
    mute.addEventListener("click", async () => {
      try {
        await api("POST", `/api/v1/pois/${m.poi_id}/chat/mute`, {
          user_id: m.user_id,
          hours: 24 * 30,
          reason: "muted by admin",
        });
        alert("Пользователь заблокирован в чате этого места");
      } catch (e) {
        alert(e.message || "Не удалось заблокировать");
      }
    });
    row.appendChild(del);
    row.appendChild(mute);
  }
  log.appendChild(row);
  log.scrollTop = log.scrollHeight;
}

async function refreshChatIsAdmin() {
  chatIsAdmin = false;
  if (!getToken()) return;
  try {
    const me = await api("GET", "/api/v1/auth/me");
    chatIsAdmin = me.data?.role === "admin";
  } catch (_) {}
}

async function pollPoiChat(poiId) {
  try {
    const q = chatSince ? `?since=${encodeURIComponent(chatSince)}` : "";
    const res = await fetch(`${API}/api/v1/pois/${poiId}/chat${q}`);
    const json = await res.json();
    const rows = json.data || [];
    for (const m of rows) {
      renderChatMessage(m);
      if (!chatSince || m.created_at > chatSince) chatSince = m.created_at;
    }
  } catch (_) {}
}

async function startPoiChat(poiId) {
  stopPoiChat();
  await refreshChatIsAdmin();
  const hint = document.getElementById("poiChatHint");
  if (hint) {
    hint.textContent = getToken()
      ? (chatIsAdmin ? "Админ: можно удалять сообщения и блокировать авторов" : "")
      : "Войдите в аккаунт, чтобы писать в чат";
  }
  await pollPoiChat(poiId);
  chatPollTimer = setInterval(() => {
    if (selectedPoi?.id === poiId) pollPoiChat(poiId);
  }, 2500);
}

async function openFullscreenStream() {
  if (!selectedPoi) return;
  const cam = getPreviewCamera(selectedPoi);
  if (!cam) return alert("Нет активной камеры");

  const u = new URL("stream.html", location.href);
  u.searchParams.set("poi", selectedPoi.id);
  u.searchParams.set("name", selectedPoi.name);
  u.searchParams.set("client", getClientId());
  u.searchParams.set("facing", facingFromPoiCam(selectedPoi, cam));
  if (selectedPoi.mask_image_url) {
    u.searchParams.set("mask", selectedPoi.mask_image_url);
  }

  // Lab / Android: HLS often unavailable — fullscreen device camera with masks
  let hlsUrl = "";
  try {
    const pb = await fetchPlayback(cam);
    hlsUrl = liveUrls(pb)[0] || "";
  } catch (_) {}

  if (hlsUrl && !isCmirAndroid()) {
    u.searchParams.set("url", hlsUrl);
    u.searchParams.set("mode", "hls");
  } else {
    u.searchParams.set("mode", "device");
  }

  // Free camera before navigating (WebView can't share stream across pages easily)
  stopPreview();
  stopClipPoll();

  // window.open is blocked / no-op in Android WebView — navigate in-place
  if (isCmirAndroid() || /Android/i.test(navigator.userAgent || "")) {
    location.assign(u.toString());
    return;
  }
  const win = window.open(u.toString(), "_blank", "noopener,noreferrer,width=1280,height=720");
  if (!win) location.assign(u.toString());
}

async function loadProfileMenu(poiId) {
  const sel = document.getElementById("profileMenu");
  if (!poiId || !sel) return;
  try {
    const items = (await api("GET", `/api/v1/pois/${poiId}/menu-items`)).data || [];
    const cur = sel.value;
    sel.innerHTML = '<option value="">— выберите —</option>'
      + items.map((i) => `<option value="${i}">${i}</option>`).join("");
    if (cur) sel.value = cur;
  } catch (_) {}
}

async function loadPlatformLinks() {
  const box = document.getElementById("platformLinks");
  if (!box || !getToken()) return;
  try {
    const links = (await api("GET", "/api/v1/auth/platforms")).data || [];
    box.innerHTML = links.length
      ? links.map((l) => `<p class="hint">${l.platform}: <strong>${l.username || "—"}</strong></p>`).join("")
      : "<p class='hint'>Нет привязанных платформ</p>";
  } catch (_) {
    box.innerHTML = "";
  }
}

async function fillProfileForm(u) {
  const form = document.getElementById("formProfile");
  if (!form) return;
  const prof = u.profile || {};
  const fio = document.getElementById("profileFio");
  if (fio) fio.textContent = `Имя: ${prof.full_name || u.display_name} (изменение недоступно)`;
  const phone = document.getElementById("profilePhone");
  const email = document.getElementById("profileEmail");
  const menu = document.getElementById("profileMenu");
  if (phone) phone.value = prof.phone || "";
  if (email) email.value = u.email || "";
  if (menu) menu.value = prof.favorite_menu_item || "";
  const poiId = u.consents?.[0]?.poi_id;
  await loadProfileMenu(poiId);
  if (menu && prof.favorite_menu_item) menu.value = prof.favorite_menu_item;
  await loadPlatformLinks();
  renderConsents(u);
  await loadAirtime();
}

async function loadAirtime() {
  const box = document.getElementById("airtimeList");
  if (!box || !getToken()) return;
  try {
    const rows = (await api("GET", "/api/v1/face-presence")).data || [];
    box.innerHTML = rows.length
      ? rows.map((r) => `
          <p class="hint">${r.camera_name || r.camera_id?.slice(0, 8) || "камера"} ·
            ${Number(r.seconds).toFixed(1)} с · период ${r.period_key}</p>
        `).join("")
      : "<p class='hint'>Пока нет зафиксированного присутствия в кадре.</p>";
  } catch (_) {
    box.innerHTML = "";
  }
}

function renderConsents(u) {
  const box = document.getElementById("consentsList");
  if (!box) return;
  const rows = u?.consents || [];
  if (!rows.length) {
    box.innerHTML = "<p class='hint'>Нет активных согласий — зарегистрируйтесь в киоске.</p>";
    return;
  }
  box.innerHTML = rows.map((c) => `
    <div class="stream-item" style="display:flex;justify-content:space-between;gap:0.5rem;align-items:center;padding:0.4rem 0;border-bottom:1px solid var(--border,#243552)">
      <span class="hint">POI ${String(c.poi_id).slice(0, 8)}… · ${c.consented_at || ""}</span>
      <button type="button" class="secondary" data-revoke-poi="${c.poi_id}" data-revoke-id="${c.id}" style="width:auto;padding:0.35rem 0.65rem;margin:0">Отозвать</button>
    </div>
  `).join("");
  box.querySelectorAll("[data-revoke-id]").forEach((btn) => {
    btn.onclick = async () => {
      if (!confirm("Отозвать согласие? На камерах снова появится маска.")) return;
      try {
        await api("DELETE", `/api/v1/pois/${btn.dataset.revokePoi}/consent/${btn.dataset.revokeId}`);
        await refreshAuth();
      } catch (err) {
        alert(err.message || "Не удалось отозвать");
      }
    };
  });
}

function userHasConsent(u) {
  return Array.isArray(u?.consents) && u.consents.length > 0;
}

function updateKioskLink(u) {
  const link = document.getElementById("tabKiosk");
  if (!link) return;
  // Keep kiosk reachable from bottom nav even after consent
  link.style.display = "";
  link.setAttribute("aria-label", u && userHasConsent(u) ? "Киоск согласия" : "Киоск согласия");
}

async function refreshAuth() {
  const token = getToken();
  const tabAccount = document.getElementById("tabAccount");
  if (!token) {
    els.authGuest().style.display = "block";
    els.authUser().style.display = "none";
    els.adminLink().style.display = "none";
    updateKioskLink(null);
    if (tabAccount) tabAccount.style.display = "";
    return;
  }
  try {
    const me = await api("GET", "/api/v1/auth/me");
    const u = me.data;
    if (u.role === "admin") {
      els.authGuest().style.display = "none";
      els.authUser().style.display = "block";
      els.adminLink().style.display = "block";
      updateKioskLink(u);
      if (tabAccount) tabAccount.style.display = "";
      els.authStatus().textContent = `${u.display_name || "Admin"} (${u.email}) · роль: admin`;
      return;
    }
    els.authGuest().style.display = "none";
    els.authUser().style.display = "block";
    els.adminLink().style.display = "none";
    updateKioskLink(u);
    if (tabAccount) tabAccount.style.display = "";
    const w = u.wallet;
    els.authStatus().textContent = w
      ? `${u.display_name} (${u.email})\nКошелёк: ${w.address}\nST: ${w.balance_st} · UT: ${w.balance_ut}`
      : `${u.display_name} (${u.email})`;
    await fillProfileForm(u);
  } catch {
    setToken("");
    refreshAuth();
  }
}

function bindEvents() {
  document.querySelectorAll(".tab-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      showView(btn.dataset.view);
    });
  });

  document.getElementById("closePanel")?.addEventListener("click", () => closePoiPanel());

  document.getElementById("btnFullscreen")?.addEventListener("click", openFullscreenStream);
  document.getElementById("btnEndBroadcast")?.addEventListener("click", () => {
    if (!selectedPoi) return;
    if (!confirm("Завершить трансляцию? Точка останется на карте ~30 минут с записью последних минут, затем удалится.")) {
      return;
    }
    endHostBroadcast(selectedPoi).catch(() => {});
  });

  document.getElementById("btnToggleChat")?.addEventListener("click", () => {
    const open = !els.poiPanel()?.classList.contains("chat-open");
    setPoiChatOpen(open);
    if (open && selectedPoi) pollPoiChat(selectedPoi.id);
  });

  document.getElementById("poiChatForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!selectedPoi) return;
    if (!getToken()) {
      alert("Войдите в аккаунт, чтобы писать в чат");
      showView("account");
      return;
    }
    const input = document.getElementById("poiChatInput");
    const text = (input?.value || "").trim();
    if (!text) return;
    try {
      const res = await api("POST", `/api/v1/pois/${selectedPoi.id}/chat`, { body: text });
      if (input) input.value = "";
      renderChatMessage(res.data);
      if (res.data?.created_at) chatSince = res.data.created_at;
    } catch (err) {
      alert(err.message || "Не удалось отправить");
    }
  });

  let addPlacePick = false;
  const addModal = document.getElementById("addPlaceModal");
  document.getElementById("btnAddPlace")?.addEventListener("click", () => {
    if (!getToken()) {
      alert("Войдите в аккаунт, чтобы предложить место");
      showView("account");
      return;
    }
    addPlacePick = true;
    showMapStatus("Кликните на карте точку нового места", false);
  });
    document.getElementById("btnCancelAddPlace")?.addEventListener("click", () => {
    addPlacePick = false;
    addModal?.classList.remove("open");
  });
  document.getElementById("formAddPlace")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("addPlaceMsg");
    try {
      await api("POST", "/api/v1/pois/submit", {
        name: document.getElementById("addPlaceName")?.value,
        address: document.getElementById("addPlaceAddress")?.value,
        comment: document.getElementById("addPlaceComment")?.value,
        latitude: Number(document.getElementById("addPlaceLat")?.value),
        longitude: Number(document.getElementById("addPlaceLng")?.value),
        facing_mode: document.getElementById("addPlaceFacing")?.value || "user",
      });
      if (msg) msg.textContent = "Заявка отправлена. Ждите аппрува администратора.";
      setTimeout(() => {
        addModal?.classList.remove("open");
        if (msg) msg.textContent = "";
      }, 1500);
    } catch (err) {
      if (msg) msg.textContent = err.message || "Ошибка";
    }
  });

  // Map click for add-place is hooked after map init via window.__cmirOnMapClick
  window.__cmirOnMapClick = (latlng) => {
    if (!addPlacePick) return false;
    addPlacePick = false;
    showMapStatus("", false);
    document.getElementById("addPlaceLat").value = String(latlng.lat);
    document.getElementById("addPlaceLng").value = String(latlng.lng);
    document.getElementById("addPlaceCoords").textContent =
      `Координаты: ${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;
    addModal?.classList.add("open");
    return true;
  };

  window.addEventListener("pagehide", () => {
    const poiId = activeStreamPoi || selectedPoi?.id;
    stopPreview();
    selectedPoi = null;
    if (!poiId) return;
    navigator.sendBeacon(
      `${API}/api/v1/pois/${poiId}/stream/release`,
      new Blob(
        [JSON.stringify({ client_id: getClientId(), force: false })],
        { type: "application/json" },
      ),
    );
    activeStreamPoi = null;
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      const poiId = activeStreamPoi || selectedPoi?.id;
      stopPreview();
      if (poiId) {
        navigator.sendBeacon(
          `${API}/api/v1/pois/${poiId}/stream/release`,
          new Blob(
            [JSON.stringify({ client_id: getClientId(), force: false })],
            { type: "application/json" },
          ),
        );
      }
      activeStreamPoi = null;
      return;
    }
    if (document.visibilityState === "visible" && selectedPoi && els.poiPanel()?.classList.contains("open")) {
      startPoiPreview(selectedPoi).catch(() => {});
    }
  });

  document.querySelectorAll(".auth-tabs button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".auth-tabs button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("formLogin").style.display = btn.dataset.auth === "login" ? "block" : "none";
      document.getElementById("formRegister").style.display = btn.dataset.auth === "register" ? "block" : "none";
    });
  });

  document.getElementById("formLogin").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const r = await api("POST", "/api/v1/auth/login", {
        email: fd.get("email"),
        password: fd.get("password"),
      });
      setToken(r.data.token);
      if (r.data.user) localStorage.setItem("cmir_user", JSON.stringify(r.data.user));
      els.authMsg().textContent = "Вход выполнен";
      els.authMsg().className = "msg ok";
      await refreshAuth();
      if (r.data.user?.role === "admin") {
        els.adminLink().style.display = "block";
      }
    } catch (err) {
      els.authMsg().textContent = err.message;
      els.authMsg().className = "msg error";
    }
  });

  document.getElementById("formRegister").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("POST", "/api/v1/auth/register", {
        email: fd.get("email"),
        password: fd.get("password"),
        display_name: fd.get("name"),
      });
      els.authMsg().textContent = "Регистрация OK — войдите";
      els.authMsg().className = "msg ok";
    } catch (err) {
      els.authMsg().textContent = err.message;
      els.authMsg().className = "msg error";
    }
  });

  document.getElementById("btnLogout").addEventListener("click", async () => {
    try { await api("POST", "/api/v1/auth/logout", {}); } catch (_) {}
    setToken("");
    localStorage.removeItem("cmir_user");
    refreshAuth();
  });

  document.getElementById("formProfile")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("profileMsg");
    try {
      const body = {
        phone: document.getElementById("profilePhone").value.trim(),
        email: document.getElementById("profileEmail").value.trim(),
        favorite_menu_item: document.getElementById("profileMenu").value,
      };
      const r = await api("PATCH", "/api/v1/auth/profile", body);
      msg.textContent = "Профиль сохранён";
      msg.className = "msg ok";
      if (r.data?.user) await fillProfileForm({ ...r.data.user, profile: r.data.profile });
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "msg error";
    }
  });

  document.getElementById("btnLinkPlatform")?.addEventListener("click", async () => {
    try {
      await api("POST", "/api/v1/auth/platforms/link", {
        platform: document.getElementById("platformSelect").value,
        username: document.getElementById("platformUsername").value.trim(),
      });
      await loadPlatformLinks();
      document.getElementById("profileMsg").textContent = "Платформа привязана";
      document.getElementById("profileMsg").className = "msg ok";
    } catch (err) {
      document.getElementById("profileMsg").textContent = err.message;
      document.getElementById("profileMsg").className = "msg error";
    }
  });

  document.getElementById("btnOAuthPlatform")?.addEventListener("click", async () => {
    try {
      const platform = document.getElementById("platformSelect").value;
      const r = await api("GET", `/api/v1/platforms/${platform}/authorize`);
      if (r.data?.authorize_url) location.href = r.data.authorize_url;
    } catch (err) {
      document.getElementById("profileMsg").textContent = err.message;
      document.getElementById("profileMsg").className = "msg error";
    }
  });
}

export async function initUser() {
  // Nav must work even if the map / API fail
  bindEvents();
  showView("map");
  try {
    initMap();
  } catch (e) {
    console.error("initMap failed:", e);
    showMapStatus(`Карта недоступна: ${e.message}`, true);
  }
  // Auth + POIs in background so UI is interactive immediately
  refreshAuth().catch((e) => console.error("refreshAuth failed:", e));
  loadPois()
    .then(() => {
      setInterval(loadPois, 30000);
    })
    .catch((e) => {
      console.error("loadPois failed:", e);
      showMapStatus(`Не удалось загрузить места: ${e.message}`, true);
    });
}
