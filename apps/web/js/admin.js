import { API, api, geocodeAddress, reverseGeocode, getToken, setToken, authHeaders } from "./api.js";
import { AdminMaskPreview } from "./mask-preview.js";

let map, markers = [], pois = [], selectedPoiId = null, selectedUserId = null;
let pendingMaskFile = null, adminHls = null, localPreviewStream = null;
let localDevices = [], cameraSlots = [], pickMarker = null, markerClickAt = 0;
let addPoiFromMap = false, maskPreview = null;

function log(msg) {
  const el = document.getElementById("adminLog");
  if (el) el.textContent = new Date().toLocaleTimeString() + " " + msg + "\n" + el.textContent;
}

function bindClick(id, handler) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Элемент #${id} не найден в admin.html`);
  el.onclick = handler;
}

function bindChange(id, handler) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Элемент #${id} не найден в admin.html`);
  el.onchange = handler;
}

function bindSubmit(id, handler) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Элемент #${id} не найден в admin.html`);
  el.onsubmit = handler;
}

function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

async function guardAdmin() {
  const token = getToken();
  if (!token) { location.href = "index.html#account"; return false; }
  try {
    const me = await api("GET", "/api/v1/auth/me");
    if (me.data.role !== "admin") { alert("Нужны права администратора"); location.href = "index.html"; return false; }
    document.getElementById("adminUserLabel").textContent = me.data.email;
    return true;
  } catch {
    setToken(""); location.href = "index.html#account"; return false;
  }
}

function showAdminTab(name) {
  const panels = { places: "panelPlaces", users: "panelUsers", quality: "panelQuality", stats: "panelStats" };
  document.querySelectorAll("[data-admin-tab]").forEach((b) => {
    b.classList.toggle("active", b.dataset.adminTab === name);
  });
  document.querySelectorAll(".admin-tab-panel").forEach((p) => p.classList.remove("active"));
  document.getElementById(panels[name])?.classList.add("active");
  if (name === "places" && map) {
    setTimeout(() => map.invalidateSize(), 50);
    setTimeout(() => map.invalidateSize(), 300);
  }
  if (name === "stats") loadAdminStats().catch((e) => alert(e.message));
}

function requireSelectedPoi(actionLabel) {
  if (selectedPoiId) return true;
  alert(`Сначала выберите место в списке — без этого ${actionLabel} невозможно.`);
  return false;
}

function setPoiFormEditable(on) {
  document.querySelector(".admin-side")?.classList.toggle("is-readonly", !on);
  document.getElementById("btnGeocode").disabled = !on;
  document.getElementById("btnSavePoi").disabled = !on;
  document.getElementById("btnDeletePoi").disabled = !on;
}

function resolveDeviceId(cam) {
  if (!cam) return "";
  if (cam.device_id) return cam.device_id;
  if (cam.stream_url?.startsWith("local://")) return cam.stream_url.slice(8);
  return "";
}

function maskPreviewUrl() {
  if (pendingMaskFile) return URL.createObjectURL(pendingMaskFile);
  const poi = pois.find((p) => p.id === selectedPoiId);
  if (poi?.mask_image_url) return API + poi.mask_image_url + "?t=" + Date.now();
  return "";
}

function updateMaskPreview(url) {
  if (!maskPreview) return;
  const resolved = url !== undefined ? url : maskPreviewUrl();
  maskPreview.setMaskUrl(resolved);
  if (localPreviewStream || adminHls) maskPreview.start();
}

