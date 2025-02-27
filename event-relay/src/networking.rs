use log::{error, info};
use reqwest::blocking::Client;
use serde_json::Value as JsonValue;

/// Send data to the event server if it differs from (or initializes) the last known state.
pub fn try_send_update(
    event_server_url: &str,
    client: &Client,
    current_data: &JsonValue,
    last_data: &mut Option<String>,
) {
    let current_json = serde_json::to_string(&current_data).unwrap_or_else(|_| "{}".to_string());

    if url::Url::parse(event_server_url).is_err() {
        error!(
            "Invalid URL format: '{}'. Please provide a valid URL.",
            event_server_url
        );
        return;
    }

    if last_data.is_none() {
        info!("Initial read of EventWatcher.lua, sending first update...");
        if send_data(event_server_url, client, current_data) {
            *last_data = Some(current_json);
        }
    } else if Some(&current_json) != last_data.as_ref() {
        // info!("Detected changes in EventWatcher.lua, sending update...");
        if send_data(event_server_url, client, current_data) {
            *last_data = Some(current_json);
        }
    } else {
        info!("EventWatcher.lua was updated, but data is unchanged");
    }
}

fn send_data(event_server_url: &str, client: &Client, data: &JsonValue) -> bool {
    info!("Attempting to send an update to: {}", event_server_url);

    let result = client.post(event_server_url).json(data).send();

    match result {
        Ok(response) => {
            let status = response.status();
            let response_copy = response.text();

            match response_copy {
                Ok(text) => {
                    let response_text = if text.trim().is_empty() {
                        "[empty]".to_string()
                    } else if text.len() > 1000 {
                        format!("(truncated): {}", &text[..1000])
                    } else {
                        text.clone()
                    };

                    if status.is_success() {
                        info!(
                            "Update sent successfully | Status: {} | Response: {}",
                            status, response_text
                        );
                        true
                    } else {
                        error!(
                            "Failed to send an update | Status: {} | Response: {}",
                            status, response_text
                        );
                        false
                    }
                }
                Err(e) => {
                    error!(
                        "Received status code {} but failed to read response body: {}",
                        status, e
                    );
                    status.is_success()
                }
            }
        }
        Err(e) => {
            if e.is_builder() {
                error!(
                    "Failed to send an update: Invalid URL format for '{}': {}",
                    event_server_url, e
                );
            } else if e.is_request() {
                error!("Failed to send an update: Request creation failed: {}", e);
            } else if e.is_redirect() {
                error!(
                    "Failed to send an update: Too many redirects from '{}': {}",
                    event_server_url, e
                );
            } else if e.is_timeout() {
                error!(
                    "Failed to send an update: Connection to '{}' timed out: {}",
                    event_server_url, e
                );
            } else if e.is_connect() {
                error!(
                    "Failed to send an update: Could not connect to '{}': {}",
                    event_server_url, e
                );
            } else {
                error!(
                    "Failed to send an update: Network error with '{}': {}",
                    event_server_url, e
                );
            }
            false
        }
    }
}
