mod config;
mod logger;
mod networking;
mod parser;
mod watcher;

use clap::Command;

fn main() {
    logger::init_custom_logger();
    let env_vars = config::init_env_vars();

    let cmd = Command::new("event-watcher")
        .version(env!("CARGO_PKG_VERSION"))
        .about("Monitor EventWatcher.lua for changes and send updates to the server")
        .subcommand_required(true)
        .arg_required_else_help(true)
        .subcommand(
            Command::new("start")
                .about("Start monitoring EventWatcher.lua for changes")
                .after_help(config::format_env_vars_help(&env_vars)),
        );

    let matches = cmd.get_matches();
    match matches.subcommand() {
        Some(("start", _)) => {
            let wow_folder = config::get_env_value(&env_vars, "WOWEVENTRELAY_WOW_FOLDER");
            let event_server_url = config::get_env_value(&env_vars, "WOWEVENTRELAY_EVENT_SERVER_URL");
            watcher::monitor_events(&wow_folder, &event_server_url);
        }
        _ => unreachable!("Exhausted list of subcommands"),
    }
}
