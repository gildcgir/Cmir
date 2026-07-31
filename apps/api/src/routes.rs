use std::sync::Arc;

use axum::extract::{Path, State};
use axum::routing::{get, post};
use axum::{Json, Router};
use serde_json::json;
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::domain::{CreateCameraRequest, CreatePoiRequest, GrantConsentRequest};
use crate::error::ApiResult;
use crate::store::AppStore;

pub type SharedStore = Arc<RwLock<AppStore>>;

pub fn router() -> Router<SharedStore> {
    Router::new()
        .route("/health", get(health))
        .route("/api/v1/pois", get(list_pois).post(create_poi))
        .route("/api/v1/pois/:id", get(get_poi))
        .route("/api/v1/pois/:id/cameras", post(add_camera))
        .route("/api/v1/pois/:id/consent", post(grant_consent))
        .route("/api/v1/tops/consent", get(top_consent))
        .route("/api/v1/tops/participants", get(top_participants))
}

async fn health() -> Json<serde_json::Value> {
    Json(json!({
        "status": "healthy",
        "service": "cmir-api",
        "version": "0.1.0",
        "phase": "0"
    }))
}

async fn list_pois(State(store): State<SharedStore>) -> Json<serde_json::Value> {
    let store = store.read().await;
    Json(json!({ "success": true, "data": store.list_pois() }))
}

async fn create_poi(
    State(store): State<SharedStore>,
    Json(req): Json<CreatePoiRequest>,
) -> ApiResult<Json<serde_json::Value>> {
    let mut store = store.write().await;
    let poi = store.create_poi(req)?;
    Ok(Json(json!({ "success": true, "data": poi })))
}

async fn get_poi(
    State(store): State<SharedStore>,
    Path(id): Path<Uuid>,
) -> ApiResult<Json<serde_json::Value>> {
    let store = store.read().await;
    let poi = store.get_poi(id)?;
    Ok(Json(json!({ "success": true, "data": poi })))
}

async fn add_camera(
    State(store): State<SharedStore>,
    Path(poi_id): Path<Uuid>,
    Json(req): Json<CreateCameraRequest>,
) -> ApiResult<Json<serde_json::Value>> {
    let mut store = store.write().await;
    let camera = store.add_camera(poi_id, req)?;
    Ok(Json(json!({ "success": true, "data": camera })))
}

async fn grant_consent(
    State(store): State<SharedStore>,
    Path(poi_id): Path<Uuid>,
    Json(req): Json<GrantConsentRequest>,
) -> ApiResult<Json<serde_json::Value>> {
    let mut store = store.write().await;
    let record = store.grant_consent(poi_id, req.face_embedding)?;
    Ok(Json(json!({
        "success": true,
        "data": record,
        "message": "Consent recorded; wallet created (POC mock)"
    })))
}

async fn top_consent(State(store): State<SharedStore>) -> Json<serde_json::Value> {
    let store = store.read().await;
    Json(json!({ "success": true, "data": store.top_by_consent() }))
}

async fn top_participants(State(store): State<SharedStore>) -> Json<serde_json::Value> {
    let store = store.read().await;
    Json(json!({ "success": true, "data": store.top_by_participants() }))
}
