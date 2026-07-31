import { API, api, getToken, setToken } from "./api.js";

let map, markers = [], pois = [], hlsPreview = null, selectedPoi = null;
let previewRetryTimer = null, previewAttempt = 0;
let activeStreamPoi = null;
let liveView = null;
let liveCameraMod = null;

async function ensureLiveCamera() {
  if (!liveCameraMod) {
    liveCameraMod = await import("./live-camera.js");
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
  document.getElementById(name === "map" ? "mapView" : "accountView").classList.add("active");
  if (name === "map") {
    setTimeout(() => map?.invalidateSize(), 50);
    setTimeout(() => map?.invalidateSize(), 300);
  }
}

function initMap() {
  if (typeof L === "undefined") {
    throw new Error("Leaflet не загружен — проверьте интернет и обновите страницу");
  }
  const el = document.getElementById("map");
  if (!el) throw new Error("Элемент #map не найден");
  if (map) {
    map.remove();
    map = null;
  }
  map = L.map(el, { zoomControl: true }).setView([41.7151, 44.8271], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
  }).addTo(map);
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
    const res = await fetch(`${API}/api/v1/pois`);
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || res.statusText);
    pois = json.data || [];
    clearMarkers();
    pois.forEach((poi) => {
      const lat = Number(poi.latitude);
      const lon = Number(poi.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      const m = L.marker([lat, lon])
        .addTo(map)
        .bindTooltip(poi.name, { permanent: false })
        .on("click", () => openPoiPanel(poi));
      markers.push(m);
    });
    if (pois.length && !selectedPoi && markers.length) {
      const bounds = L.featureGroup(markers).getBounds();
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
    showMapStatus(
      `Сервер недоступен (${API}). Запустите: cd cmir && bash scripts/start-lab.sh`,
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

function setPreviewStatus(msg) {
  const el = els.panelPreviewStatus();
  if (el) el.textContent = msg || "";
}

function stopViewTracking() {
  if (viewTimer) { clearInterval(viewTimer); viewTimer = null; }
  viewCameraId = null;
}

async function releaseStream(poiId, { force = true } = {}) {
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
  if (previewRetryTimer) { clearTimeout(previewRetryTimer); previewRetryTimer = null; }
  stopClipPoll();
  stopViewTracking();
  if (liveView) {
    liveView.stop();
    liveView = null;
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
    v.pause();
    v.removeAttribute("src");
    v.srcObject = null;
    v.loop = false;
    v.load();
  }
}

async function closePoiPanel() {
  const poiId = selectedPoi?.id || activeStreamPoi;
  els.poiPanel().classList.remove("open");
  stopPreview();
  setPreviewStatus("");
  selectedPoi = null;
  previewAttempt = 0;
  if (poiId) await releaseStream(poiId, { force: true });
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
  const cam = getPreviewCamera(poi);
  const video = els.previewVideo();
  const canvas = document.getElementById("previewMaskCanvas");
  stopPreview();
  stopClipPoll();
  if (!cam) {
    setPreviewStatus("У места нет активной камеры. Настройте в админке и нажмите «Сохранить камеры».");
    return;
  }

  const mod = await ensureLiveCamera();
  const deviceId = await mod.resolveUsbDeviceIdAsync(cam, usbFallbackCams(poi, cam));
  const isLocal = cam.source_type === "local_usb" || !!deviceId
    || !!cam.device_id || (cam.stream_url || "").startsWith("local://");

  if (activeStreamPoi && activeStreamPoi !== poi.id) {
    await releaseStream(activeStreamPoi, { force: true });
  }
  activeStreamPoi = poi.id;

  // local_usb на iMac: только браузерный getUserMedia — без ffmpeg/acquire
  // (иначе 10 ретраев и камера остаётся включённой)
  if (isLocal && canvas) {
    try {
      setPreviewStatus("Подключение камеры…");
      // освобождаем device, если relay ещё держит ffmpeg
      await releaseStream(poi.id, { force: true });
      activeStreamPoi = poi.id;
      await new Promise((r) => setTimeout(r, 350));
      const { LiveCameraView } = mod;
      liveView = new LiveCameraView(video, canvas);
      canvas.style.display = "";
      const maskUrl = poi.mask_image_url ? `${API}${poi.mask_image_url}` : "";
      await liveView.start({
        deviceId,
        maskImageUrl: maskUrl,
        apiBase: API,
        cameraId: cam.id,
        compositeMode: true,
      });
      liveView.onRecognized = () => { liveView.loadConsentedFaces().catch(() => {}); };
      setPreviewStatus("Прямой эфир (веб-камера)");
      previewAttempt = 0;
      return;
    } catch (e) {
      liveView?.stop();
      liveView = null;
      previewAttempt += 1;
      if (previewAttempt < 3) {
        setPreviewStatus(`Камера занята, повтор ${previewAttempt}/3…`);
        previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 700);
        return;
      }
      setPreviewStatus(`Камера недоступна: ${e.message}. Закройте FaceTime/Zoom и откройте место снова.`);
      return;
    }
  }

  setPreviewStatus(previewAttempt ? `Подключение… попытка ${previewAttempt + 1}` : "Запуск камеры…");
  try {
    const pb = await fetchPlayback(cam);
    const isLocalNet = pb.data?.source_type === "local_usb";

    if (isLocalNet && !pb.data?.masked_ready) {
      setPreviewStatus("Подготовка защищённого потока…");
      previewAttempt += 1;
      if (previewAttempt >= 8) {
        setPreviewStatus("Защищённый поток не готов. Проверьте камеру и face-worker.");
        return;
      }
      previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 1000);
      return;
    }

    const urls = liveUrls(pb);
    if (!urls.length) {
      setPreviewStatus("Поток недоступен. Запустите start-lab.sh и сохраните камеры в админке.");
      previewAttempt += 1;
      if (previewAttempt < 6) {
        previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 1500);
      }
      return;
    }

    setPreviewStatus("Прямой эфир…");
    for (const url of urls) {
      const ok = await tryHlsUrl(video, url, cam.id, { trackViews: !isLocalNet });
      if (ok) {
        previewAttempt = 0;
        if (isLocalNet) pollPreviewClipSwitch(poi);
        else setPreviewStatus("");
        return;
      }
    }
    previewAttempt += 1;
    if (previewAttempt >= 5) {
      setPreviewStatus("Не удалось подключиться. Проверьте MediaMTX (docker) и USB-камеру в админке.");
      return;
    }
    previewRetryTimer = setTimeout(() => startPoiPreview(poi, true), 2000);
  } catch (e) {
    setPreviewStatus(e.message || "Ошибка загрузки потока");
  }
}