function initMap() {
  map = L.map("adminMap").setView([41.7151, 44.8271], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OSM" }).addTo(map);
  map.on("click", async (e) => {
    if (Date.now() - markerClickAt < 250) return;
    const { lat, lng } = e.latlng;
    try {
      const rev = await reverseGeocode(lat, lng);
      openAddPoiModal({
        fromMap: true,
        lat: rev.lat,
        lon: rev.lon,
        address: rev.display,
      });
      if (pickMarker) map.removeLayer(pickMarker);
      pickMarker = L.marker([rev.lat, rev.lon], {
        icon: L.divIcon({
          className: "",
          html: '<div style="background:#4d9fff;color:#fff;padding:4px 8px;border-radius:6px;font-size:11px">Новое место</div>',
          iconAnchor: [40, 10],
        }),
      }).addTo(map);
    } catch (err) {
      alert("Не удалось определить адрес по точке на карте: " + err.message);
    }
  });
}

function openAddPoiModal({ fromMap = false, lat = "", lon = "", address = "" } = {}) {
  addPoiFromMap = fromMap;
  document.getElementById("formAddPoi").reset();
  document.getElementById("dlgPoiLat").value = lat;
  document.getElementById("dlgPoiLng").value = lon;
  const addrEl = document.getElementById("dlgPoiAddress");
  const infoEl = document.getElementById("addPoiMapInfo");
  const titleEl = document.getElementById("addPoiModalTitle");
  if (fromMap) {
    titleEl.textContent = "Новое место с карты";
    addrEl.value = address;
    addrEl.readOnly = true;
    addrEl.required = false;
    infoEl.style.display = "block";
    infoEl.textContent = `Координаты: ${Number(lat).toFixed(5)}, ${Number(lon).toFixed(5)} · адрес с карты`;
  } else {
    titleEl.textContent = "Новое место по адресу";
    addrEl.readOnly = false;
    addrEl.required = true;
    infoEl.style.display = "none";
    infoEl.textContent = "";
  }
  openModal("addPoiModal");
}

function refreshPoiMarkers() {
  if (!map) return;
  markers.forEach((m) => map.removeLayer(m));
  markers = [];
  pois.forEach((poi) => {
    const m = L.marker([poi.latitude, poi.longitude], {
      icon: L.divIcon({
        className: "",
        html: `<div style="background:${poi.id === selectedPoiId ? "#4d9fff" : "#2d6a9f"};color:#fff;padding:4px 8px;border-radius:6px;font-size:11px">${poi.name}</div>`,
        iconAnchor: [20, 10],
      }),
    }).addTo(map).on("click", () => {
      markerClickAt = Date.now();
      selectPoi(poi.id);
    });
    markers.push(m);
  });
}

async function loadPois() {
  const res = await fetch(`${API}/api/v1/pois`);
  pois = (await res.json()).data || [];
  refreshPoiMarkers();
  const sel = document.getElementById("poiSelect");
  sel.innerHTML = '<option value="">— выберите место —</option>' +
    pois.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
  if (selectedPoiId && pois.some((p) => p.id === selectedPoiId)) sel.value = selectedPoiId;
}

async function loadLocalDevices() {
  try {
    await navigator.mediaDevices.getUserMedia({ video: true }).then((s) => s.getTracks().forEach((t) => t.stop()));
  } catch (_) {}
  const all = await navigator.mediaDevices.enumerateDevices();
  localDevices = all.filter((d) => d.kind === "videoinput");
}

function stopCameraStreams() {
  maskPreview?.stop();
  if (adminHls) { adminHls.destroy(); adminHls = null; }
  if (localPreviewStream) { localPreviewStream.getTracks().forEach((t) => t.stop()); localPreviewStream = null; }
  const video = document.getElementById("adminCameraPreview");
  video.removeAttribute("src");
  video.srcObject = null;
}

function setMaskSectionEnabled(previewOn, hint = "") {
  const section = document.getElementById("maskSection");
  section.classList.toggle("preview-inactive", !previewOn);
  document.getElementById("maskCameraHint").textContent = previewOn
    ? "Рабочая камера активна — загрузите маску для превью"
    : hint || "Включите рабочую камеру у выбранного места";
  refreshMaskButtons();
}

function refreshMaskButtons() {
  const hasPoi = !!selectedPoiId;
  document.getElementById("maskFile").disabled = !hasPoi;
  document.getElementById("btnApplyMask").disabled = !hasPoi || !pendingMaskFile;
  document.getElementById("btnRemoveMask").disabled = !hasPoi;
}

function slotToPreviewCam(slot) {
  if (!slot) return null;
  return {
    id: slot.id,
    is_active: slot.is_active,
    is_preview: slot.is_preview,
    source_type: slot.device_id ? "local_usb" : (slot.source_type || "rtsp"),
    device_id: slot.device_id,
    stream_url: slot.device_id ? `local://${slot.device_id}` : (slot.stream_url || ""),
  };
}

function getPreviewSlotCamera() {
  const slot = cameraSlots.find((s) => s.is_preview && s.is_active);
  return slotToPreviewCam(slot);
}

async function refreshLocalPreview() {
  if (!selectedPoiId) return;
  updateMaskPreview();
  const cam = getPreviewSlotCamera();
  if (!cam) {
    stopCameraStreams();
    setMaskSectionEnabled(false, "Выберите рабочую включённую камеру");
    return;
  }
  const deviceId = resolveDeviceId(cam);
  if (!deviceId && (cam.source_type === "local_usb" || !cam.id)) {
    stopCameraStreams();
    setMaskSectionEnabled(false, "Выберите USB-камеру в списке");
    return;
  }
  await startCameraPreview({ ...cam, device_id: deviceId });
}

function showMaskOverlay(url) {
  updateMaskPreview(url);
}

async function startCameraPreview(cam) {
  stopCameraStreams();
  updateMaskPreview();
  if (!cam?.is_active) {
    setMaskSectionEnabled(false, "Отметьте камеру как включённую и рабочую");
    return;
  }
  const video = document.getElementById("adminCameraPreview");
  const deviceId = resolveDeviceId(cam);
  if (cam.source_type === "local_usb" || cam.stream_url?.startsWith("local://") || deviceId) {
    if (!deviceId) {
      setMaskSectionEnabled(false, "Выберите USB-камеру в списке");
      return;
    }
    try {
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } } });
      } catch (_) {
        stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId } });
      }
      localPreviewStream = stream;
      video.srcObject = stream;
      await video.play();
      if (!maskPreview?.ready) await maskPreview?.init();
      updateMaskPreview();
      maskPreview?.start();
      setMaskSectionEnabled(true);
    } catch (e) {
      setMaskSectionEnabled(false, "USB-камера недоступна: " + e.message);
    }
    return;
  }
  if (!cam.id) {
    setMaskSectionEnabled(false, "Сохраните камеры, чтобы открыть сетевой поток");
    return;
  }
  try {
    const pb = await api("GET", `/api/v1/cameras/${cam.id}/playback`);
    const url = pb.data.masked_hls_url || pb.data.hls_url;
    if (!url) throw new Error("нет HLS");
    if (window.Hls && Hls.isSupported()) {
      adminHls = new Hls({ lowLatencyMode: true });
      adminHls.loadSource(url);
      adminHls.attachMedia(video);
      adminHls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().then(async () => {
          if (!maskPreview?.ready) await maskPreview?.init();
          updateMaskPreview();
          maskPreview?.start();
          setMaskSectionEnabled(true);
        });
      });
    } else {
      video.src = url;
      await video.play();
      if (!maskPreview?.ready) await maskPreview?.init();
      updateMaskPreview();
      maskPreview?.start();
      setMaskSectionEnabled(true);
    }
  } catch (e) {
    setMaskSectionEnabled(false, "Поток недоступен");
  }
}

