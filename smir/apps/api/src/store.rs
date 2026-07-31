use std::collections::HashMap;

use chrono::Utc;
use uuid::Uuid;

use crate::domain::{
    Camera, CameraRole, ConsentRecord, CreateCameraRequest, CreatePoiRequest, Poi, PoiStats,
    PoiType, PoiWithCameras,
};
use crate::error::{ApiError, ApiResult};

pub struct AppStore {
    pois: HashMap<Uuid, Poi>,
    cameras: HashMap<Uuid, Camera>,
    consents: Vec<ConsentRecord>,
    /// POC: consent rate per POI (0.0 - 100.0)
    consent_rates: HashMap<Uuid, f64>,
    participants: HashMap<Uuid, u64>,
}

impl AppStore {
    pub fn new_with_demo() -> Self {
        let mut store = Self {
            pois: HashMap::new(),
            cameras: HashMap::new(),
            consents: Vec::new(),
            consent_rates: HashMap::new(),
            participants: HashMap::new(),
        };
        store.seed_demo();
        store
    }

    fn seed_demo(&mut self) {
        let poi_id = Uuid::new_v4();
        let now = Utc::now();
        let poi = Poi {
            id: poi_id,
            name: "Demo: Social Event — Пингвинья вечеринка".into(),
            description: "Тестовая точка для Фазы 0".into(),
            poi_type: PoiType::SocialEvent,
            latitude: 41.7151,
            longitude: 44.8271,
            promo_description: "Лучшее место в городе для live-трансляций.".into(),
            created_at: now,
            updated_at: now,
        };
        self.pois.insert(poi_id, poi);

        let c1 = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: "General A".into(),
            stream_url: "rtsp://localhost/demo/general_a".into(),
            role: CameraRole::General,
            view_mode: crate::domain::ViewMode::Standard,
            is_active: true,
            created_at: now,
        };
        let c2 = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: "General B".into(),
            stream_url: "rtsp://localhost/demo/general_b".into(),
            role: CameraRole::General,
            view_mode: crate::domain::ViewMode::Fisheye,
            is_active: true,
            created_at: now,
        };
        let c3 = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: "Consent kiosk".into(),
            stream_url: "rtsp://localhost/demo/consent".into(),
            role: CameraRole::Consent,
            view_mode: crate::domain::ViewMode::Standard,
            is_active: true,
            created_at: now,
        };
        self.cameras.insert(c1.id, c1);
        self.cameras.insert(c2.id, c2);
        self.cameras.insert(c3.id, c3);

        self.consent_rates.insert(poi_id, 42.0);
        self.participants.insert(poi_id, 17);
    }

    pub fn list_pois(&self) -> Vec<PoiWithCameras> {
        self.pois
            .values()
            .map(|p| self.poi_with_cameras(p.id))
            .collect()
    }

    pub fn poi_with_cameras(&self, poi_id: Uuid) -> PoiWithCameras {
        let poi = self.pois.get(&poi_id).cloned().expect("poi exists");
        let cameras: Vec<Camera> = self
            .cameras
            .values()
            .filter(|c| c.poi_id == poi_id)
            .cloned()
            .collect();
        let stats = PoiStats {
            poi_id,
            consent_rate_percent: *self.consent_rates.get(&poi_id).unwrap_or(&0.0),
            participant_count_24h: *self.participants.get(&poi_id).unwrap_or(&0),
            avatar_faces_ratio: 1.0
                - self.consent_rates.get(&poi_id).copied().unwrap_or(0.0) / 100.0,
        };
        PoiWithCameras {
            poi,
            cameras,
            stats,
        }
    }

    pub fn create_poi(&mut self, req: CreatePoiRequest) -> ApiResult<Poi> {
        if req.name.trim().is_empty() {
            return Err(ApiError::Validation("name is required".into()));
        }
        let id = Uuid::new_v4();
        let now = Utc::now();
        let poi = Poi {
            id,
            name: req.name,
            description: req.description.unwrap_or_default(),
            poi_type: req.poi_type,
            latitude: req.latitude,
            longitude: req.longitude,
            promo_description: req.promo_description.unwrap_or_default(),
            created_at: now,
            updated_at: now,
        };
        self.pois.insert(id, poi.clone());
        self.consent_rates.insert(id, 0.0);
        self.participants.insert(id, 0);
        Ok(poi)
    }

    pub fn get_poi(&self, id: Uuid) -> ApiResult<PoiWithCameras> {
        if !self.pois.contains_key(&id) {
            return Err(ApiError::NotFound(format!("poi {}", id)));
        }
        Ok(self.poi_with_cameras(id))
    }

    pub fn add_camera(&mut self, poi_id: Uuid, req: CreateCameraRequest) -> ApiResult<Camera> {
        let poi = self
            .pois
            .get(&poi_id)
            .ok_or_else(|| ApiError::NotFound(format!("poi {}", poi_id)))?;

        if req.stream_url.trim().is_empty() {
            return Err(ApiError::Validation("stream_url is required".into()));
        }

        let camera = Camera {
            id: Uuid::new_v4(),
            poi_id,
            name: req.name,
            stream_url: req.stream_url,
            role: req.role,
            view_mode: req.view_mode,
            is_active: true,
            created_at: Utc::now(),
        };
        self.cameras.insert(camera.id, camera.clone());

        self.validate_poi_cameras(poi.poi_type, poi_id)?;

        Ok(camera)
    }

    pub fn validate_poi_cameras(&self, poi_type: PoiType, poi_id: Uuid) -> ApiResult<()> {
        let cams: Vec<&Camera> = self.cameras.values().filter(|c| c.poi_id == poi_id).collect();
        let total = cams.len() as u32;
        let consent = cams
            .iter()
            .filter(|c| c.role == CameraRole::Consent)
            .count() as u32;

        if total < poi_type.min_cameras() {
            return Err(ApiError::Validation(format!(
                "poi type {:?} requires at least {} cameras, has {}",
                poi_type, poi_type.min_cameras(), total
            )));
        }
        if consent < poi_type.min_consent_cameras() {
            return Err(ApiError::Validation(format!(
                "poi type {:?} requires at least {} consent cameras, has {}",
                poi_type, poi_type.min_consent_cameras(), consent
            )));
        }
        Ok(())
    }

    pub fn grant_consent(
        &mut self,
        poi_id: Uuid,
        _embedding: Option<String>,
    ) -> ApiResult<ConsentRecord> {
        if !self.pois.contains_key(&poi_id) {
            return Err(ApiError::NotFound(format!("poi {}", poi_id)));
        }

        let wallet = format!("0xsmir{}", Uuid::new_v4().simple());
        let record = ConsentRecord {
            id: Uuid::new_v4(),
            poi_id,
            wallet_address: wallet,
            consented_at: Utc::now(),
            consent_text_version: "0.1.0-draft".into(),
        };
        self.consents.push(record.clone());

        let rate = self.consent_rates.entry(poi_id).or_insert(0.0);
        *rate = (*rate + 5.0).min(100.0);
        *self.participants.entry(poi_id).or_insert(0) += 1;

        Ok(record)
    }

    pub fn top_by_consent(&self) -> Vec<PoiWithCameras> {
        let mut list: Vec<_> = self.list_pois();
        list.sort_by(|a, b| {
            b.stats
                .consent_rate_percent
                .partial_cmp(&a.stats.consent_rate_percent)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        list
    }

    pub fn top_by_participants(&self) -> Vec<PoiWithCameras> {
        let mut list: Vec<_> = self.list_pois();
        list.sort_by(|a, b| {
            b.stats
                .participant_count_24h
                .cmp(&a.stats.participant_count_24h)
        });
        list
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::{CameraRole, CreateCameraRequest, CreatePoiRequest, PoiType, ViewMode};

    #[test]
    fn social_event_requires_two_cameras_and_one_consent() {
        let mut store = AppStore {
            pois: HashMap::new(),
            cameras: HashMap::new(),
            consents: Vec::new(),
            consent_rates: HashMap::new(),
            participants: HashMap::new(),
        };
        let poi = store
            .create_poi(CreatePoiRequest {
                name: "Test".into(),
                description: None,
                poi_type: PoiType::SocialEvent,
                latitude: 0.0,
                longitude: 0.0,
                promo_description: None,
            })
            .unwrap();

        assert!(store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "g1".into(),
                    stream_url: "rtsp://x".into(),
                    role: CameraRole::General,
                    view_mode: ViewMode::Standard,
                },
            )
            .is_err());

        store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "g2".into(),
                    stream_url: "rtsp://y".into(),
                    role: CameraRole::General,
                    view_mode: ViewMode::Standard,
                },
            )
            .unwrap();

        assert!(store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "extra".into(),
                    stream_url: "rtsp://w".into(),
                    role: CameraRole::General,
                    view_mode: ViewMode::Standard,
                },
            )
            .is_err());

        let consent_cam = store
            .add_camera(
                poi.id,
                CreateCameraRequest {
                    name: "c1".into(),
                    stream_url: "rtsp://z".into(),
                    role: CameraRole::Consent,
                    view_mode: ViewMode::Standard,
                },
            )
            .unwrap();
        assert_eq!(consent_cam.role, CameraRole::Consent);
    }

    #[test]
    fn grant_consent_increases_rate() {
        let mut store = AppStore::new_with_demo();
        let demo_id = store.list_pois()[0].poi.id;
        let before = store.get_poi(demo_id).unwrap().stats.consent_rate_percent;
        store.grant_consent(demo_id, None).unwrap();
        let after = store.get_poi(demo_id).unwrap().stats.consent_rate_percent;
        assert!(after > before);
    }
}