async function openPoiPanel(poi) {
  try {
    const res = await fetch(`${API}/api/v1/pois`);
    const list = (await res.json()).data || [];
    poi = list.find((p) => p.id === poi.id) || poi;
  } catch (_) {}
  selectedPoi = poi;
  els.poiPanel().classList.add("open");
  els.panelTitle().textContent = poi.name;
  els.panelAddr().textContent = poi.address || `${poi.city || ""} ${poi.country || ""}`.trim() || "—";
  els.panelComment().textContent = poi.comment || poi.description || "";
  await startPoiPreview(poi);
}

async function openFullscreenStream() {
  if (!selectedPoi) return;
  const cam = getPreviewCamera(selectedPoi);
  if (!cam) return alert("Нет активной камеры");
  try {
    const pb = await fetchPlayback(cam);
    const url = liveUrls(pb)[0];
    if (!url) return alert("Поток недоступен — подождите завершения подготовки превью");
    const u = new URL("stream.html", location.href);
    u.searchParams.set("poi", selectedPoi.id);
    u.searchParams.set("url", url);
    u.searchParams.set("name", selectedPoi.name);
    u.searchParams.set("client", getClientId());
    window.open(u.toString(), "_blank", "noopener,noreferrer,width=1280,height=720");
  } catch (e) {
    alert(e.message || "Ошибка открытия трансляции");
  }
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
  if (fio) fio.textContent = `ФИО: ${prof.full_name || u.display_name} (изменение недоступно)`;
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
        if (liveView) await liveView.loadConsentedFaces();
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
  const link = document.getElementById("kioskLink");
  if (!link) return;
  link.style.display = u && userHasConsent(u) ? "none" : "";
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
      els.authUser().style.display = "none";
      els.adminLink().style.display = "inline-block";
      updateKioskLink(u);
      if (tabAccount) tabAccount.style.display = "none";
      showView("map");
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
    if (liveView) await liveView.loadConsentedFaces();
  } catch {
    setToken("");
    refreshAuth();
  }
}

function bindEvents() {
  document.querySelectorAll(".tab-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  });

  document.getElementById("closePanel").addEventListener("click", () => closePoiPanel());

  document.getElementById("btnFullscreen").addEventListener("click", openFullscreenStream);

  window.addEventListener("pagehide", () => {
    const poiId = activeStreamPoi || selectedPoi?.id;
    stopPreview();
    selectedPoi = null;
    if (!poiId) return;
    navigator.sendBeacon(
      `${API}/api/v1/pois/${poiId}/stream/release`,
      new Blob(
        [JSON.stringify({ client_id: getClientId(), force: true })],
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
            [JSON.stringify({ client_id: getClientId(), force: true })],
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
      els.authMsg().textContent = "Вход выполнен";
      els.authMsg().className = "msg ok";
      await refreshAuth();
      if (r.data.user?.role === "admin") {
        els.adminLink().style.display = "inline-block";
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
  try {
    initMap();
    bindEvents();
    showView("map");
    await refreshAuth();
    await loadPois();
    setInterval(loadPois, 30000);
  } catch (e) {
    console.error("initUser failed:", e);
    const banner = document.createElement("p");
    banner.className = "msg error";
    banner.style.cssText = "position:fixed;bottom:1rem;left:1rem;right:1rem;z-index:9999;padding:1rem;background:#2a1212";
    banner.textContent = `Ошибка загрузки карты: ${e.message}`;
    document.body.appendChild(banner);
  }
}
