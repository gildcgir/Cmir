function defaultApiBase() {
  const host = typeof location !== "undefined" ? location.hostname : "";
  // Prefer 127.0.0.1 with adb reverse — "localhost" can resolve oddly on some devices.
  if (!host || host === "localhost" || host === "127.0.0.1") {
    return "http://127.0.0.1:8090";
  }
  return `http://${host}:8090`;
}

function resolveApiBase() {
  const host = typeof location !== "undefined" ? location.hostname : "";
  const onLoopback = !host || host === "localhost" || host === "127.0.0.1";
  const stored = localStorage.getItem("cmir_api");
  // On phone lab via adb reverse, ignore stale overrides that break fetch
  if (onLoopback) {
    if (stored && !/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/?$/i.test(stored.replace(/\/$/, ""))) {
      localStorage.removeItem("cmir_api");
    } else if (stored) {
      return stored.replace(/\/$/, "");
    }
    return defaultApiBase();
  }
  return (stored || defaultApiBase()).replace(/\/$/, "");
}

export const API = resolveApiBase();


export function getToken() {
  return localStorage.getItem("cmir_token") || "";
}

export function setToken(t) {
  if (t) localStorage.setItem("cmir_token", t);
  else {
    localStorage.removeItem("cmir_token");
    localStorage.removeItem("cmir_user");
  }
}

export function authHeaders(extra = {}) {
  const h = { ...extra };
  const t = getToken();
  if (t) h.Authorization = "Bearer " + t;
  return h;
}

export async function api(method, path, body, isForm = false) {
  const opts = { method, headers: authHeaders() };
  if (body !== undefined) {
    if (isForm) {
      opts.body = body;
    } else {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(API + path, opts);
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || res.statusText);
  return json;
}

export async function geocodeAddress(address) {
  const q = encodeURIComponent(address);
  const res = await fetch(`${API}/api/v1/geocode?q=${q}`);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Адрес не найден");
  return {
    lat: json.data.lat,
    lon: json.data.lon,
    display: json.data.display_name,
  };
}

export async function reverseGeocode(lat, lon) {
  const res = await fetch(`${API}/api/v1/reverse-geocode?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Не удалось определить адрес");
  return {
    lat: json.data.lat,
    lon: json.data.lon,
    display: json.data.display_name,
    street: json.data.street || "",
    building: json.data.building || "",
  };
}
