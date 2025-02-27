use chrono::Local;
use env_logger::{Builder, Env};
use log::Level;
use std::io::Write;

pub fn init_custom_logger() {
    Builder::from_env(Env::default().default_filter_or("info"))
        .format(|buf, record| {
            let ts = format!(
                "\x1b[32m{}\x1b[0m",
                Local::now().format("%Y-%m-%d %H:%M:%S%.3f")
            );
            let (level_color, level_str) = match record.level() {
                Level::Error => ("\x1b[1;31m", format!("{:<5}", record.level())),
                Level::Warn => ("\x1b[1;33m", format!("{:<5}", record.level())),
                Level::Info => ("\x1b[1;37m", format!("{:<5}", record.level())),
                Level::Debug => ("\x1b[1;34m", format!("{:<5}", record.level())),
                Level::Trace => ("\x1b[1;36m", format!("{:<5}", record.level())),
            };

            let level = format!("{}{}\x1b[0m", level_color, level_str);

            let module_path = record.module_path().unwrap_or("__main__");
            let file = record.file().unwrap_or("unknown");
            let line = record.line().unwrap_or(0);
            let module_str = format!("\x1b[36m{}:{}:{}\x1b[0m", module_path, file, line);

            let message_str = format!("{}{}\x1b[0m", level_color, record.args());

            writeln!(
                buf,
                "{} | {:<7} | {} - {}",
                ts, level, module_str, message_str
            )
        })
        .init();
}