function buildCameraSlotsFromPoi(poi) {
  const cams = (poi?.cameras || []).slice().sort((a, b) => (a.slot_index ?? 0) - (b.slot_index ?? 0));
  if (!cams.length) {
    cameraSlots = [{ slot_index: 0, device_id: "", is_active: true, is_preview: true, name: "Камера 1", role: "general" }];
  } else {
    cameraSlots = cams.map((c, i) => ({
      id: c.id,
      slot_index: c.slot_index ?? i,
      device_id: resolveDeviceId(c),
      device_label: c.device_label || "",
      is_active: c.is_active,
      is_preview: c.is_preview,
      name: c.name,
      role: c.role || "general",
      source_type: c.source_type || (resolveDeviceId(c) ? "local_usb" : "rtsp"),
      stream_url: c.stream_url,
    }));
  }
  renderCameraSlots();
}

const CAMERA_ROLE_LABELS = {
  general: "Общий план",
  consent: "Согласие",
  performance: "Перфоманс",
};

function buildDeviceOptions(selectedId) {
  let opts = '<option value="">— выберите USB-камеру —</option>';
  const seen = new Set();
  for (const d of localDevices) {
    seen.add(d.deviceId);
    const sel = d.deviceId === selectedId ? " selected" : "";
    opts += `<option value="${d.deviceId}"${sel}>${d.label || "Камера"}</option>`;
  }
  if (selectedId && !seen.has(selectedId)) {
    opts += `<option value="${selectedId}" selected>Сохранённая (${selectedId.slice(0, 10)}…)</option>`;
  }
  return opts;
}

