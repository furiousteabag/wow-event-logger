use crate::config::FILE_TO_WATCH;
use crate::networking;
use crate::parser;
use log::{debug, error, info};
use notify::RecursiveMode;
use notify_debouncer_full::{new_debouncer, DebouncedEvent};
use reqwest::blocking::Client;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::mpsc::channel;
use std::time::Duration;

/// Monitor all SavedVariables directories for EventWatcher.lua changes and send updates to the server.
pub fn monitor_events(wow_folder: &str, event_server_url: &str) {
    let saved_vars_dirs = find_all_savedvars_dirs(wow_folder);

    if saved_vars_dirs.is_empty() {
        error!("No SavedVariables directories found. Exiting.");
        return;
    }

    let mut last_data: Option<String> = None;
    let client = Client::new();
    let (tx, rx) = channel();
    let mut debouncer = new_debouncer(Duration::from_secs(2), None, tx).expect("Failed to create debouncer");

    // Watch all SavedVariables directories
    debug!(
        "Setting up watchers for {} SavedVariables directories",
        saved_vars_dirs.len()
    );
    for dir in &saved_vars_dirs {
        match debouncer.watch(dir, RecursiveMode::NonRecursive) {
            Ok(_) => {
                debug!("Watching directory: {:?}", dir);
            }
            Err(e) => {
                error!("Could not watch directory {:?}: {}", dir, e);
            }
        }
    }

    info!(
        "Monitoring all {} SavedVariables directories for {} changes",
        saved_vars_dirs.len(),
        FILE_TO_WATCH
    );

    // Process existing files initially
    for dir in &saved_vars_dirs {
        let file_path = dir.join(FILE_TO_WATCH);
        if file_path.exists() {
            match fs::read_to_string(&file_path) {
                Ok(content) => {
                    debug!("Processing existing file: {:?}", file_path);
                    let current_data = parser::parse_lua_table(&content);
                    networking::try_send_update(event_server_url, &client, &current_data, &mut last_data);
                }
                Err(e) => {
                    error!("Error reading file initially at {:?}: {}", file_path, e);
                }
            }
        }
    }

    // Monitor for file changes
    for result in rx {
        match result {
            Ok(events) => {
                for DebouncedEvent { event, time: _ } in events {
                    for path in &event.paths {
                        if path
                            .file_name()
                            .map_or(false, |name| name.to_string_lossy() == FILE_TO_WATCH)
                        {
                            match event.kind {
                                notify::EventKind::Create(_) | notify::EventKind::Modify(_) => {
                                    match fs::read_to_string(path) {
                                        Ok(content) => {
                                            debug!("File changed: {:?}", path);
                                            let current_data = parser::parse_lua_table(&content);
                                            networking::try_send_update(
                                                event_server_url,
                                                &client,
                                                &current_data,
                                                &mut last_data,
                                            );
                                        }
                                        Err(e) => {
                                            error!("Error reading file {:?}: {}", path, e);
                                        }
                                    }
                                }
                                _ => {}
                            }
                        }
                    }
                }
            }
            Err(errors) => {
                for e in errors {
                    error!("Watch error: {:?}", e);
                }
            }
        }
    }

    info!("Stopped watching all SavedVariables directories");
}

/// Find all top-level SavedVariables directories in the WoW directory structure.
fn find_all_savedvars_dirs(wow_folder: &str) -> Vec<PathBuf> {
    let mut saved_vars_dirs = Vec::new();
    let wow_path = Path::new(wow_folder);

    if !wow_path.exists() {
        error!("WoW folder not found: {:?}", wow_path);
        return saved_vars_dirs;
    }

    let classic_path = wow_path.join("_classic_era_").join("WTF").join("Account");

    if !classic_path.exists() {
        error!("Classic WoW folder not found: {:?}", classic_path);
        return saved_vars_dirs;
    }

    // Find all account folders
    let Ok(account_entries) = fs::read_dir(&classic_path) else {
        error!("Could not read directory: {:?}", classic_path);
        return saved_vars_dirs;
    };

    for account_entry in account_entries {
        if let Ok(account_entry) = account_entry {
            if !account_entry.file_type().map_or(false, |ft| ft.is_dir()) {
                continue;
            }

            // Check SavedVariables dir in account root
            let saved_vars_path = account_entry.path().join("SavedVariables");
            if saved_vars_path.exists() {
                info!(
                    "Found SavedVariables directory under account: {:?}",
                    account_entry.file_name()
                );
                saved_vars_dirs.push(saved_vars_path);
            }
        }
    }

    if saved_vars_dirs.is_empty() {
        error!("No SavedVariables directories found. Please check your WoW installation.");
    } else {
        debug!("Found {} SavedVariables directories to monitor", saved_vars_dirs.len());
    }

    saved_vars_dirs
}
