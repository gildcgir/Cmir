use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Тип точки интереса — определяет минимум камер.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PoiType {
    LiveCam,
    SocialEvent,
    Venue,
}

impl PoiType {
    pub fn min_cameras(self) -> u32 {
        match self {
            PoiType::LiveCam => 1,
            PoiType::SocialEvent => 2,
            PoiType::Venue => 3,
        }
    }

    pub fn min_consent_cameras(self) -> u32 {
        match self {
            PoiType::LiveCam => 0,
            PoiType::SocialEvent => 1,
            PoiType::Venue => 2,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CameraRole {
    General,
    Consent,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ViewMode {
    Fisheye,
    Standard,
    Zoom2x,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Poi {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub poi_type: PoiType,
    pub latitude: f64,
    pub longitude: f64,
    pub promo_description: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreatePoiRequest {
    pub name: String,
    pub description: Option<String>,
    pub poi_type: PoiType,
    pub latitude: f64,
    pub longitude: f64,
    pub promo_description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Camera {
    pub id: Uuid,
    pub poi_id: Uuid,
    pub name: String,
    pub stream_url: String,
    pub role: CameraRole,
    pub view_mode: ViewMode,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreateCameraRequest {
    pub name: String,
    pub stream_url: String,
    pub role: CameraRole,
    pub view_mode: ViewMode,
}

#[derive(Debug, Clone, Serialize)]
pub struct PoiStats {
    pub poi_id: Uuid,
    pub consent_rate_percent: f64,
    pub participant_count_24h: u64,
    pub avatar_faces_ratio: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct PoiWithCameras {
    #[serde(flatten)]
    pub poi: Poi,
    pub cameras: Vec<Camera>,
    pub stats: PoiStats,
}

/// Consent (Phase 0 — mock wallet)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsentRecord {
    pub id: Uuid,
    pub poi_id: Uuid,
    pub wallet_address: String,
    pub consented_at: DateTime<Utc>,
    pub consent_text_version: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct GrantConsentRequest {
    /// Base64 embedding placeholder for POC
    pub face_embedding: Option<String>,
}
