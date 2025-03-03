use std::collections::HashMap;
use std::env;

pub type EnvVars = HashMap<&'static str, (&'static str, Option<&'static str>)>;

pub const FILE_TO_WATCH: &str = "EventWatcher.lua";

pub fn init_env_vars() -> EnvVars {
    let mut vars = HashMap::new();
    vars.insert(
        "WOWEVENTRELAY_WOW_FOLDER",
        (
            "Path to WoW installation folder",
            Some("C:/Program Files (x86)/World of Warcraft"),
        ),
    );
    vars.insert(
        "WOWEVENTRELAY_EVENT_SERVER_URL",
        (
            "URL to send character updates",
            Some("https://wow.asmirnov.xyz/character"),
        ),
    );
    vars
}

pub fn get_env_value(vars: &EnvVars, key: &str) -> String {
    let (_, default) = vars.get(key).expect("Unknown environment variable");
    env::var(key).unwrap_or_else(|_| default.map(|v| v.to_string()).unwrap_or_default())
}

pub fn format_env_vars_help(vars: &EnvVars) -> String {
    let mut help = String::from("\x1b[1;4mEnvironment Variables:\x1b[0m\n");
    let mut keys: Vec<&&'static str> = vars.keys().collect();
    keys.sort();
    for &var_name in keys {
        let (description, default_value) = vars.get(var_name).unwrap();
        let var_desc = match default_value {
            Some(value) => format!("{} (default: {})", description, value),
            None => description.to_string(),
        };
        help.push_str(&format!("      {:<32} {}\n", var_name, var_desc));
    }
    if help.ends_with('\n') {
        help.pop();
    }
    help
}