function renderCameraSlots() {
  const wrap = document.getElementById("cameraSlots");
  if (!wrap) return;
  wrap.innerHTML = cameraSlots.map((slot, i) => {
    const opts = buildDeviceOptions(slot.device_id || "");
    const role = slot.role || "general";
    const roleOpts = Object.entries(CAMERA_ROLE_LABELS).map(([v, label]) =>
      `<option value="${v}"${v === role ? " selected" : ""}>${label}</option>`,
    ).join("");
    const previewRow = role === "general"
      ? `<label><input type="radio" name="previewCam" class="slot-preview" value="${i}" ${slot.is_preview ? "checked" : ""} /> Рабочая (превью с маской)</label>`
      : "";
    return `
    <div class="camera-slot" data-slot="${i}">
      <strong>Камера ${i + 1}</strong>
      <label>Тип камеры
        <select class="slot-role">${roleOpts}</select>
      </label>
      <select class="slot-device">${opts}</select>
      <label><input type="checkbox" class="slot-active" ${slot.is_active ? "checked" : ""} /> Камера включена</label>
      ${previewRow}
      <button type="button" class="slot-remove" data-slot="${i}">Отвязать камеру</button>
    </div>`;
  }).join("");
  wrap.querySelectorAll(".camera-slot").forEach((el, i) => {
    const devSel = el.querySelector(".slot-device");
    if (devSel) {
      devSel.value = cameraSlots[i].device_id || "";
      devSel.onchange = (e) => {
        cameraSlots[i].device_id = e.target.value;
        cameraSlots[i].device_label = localDevices.find((d) => d.deviceId === e.target.value)?.label || "";
        cameraSlots[i].source_type = e.target.value ? "local_usb" : "rtsp";
        if (cameraSlots[i].is_preview) refreshLocalPreview();
      };
    }
    const roleSel = el.querySelector(".slot-role");
    if (roleSel) {
      roleSel.value = cameraSlots[i].role || "general";
      roleSel.onchange = (e) => {
        cameraSlots[i].role = e.target.value;
        if (e.target.value !== "general") cameraSlots[i].is_preview = false;
        renderCameraSlots();
      };
    }
    const activeCb = el.querySelector(".slot-active");
    if (activeCb) {
      activeCb.onchange = (e) => {
        cameraSlots[i].is_active = e.target.checked;
        if (cameraSlots[i].is_preview) refreshLocalPreview();
      };
    }
    const prev = el.querySelector(".slot-preview");
    if (prev) {
      prev.onchange = () => {
        cameraSlots.forEach((s, j) => { s.is_preview = j === i; });
        renderCameraSlots();
        refreshLocalPreview();
      };
    }
    const removeBtn = el.querySelector(".slot-remove");
    if (removeBtn) removeBtn.onclick = () => removeCameraSlot(i);
  });
}

