use std::io::Read;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct Network {
    pub address: String,
}

#[derive(Deserialize)]
pub struct Data {
    pub database: String
}

#[derive(Deserialize)]
pub struct Misc {
    pub log_level: String
}

#[derive(Deserialize)]
pub struct Config {
    pub network: Network,
    pub data: Data,
    pub misc: Misc
}

impl Config {
    pub fn load(path: &str) -> Self {
        let mut file = std::fs::File::open(&path).expect(&*format!("无法打开配置文件: {}", path));
        let mut config = String::new();
        file.read_to_string(&mut config).expect(&*format!("无法读取配置文件: {}", path));
        toml::from_str(&config).expect(&*format!("无法解析配置文件: {}", path))
    }
}
