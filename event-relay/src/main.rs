mod logger;
mod networking;
mod parser;
mod watcher;

use clap::Parser;

/// Monitor EventWatcher.lua for changes and send updates to the server
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to WoW installation folder
    wow_folder: String,

    /// URL to send character updates
    #[arg(
        short = 'u',
        long = "event-server-url",
        default_value = "https://wow.asmirnov.xyz/character"
    )]
    event_server_url: String,
}

fn main() {
    logger::init_custom_logger();
    let args = Args::parse();
    watcher::monitor_events(&args.wow_folder, &args.event_server_url);
}