async function removeCameraSlot(i) {
  if (!requireSelectedPoi("отвязку камеры")) return;
  const label = cameraSlots[i]?.name || `Камера ${i + 1}`;
  if (!confirm(`Отвязать «${label}» от этого места?`)) return;
  const wasPreview = cameraSlots[i]?.is_preview;
  cameraSlots.splice(i, 1);
  if (cameraSlots.length) {
    if (wasPreview || !cameraSlots.some((s) => s.is_preview)) cameraSlots[0].is_preview = true;
    renderCameraSlots();
    try {
      await saveCamerasAndPreview();
      log("Камера отвязана");
    } catch (e) { alert(e.message); }
  } else {
    try {
      await api("POST", `/api/v1/pois/${selectedPoiId}/cameras/sync`, { cameras: [] });
      await loadPois();
      buildCameraSlotsFromPoi(pois.find((p) => p.id === selectedPoiId));
      stopCameraStreams();
      setMaskSectionEnabled(false, "Нет камер — добавьте или выберите USB");
      log("Все камеры отвязаны");
    } catch (e) { alert(e.message); }
  }
}

function collectCameraPayload() {
  return cameraSlots.map((s, i) => {
    const deviceId = s.device_id || "";
    const dev = localDevices.find((d) => d.deviceId === deviceId);
    const role = s.role || "general";
    return {
      slot_index: i,
      device_id: deviceId,
      device_label: s.device_label || dev?.label || "",
      name: s.name || `Камера ${i + 1}`,
      role,
      source_type: deviceId ? "local_usb" : (s.source_type || "rtsp"),
      stream_url: deviceId ? `local://${deviceId}` : (s.stream_url || ""),
      is_active: s.is_active,
      is_preview: role === "general" ? s.is_preview : false,
    };
  });
}

async function saveCamerasAndPreview() {
  if (!selectedPoiId) return;
  const payload = collectCameraPayload();
  const preview = payload.find((c) => c.is_preview && c.is_active && c.role === "general" && (c.device_id || c.stream_url));
  if (!preview) {
    setMaskSectionEnabled(false, "Выберите рабочую камеру «общий план» с USB-устройством");
    throw new Error("Выберите рабочую камеру «общий план» с USB-устройством");
  }
  await api("POST", `/api/v1/pois/${selectedPoiId}/cameras/sync`, { cameras: payload });
  await loadPois();
  const poi = pois.find((p) => p.id === selectedPoiId);
  buildCameraSlotsFromPoi(poi);
  await refreshLocalPreview();
}

async function selectPoi(id) {
  stopCameraStreams();
  if (!id) {
    selectedPoiId = null;
    document.getElementById("camerasSection").style.display = "none";
    document.getElementById("maskSection").style.display = "none";
    setPoiFormEditable(false);
    maskPreview?.setMaskUrl("");
    maskPreview?.stop();
    refreshPoiMarkers();
    return;
  }
  selectedPoiId = id;
  const poi = pois.find((p) => p.id === id);
  if (!poi) return;
  setPoiFormEditable(true);
  document.getElementById("poiSelect").value = id;
  document.getElementById("poiName").value = poi.name;
  document.getElementById("poiAddress").value = poi.address || "";
  document.getElementById("poiComment").value = poi.comment || "";
  document.getElementById("poiLat").value = poi.latitude;
  document.getElementById("poiLng").value = poi.longitude;
  document.getElementById("camerasSection").style.display = "block";
  document.getElementById("maskSection").style.display = "block";
  pendingMaskFile = null;
  document.getElementById("maskFile").value = "";
  refreshMaskButtons();
  updateMaskPreview(poi.mask_image_url ? API + poi.mask_image_url + "?t=" + Date.now() : "");
  await loadLocalDevices();
  buildCameraSlotsFromPoi(poi);
  refreshPoiMarkers();
  map.setView([poi.latitude, poi.longitude], 15);
  await refreshLocalPreview();
}

