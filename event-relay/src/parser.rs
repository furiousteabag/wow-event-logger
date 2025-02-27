use log::error;
use mlua::{Lua, Table, Value};
use serde_json::{json, Value as JsonValue};

pub fn parse_lua_table(content: &str) -> JsonValue {
    let lua = Lua::new();

    if let Err(e) = lua.load(content).exec() {
        error!("Failed to parse Lua table: {}", e);
        return json!({});
    }

    match lua.globals().get("EventWatcherDump") {
        Ok(value) => {
            let result = lua_value_to_json(value);
            if serde_json::to_string(&result).is_err() {
                error!("Failed to serialize Lua table to JSON.");
                return json!({});
            }
            result
        }
        Err(e) => {
            error!("Failed to find EventWatcherDump in Lua globals: {}", e);
            json!({})
        }
    }
}

fn lua_table_to_json(table: Table) -> JsonValue {
    let mut map = serde_json::Map::new();

    for pair in table.pairs::<Value, Value>() {
        if let Ok((k, v)) = pair {
            let key_str = match &k {
                Value::String(s) => match s.to_str() {
                    Ok(v) => v.to_string(),
                    Err(_) => String::new(),
                },
                Value::Number(n) => n.to_string(),
                Value::Integer(i) => i.to_string(),
                Value::Boolean(b) => b.to_string(),
                _ => format!("{:?}", k),
            };
            map.insert(key_str, lua_value_to_json(v));
        }
    }

    JsonValue::Object(map)
}

fn lua_value_to_json(value: Value) -> JsonValue {
    match value {
        Value::Nil => JsonValue::Null,
        Value::Boolean(b) => JsonValue::Bool(b),
        Value::Integer(i) => JsonValue::from(i),
        Value::Number(f) => JsonValue::from(f),
        Value::String(s) => {
            let st = match s.to_str() {
                Ok(v) => v.to_string(),
                Err(_) => String::new(),
            };
            JsonValue::String(st)
        }
        Value::Table(t) => lua_table_to_json(t),
        // For function, thread, userdata, etc., just convert to string
        other => JsonValue::String(format!("{:?}", other)),
    }
}
