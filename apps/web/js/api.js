export const API = localStorage.getItem("cmir_api") || "http://localhost:8090";

export function getToken() {
  return localStorage.getItem("cmir_token") || "";
}

export function setToken(t) {
  if (t) localStorage.setItem("cmir_token", t);
  else localStorage.removeItem("cmir_token");
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
