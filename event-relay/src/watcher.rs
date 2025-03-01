use crate::networking;
use crate::parser;
use log::{error, info};
use notify::RecursiveMode;
use notify_debouncer_full::{new_debouncer, DebouncedEvent};
use reqwest::blocking::Client;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::mpsc::channel;
use std::time::Duration;

/// Monitor EventWatcher.lua for changes and send updates to the server using notify-debouncer-full.
pub fn monitor_events(wow_folder: &str, event_server_url: &str) {
    let event_watcher_path = match find_event_watcher(wow_folder) {
        Some(path) => path,
        None => return,
    };

    let mut last_data: Option<String> = None;

    let client = Client::new();

    let (tx, rx) = channel();
    let mut debouncer = new_debouncer(Duration::from_secs(2), None, tx).expect("Failed to create debouncer");

    let parent = event_watcher_path
        .parent()
        .expect("EventWatcher.lua has no parent directory");
    debouncer
        .watch(parent, RecursiveMode::NonRecursive)
        .unwrap_or_else(|_| {
            panic!(
                "Could not watch directory {:?}. Make sure it exists and is accessible.",
                parent
            );
        });

    match fs::read_to_string(&event_watcher_path) {
        Ok(content) => {
            let current_data = parser::parse_lua_table(&content);
            networking::try_send_update(event_server_url, &client, &current_data, &mut last_data);
        }
        Err(e) => {
            error!("Error reading file initially: {}", e);
        }
    }

    for result in rx {
        match result {
            Ok(events) => {
                for DebouncedEvent { event, time: _ } in events {
                    if event
                        .paths
                        .iter()
                        .any(|p| p.file_name() == event_watcher_path.file_name())
                    {
                        match event.kind {
                            notify::EventKind::Create(_) | notify::EventKind::Modify(_) => {
                                match fs::read_to_string(&event_watcher_path) {
                                    Ok(content) => {
                                        let current_data = parser::parse_lua_table(&content);
                                        networking::try_send_update(
                                            event_server_url,
                                            &client,
                                            &current_data,
                                            &mut last_data,
                                        );
                                    }
                                    Err(e) => {
                                        error!("Error reading file: {}", e);
                                    }
                                }
                            }
                            _ => {}
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

    info!("Stopped watching EventWatcher.lua");
}

/// Find the first EventWatcher.lua file in the WoW directory structure.
fn find_event_watcher(wow_folder: &str) -> Option<PathBuf> {
    let wow_path = Path::new(wow_folder);
    if !wow_path.exists() {
        error!("WoW folder not found: {:?}", wow_path);
        return None;
    }

    let classic_path = wow_path.join("_classic_era_").join("WTF").join("Account");

    if !classic_path.exists() {
        error!("Classic WoW folder not found: {:?}", classic_path);
        return None;
    }

    // Find first account folder
    let Ok(entries) = fs::read_dir(&classic_path) else {
        error!("Could not read directory: {:?}", classic_path);
        return None;
    };

    for entry in entries {
        if let Ok(entry) = entry {
            if let Ok(file_type) = entry.file_type() {
                if file_type.is_dir() {
                    let event_watcher = entry.path().join("SavedVariables").join("EventWatcher.lua");
                    if event_watcher.exists() {
                        info!("Found EventWatcher.lua at: {:?}", event_watcher);
                        return Some(event_watcher);
                    }
                }
            }
        }
    }

    error!("EventWatcher.lua not found in any account folder. Please ensure you install, enable, login and logout once. You can get the addon from the CurseForge page: https://www.curseforge.com/wow/addons/eventwatcher");
    None
}
