# Cmir

Privacy-first live venue map: consent kiosk, multi-pose face profiles, face masking on streams, wallets (ST/UT), Android shell.

## Quick start

```bash
bash scripts/start-lab.sh
```

- Web: http://127.0.0.1:3000/
- API: http://127.0.0.1:8090/health
- Docs: [`docs/`](./docs/)

## Layout

- `apps/web` — map / account / admin / performance
- `apps/consent-kiosk` — multi-pose face enrollment
- `apps/api_py` — Python API + SQLite
- `apps/face-worker` — MediaPipe masking / matching (`cmir_face`)
- `apps/android` — Google Play WebView shell (`com.cmir.app`)
- `apps/ingest` — MediaMTX