async function loadUsers() {
  const res = await api("GET", "/api/v1/admin/users");
  const tbody = document.getElementById("usersBody");
  tbody.innerHTML = res.data.map((u) => {
    const ut = u.wallet ? u.wallet.balance_ut : "—";
    return `<tr data-id="${u.id}" class="${u.id === selectedUserId ? "selected" : ""}">
      <td>${u.email}</td><td>${u.role}</td><td>${ut}</td><td>${u.blocked_until ? "🔒" : "—"}</td></tr>`;
  }).join("");
  tbody.querySelectorAll("tr").forEach((tr) => {
    tr.onclick = () => {
      selectedUserId = tr.dataset.id;
      const u = res.data.find((x) => x.id === selectedUserId);
      document.getElementById("editUserEmail").value = u.email;
      document.getElementById("editUserName").value = u.display_name;
      document.getElementById("editUserRole").value = u.role;
      loadUsers();
    };
  });
}

async function checkNetworkQuality() {
  const data = (await api("GET", "/api/v1/admin/network-quality")).data;
  document.getElementById("qualityScore").textContent = data.aggregate_score + " / 100";
  document.getElementById("qualityGrade").textContent = `Оценка сети: ${data.grade} · камер: ${data.camera_count}`;
  document.getElementById("qualityList").innerHTML = (data.cameras || []).map((c) =>
    `<p class="hint">${c.name} (${CAMERA_ROLE_LABELS[c.role] || c.role}) @ ${c.poi_id?.slice(0, 8)}… — ${c.quality_score} (${c.status})</p>`
  ).join("") || "<p class='hint'>Нет активных камер</p>";
}

function statCard(title, value, sub = "") {
  return `<div class="admin-section" style="padding:0.75rem;text-align:center">
    <div style="font-size:1.6rem;font-weight:700">${value}</div>
    <div style="opacity:0.85">${title}</div>
    ${sub ? `<div class="hint" style="margin-top:0.25rem">${sub}</div>` : ""}
  </div>`;
}

async function loadAdminStats() {
  const s = (await api("GET", "/api/v1/admin/stats")).data;
  const byRole = s.cameras_by_role || {};
  document.getElementById("statsCards").innerHTML = [
    statCard("Пользователи", s.users_total),
    statCard("Профили", s.profiles_total),
    statCard("Кошельки", s.wallets_total, `ST: ${s.balance_st_total} · UT: ${s.balance_ut_total}`),
    statCard("Места (POI)", s.pois_total),
    statCard("Согласия", s.consents_active),
    statCard("Просмотр", `${Math.round(s.view_seconds_total)} с`),
    statCard("Перфоманс-стримы", s.performance_streams_total),
    statCard("Привязки подписи", s.signature_bindings_active),
  ].join("");
  document.getElementById("statsCameras").innerHTML = Object.entries(CAMERA_ROLE_LABELS).map(([role, label]) =>
    `<p class="hint">${label}: <strong>${byRole[role] || 0}</strong></p>`,
  ).join("");
  const tops = s.top_pois_consent || [];
  document.getElementById("statsTopPois").innerHTML = tops.length
    ? tops.map((p, i) => `<p class="hint">${i + 1}. ${p.name} — ${p.stats?.consent_rate_percent ?? "—"}%</p>`).join("")
    : "<p class='hint'>Нет данных</p>";
  const q = s.network_quality || {};
  document.getElementById("statsQuality").textContent =
    `Сводная оценка: ${q.aggregate_score ?? "—"} / 100 (${q.grade || "—"}), камер в мониторинге: ${q.camera_count ?? 0}`;
}

