use super::models::*;
use anyhow::{Context, Result};
use reqwest::{cookie::{Jar, CookieStore}, Client, StatusCode};
use std::sync::Arc;

pub struct ApiClient {
    client: Client,
    base_url: String,
    cookie_jar: Arc<Jar>,
}

impl ApiClient {
    pub fn new(base_url: String) -> Result<Self> {
        let cookie_jar = Arc::new(Jar::default());
        let client = Client::builder()
            .cookie_provider(cookie_jar.clone())
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            client,
            base_url: base_url.trim_end_matches('/').to_string(),
            cookie_jar,
        })
    }

    pub async fn login(&self, username: &str, password: &str) -> Result<LoginResponse> {
        let url = format!("{}/api/auth/login", self.base_url);
        let body = LoginRequest {
            username: username.to_string(),
            password: password.to_string(),
        };

        let response = self
            .client
            .post(&url)
            .json(&body)
            .send()
            .await
            .context("Failed to send login request")?;

        if response.status() == StatusCode::UNAUTHORIZED {
            anyhow::bail!("Invalid credentials");
        }

        if !response.status().is_success() {
            anyhow::bail!("Login failed: {}", response.status());
        }

        let login_response: LoginResponse = response
            .json()
            .await
            .context("Failed to parse login response")?;

        Ok(login_response)
    }

    pub async fn get_apps(&self) -> Result<Vec<Application>> {
        let url = format!("{}/api/apps", self.base_url);

        let response = self
            .client
            .get(&url)
            .send()
            .await
            .context("Failed to fetch applications")?;

        if response.status() == StatusCode::UNAUTHORIZED {
            anyhow::bail!("Session expired. Please login again.");
        }

        if !response.status().is_success() {
            anyhow::bail!("Failed to fetch applications: {}", response.status());
        }

        let apps: Vec<Application> = response
            .json()
            .await
            .context("Failed to parse applications response")?;

        Ok(apps)
    }

    pub async fn get_logs(&self, filters: &LogFilters) -> Result<Vec<Log>> {
        let url = format!("{}/api/logs", self.base_url);

        let mut params = vec![
            ("limit", filters.limit.to_string()),
            ("offset", filters.offset.to_string()),
        ];

        if let Some(app_id) = filters.app_id {
            params.push(("app_id", app_id.to_string()));
        }

        if !filters.levels.is_empty() {
            let levels_str = filters.levels.join(",");
            params.push(("levels", levels_str));
        }

        if let Some(ref search) = filters.search {
            if !search.is_empty() {
                params.push(("search", search.clone()));
            }
        }

        if let Some(start_time) = filters.start_time {
            params.push(("start_time", start_time.to_rfc3339()));
        }

        if let Some(end_time) = filters.end_time {
            params.push(("end_time", end_time.to_rfc3339()));
        }

        let response = self
            .client
            .get(&url)
            .query(&params)
            .send()
            .await
            .context("Failed to fetch logs")?;

        if response.status() == StatusCode::UNAUTHORIZED {
            anyhow::bail!("Session expired. Please login again.");
        }

        if !response.status().is_success() {
            anyhow::bail!("Failed to fetch logs: {}", response.status());
        }

        let logs: Vec<Log> = response
            .json()
            .await
            .context("Failed to parse logs response")?;

        Ok(logs)
    }

    pub async fn get_logs_count(&self, filters: &LogFilters) -> Result<u64> {
        let url = format!("{}/api/logs/count", self.base_url);

        let mut params = vec![];

        if let Some(app_id) = filters.app_id {
            params.push(("app_id", app_id.to_string()));
        }

        if !filters.levels.is_empty() {
            let levels_str = filters.levels.join(",");
            params.push(("levels", levels_str));
        }

        if let Some(ref search) = filters.search {
            if !search.is_empty() {
                params.push(("search", search.clone()));
            }
        }

        if let Some(start_time) = filters.start_time {
            params.push(("start_time", start_time.to_rfc3339()));
        }

        if let Some(end_time) = filters.end_time {
            params.push(("end_time", end_time.to_rfc3339()));
        }

        let response = self
            .client
            .get(&url)
            .query(&params)
            .send()
            .await
            .context("Failed to fetch log count")?;

        if response.status() == StatusCode::UNAUTHORIZED {
            anyhow::bail!("Session expired. Please login again.");
        }

        if !response.status().is_success() {
            anyhow::bail!("Failed to fetch log count: {}", response.status());
        }

        let count_response: LogsCountResponse = response
            .json()
            .await
            .context("Failed to parse log count response")?;

        Ok(count_response.total)
    }

    pub async fn export_logs(
        &self,
        format: ExportFormat,
        filters: &LogFilters,
    ) -> Result<Vec<u8>> {
        let url = format!("{}/api/logs/export", self.base_url);

        let mut params = vec![("format", format.as_str().to_string())];

        if let Some(app_id) = filters.app_id {
            params.push(("app_id", app_id.to_string()));
        }

        if !filters.levels.is_empty() {
            let levels_str = filters.levels.join(",");
            params.push(("level", levels_str));
        }

        if let Some(ref search) = filters.search {
            if !search.is_empty() {
                params.push(("search", search.clone()));
            }
        }

        if let Some(start_time) = filters.start_time {
            params.push(("start_time", start_time.to_rfc3339()));
        }

        if let Some(end_time) = filters.end_time {
            params.push(("end_time", end_time.to_rfc3339()));
        }

        let response = self
            .client
            .get(&url)
            .query(&params)
            .send()
            .await
            .context("Failed to export logs")?;

        if response.status() == StatusCode::UNAUTHORIZED {
            anyhow::bail!("Session expired. Please login again.");
        }

        if !response.status().is_success() {
            anyhow::bail!("Failed to export logs: {}", response.status());
        }

        let bytes = response
            .bytes()
            .await
            .context("Failed to read export response")?;

        Ok(bytes.to_vec())
    }

    pub fn get_stream_url(&self) -> String {
        format!("{}/api/logs/stream", self.base_url)
    }

    pub fn has_session(&self) -> bool {
        !self.cookie_jar.cookies(&self.base_url.parse().unwrap()).is_none()
    }
}
