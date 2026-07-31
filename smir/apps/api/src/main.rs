//! Smir API — POI & camera registry (Phase 0)

mod domain;
mod error;
mod routes;
mod store;

use std::net::SocketAddr;
use std::sync::Arc;

use axum::Router;
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::info;

use crate::store::AppStore;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "smir_api=info,tower_http=info".into()),
        )
        .init();

    let store = Arc::new(RwLock::new(AppStore::new_with_demo()));
    let app = Router::new()
        .merge(routes::router())
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(store);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8090));
    info!("Smir API listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.expect("bind");
    axum::serve(listener, app).await.expect("serve");
}