function bindEvents() {
  document.querySelectorAll("[data-admin-tab]").forEach((btn) => {
    btn.onclick = () => showAdminTab(btn.dataset.adminTab);
  });
  bindClick("btnBack", () => (location.href = "index.html"));
  bindClick("btnLogoutAdmin", async () => {
    try { await api("POST", "/api/v1/auth/logout", {}); } catch (_) {}
    setToken(""); location.href = "index.html";
  });
  bindChange("poiSelect", (e) => { selectPoi(e.target.value || null); });
  bindClick("btnAddPoi", () => openAddPoiModal({ fromMap: false }));
  bindClick("btnCancelAddPoi", () => {
    closeModal("addPoiModal");
    addPoiFromMap = false;
  });
  bindClick("addPoiModal", (e) => {
    if (e.target.id === "addPoiModal") {
      closeModal("addPoiModal");
      addPoiFromMap = false;
    }
  });
  bindSubmit("formAddPoi", async (e) => {
    e.preventDefault();
    const name = document.getElementById("dlgPoiName").value.trim();
    const comment = document.getElementById("dlgPoiComment").value.trim();
    if (!name) return alert("Укажите наименование");
    try {
      let lat, lon, address;
      if (addPoiFromMap) {
        lat = parseFloat(document.getElementById("dlgPoiLat").value);
        lon = parseFloat(document.getElementById("dlgPoiLng").value);
        address = document.getElementById("dlgPoiAddress").value.trim();
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) throw new Error("Некорректные координаты");
      } else {
        address = document.getElementById("dlgPoiAddress").value.trim();
        if (!address) return alert("Введите адрес");
        const g = await geocodeAddress(address);
        lat = g.lat;
        lon = g.lon;
        address = g.display || address;
      }
      const r = await api("POST", "/api/v1/pois", {
        name, address, comment, description: comment, poi_type: "live_cam",
        latitude: lat, longitude: lon, city: "", country: "",
      });
      closeModal("addPoiModal");
      addPoiFromMap = false;
      if (pickMarker) { map.removeLayer(pickMarker); pickMarker = null; }
      log("Место создано: " + name);
      await loadPois();
      selectPoi(r.data.id);
    } catch (err) { alert(err.message); }
  });
  bindClick("btnGeocode", async () => {
    if (!requireSelectedPoi("поиск по адресу")) return;
    const addr = document.getElementById("poiAddress").value.trim();
    if (!addr) return alert("Введите адрес");
    try {
      const g = await geocodeAddress(addr);
      document.getElementById("poiLat").value = g.lat;
      document.getElementById("poiLng").value = g.lon;
      if (g.display) document.getElementById("poiAddress").value = g.display;
      map.setView([g.lat, g.lon], 16);
      log("Координаты обновлены по адресу");
    } catch (e) { alert(e.message); }
  });
  bindClick("btnSavePoi", async () => {
    if (!requireSelectedPoi("сохранение")) return;
    try {
      await api("PATCH", `/api/v1/pois/${selectedPoiId}`, {
        name: document.getElementById("poiName").value,
        address: document.getElementById("poiAddress").value,
        comment: document.getElementById("poiComment").value,
        latitude: parseFloat(document.getElementById("poiLat").value),
        longitude: parseFloat(document.getElementById("poiLng").value),
      });
      log("Место сохранено");
      await loadPois();
    } catch (e) { alert(e.message); }
  });
  bindClick("btnDeletePoi", async () => {
    if (!requireSelectedPoi("удаление")) return;
    if (!confirm("Удалить место?")) return;
    await api("DELETE", `/api/v1/pois/${selectedPoiId}`);
    selectedPoiId = null;
    await loadPois();
    document.getElementById("camerasSection").style.display = "none";
    document.getElementById("maskSection").style.display = "none";
    setPoiFormEditable(false);
    stopCameraStreams();
  });
  bindClick("btnAddCameraSlot", () => {
    if (!requireSelectedPoi("добавление камеры")) return;
    if (cameraSlots.length >= 5) return alert("Максимум 5 камер");
    cameraSlots.push({
      slot_index: cameraSlots.length,
      device_id: "",
      is_active: false,
      is_preview: false,
      role: "general",
      name: `Камера ${cameraSlots.length + 1}`,
    });
    renderCameraSlots();
  });
  bindClick("btnSaveCameras", async () => {
    if (!requireSelectedPoi("сохранение камер")) return;
    try {
      await saveCamerasAndPreview();
      log("Камеры сохранены");
    } catch (e) { alert(e.message); }
  });
  bindChange("maskFile", (e) => {
    const f = e.target.files[0];
    if (!f) return;
    pendingMaskFile = f;
    updateMaskPreview(URL.createObjectURL(f));
    refreshMaskButtons();
    if (localPreviewStream || adminHls) maskPreview?.start();
  });
  bindClick("btnApplyMask", async () => {
    if (!requireSelectedPoi("применение маски")) return;
    if (!pendingMaskFile) return alert("Сначала выберите файл маски");
    try {
      const fd = new FormData();
      fd.append("image", pendingMaskFile, pendingMaskFile.name || "mask.png");
      const res = await fetch(`${API}/api/v1/pois/${selectedPoiId}/mask-image`, {
        method: "POST",
        headers: authHeaders(),
        body: fd,
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || json.success === false) throw new Error(json.error || "Не удалось применить маску");
      pendingMaskFile = null;
      document.getElementById("maskFile").value = "";
      refreshMaskButtons();
      await loadPois();
      await selectPoi(selectedPoiId);
      log("Маска применена к месту");
    } catch (e) {
      alert(e.message);
    }
  });
  bindClick("btnRemoveMask", async () => {
    if (!requireSelectedPoi("удаление маски")) return;
    try {
      await api("DELETE", `/api/v1/pois/${selectedPoiId}/mask-image`);
      pendingMaskFile = null;
      document.getElementById("maskFile").value = "";
      refreshMaskButtons();
      await loadPois();
      await selectPoi(selectedPoiId);
      log("Маска убрана — чёрная плашка");
    } catch (e) {
      alert(e.message);
    }
  });
  bindClick("btnCheckQuality", checkNetworkQuality);
  bindClick("btnRefreshStats", () => loadAdminStats().catch((e) => alert(e.message)));
  bindClick("btnAddUser", async () => {
    try {
      await api("POST", "/api/v1/admin/users", {
        email: document.getElementById("newUserEmail").value,
        password: document.getElementById("newUserPass").value,
        display_name: document.getElementById("newUserName").value,
        role: document.getElementById("newUserRole").value,
      });
      loadUsers();
    } catch (e) { alert(e.message); }
  });
  bindClick("btnSaveUser", async () => {
    if (!selectedUserId) return;
    const body = { email: document.getElementById("editUserEmail").value, display_name: document.getElementById("editUserName").value, role: document.getElementById("editUserRole").value };
    const pw = document.getElementById("editUserPass").value;
    if (pw) body.password = pw;
    await api("PATCH", `/api/v1/admin/users/${selectedUserId}`, body);
    loadUsers();
  });
  bindClick("btnBlockUser", async () => {
    if (!selectedUserId) return;
    await api("POST", `/api/v1/admin/users/${selectedUserId}/block`, { hours: parseFloat(document.getElementById("blockHours").value) || 24 });
    loadUsers();
  });
  bindClick("btnUnblockUser", async () => {
    if (!selectedUserId) return;
    await api("POST", `/api/v1/admin/users/${selectedUserId}/unblock`, {});
    loadUsers();
  });
  bindClick("btnDeleteUser", async () => {
    if (!selectedUserId || !confirm("Удалить?")) return;
    await api("DELETE", `/api/v1/admin/users/${selectedUserId}`);
    selectedUserId = null;
    loadUsers();
  });
}

export async function initAdmin() {
  if (!(await guardAdmin())) return;
  bindEvents();
  const video = document.getElementById("adminCameraPreview");
  const canvas = document.getElementById("maskOverlayCanvas");
  if (!video || !canvas) throw new Error("Превью камеры (#adminCameraPreview / #maskOverlayCanvas) не найдено");
  maskPreview = new AdminMaskPreview(video, canvas);
  maskPreview.init().catch((e) => console.warn("mask preview init", e));
  setPoiFormEditable(false);
  initMap();
  const h = await fetch(`${API}/health`).then((r) => r.json());
  document.getElementById("envBadge").textContent = h.environment || "test";
  await loadLocalDevices();
  await loadPois();
  try { await loadUsers(); } catch (_) {}
  setMaskSectionEnabled(false);
  setTimeout(() => map?.invalidateSize(), 100);
  setTimeout(() => map?.invalidateSize(), 500);
  if (!pois.length) log("Нет мест — кликните на карту или «Добавить место»");
  else if (pois.length === 1) await selectPoi(pois[0].id);
}
