/** Надёжное воспроизведение защищённого HLS через API Smir. */
import { API } from "./api.js";

export function hlsConfig() {
  return {
    lowLatencyMode: false,
    manifestLoadingTimeOut: 30000,
    manifestLoadingMaxRetry: 10,
    levelLoadingTimeOut: 30000,
    fragLoadingTimeOut: 30000,
    maxBufferLength: 30,
    startFragPrefetch: true,
  };
}

export async function waitMaskedPlayback(cameraId, clientId, { maxWaitMs = 45000, pollMs = 800 } = {}) {
  const started = Date.now();
  while (Date.now() - started < maxWaitMs) {
    const res = await fetch(
      `${API}/api/v1/cameras/${cameraId}/playback?client_id=${encodeURIComponent(clientId)}`,
    );
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "playback failed");
    const d = json.data || {};
    const url = d.masked_hls_url || d.live_hls_url;
    if (d.masked_ready && url) return { url, data: d };
    await new Promise((r) => setTimeout(r, pollMs));
  }
  throw new Error("Защищённый поток не готов — проверьте камеру и face-worker");
}

export function playHlsOnVideo(video, url, { onReady, onError } = {}) {
  return new Promise((resolve, reject) => {
    if (!url) {
      reject(new Error("Нет URL потока"));
      return;
    }
    if (window.Hls && Hls.isSupported()) {
      const hls = new Hls(hlsConfig());
      let settled = false;
      const done = (ok, err) => {
        if (settled) return;
        settled = true;
        if (!ok) {
          hls.destroy();
          reject(err || new Error("HLS error"));
          return;
        }
        resolve(hls);
      };
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().then(() => {
          onReady?.();
          done(true);
        }).catch((e) => done(false, e));
      });
      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          hls.startLoad();
          return;
        }
        if (data.fatal) {
          onError?.(data);
          done(false, new Error(data.type || "fatal"));
        }
      });
      setTimeout(() => done(false, new Error("timeout")), 35000);
      return;
    }
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      video.play().then(() => {
        onReady?.();
        resolve(null);
      }).catch(reject);
      return;
    }
    reject(new Error("HLS не поддерживается"));
  });
}

export async function acquirePoiStream(poiId, clientId, waitHls = true) {
  const res = await fetch(`${API}/api/v1/pois/${poiId}/stream/acquire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: clientId, wait_hls: waitHls }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "acquire failed");
  return json.data;
}

export function releasePoiStream(poiId, clientId) {
  if (!poiId) return;
  navigator.sendBeacon(
    `${API}/api/v1/pois/${poiId}/stream/release`,
    new Blob([JSON.stringify({ client_id: clientId })], { type: "application/json" }),
  );
}
