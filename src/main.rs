use crate::apis::register_apis;

mod models;
mod apis;
mod config;

use log;
use badlog;
use log::warn;
use tide::http::headers::HeaderValue;
use tide::{Response, StatusCode};
use tide::convert::json;
use tide::security::{CorsMiddleware, Origin};
use tide::utils::After;


#[derive(Clone)]
pub struct GlobalState {

}

impl GlobalState {
    fn new() -> Self {
        GlobalState {

        }
    }
}


#[async_std::main]
async fn main() -> tide::Result<()> {
    let config = config::Config::load("./server_config.toml");
    badlog::init(Some(config.misc.log_level));
    log::info!("创建Web APP...");
    let mut app = tide::with_state(GlobalState::new());
    app.with(
        CorsMiddleware::new()
            .allow_credentials(true)
            .allow_origin(Origin::from("*"))
            .allow_methods("*".parse::<HeaderValue>().unwrap())
    );
    app.with(After(|resp: Response| async move {
        Ok(if resp.is_empty().unwrap_or(false) {
            match resp.status() {
                StatusCode::NotFound => Response::builder(404).body(json!({
                    "code": 404,
                    "description": "Not Found",
                    "message": "找不到对应资源~"
                })),
                StatusCode::InternalServerError => Response::builder(500).body(json!({
                    "code": 500,
                    "description": "Internal Server Error",
                    "message": "服务器内部错误，请联系管理员~"
                })),
                StatusCode::Unauthorized => Response::builder(401).body(json!({
                    "code": 401,
                    "description": "Unauthorized",
                    "message": "没有与该Endpoint交互的权限!"
                })),
                _ => {
                    if resp.status().is_success() {
                        Response::builder(resp.status()).body(json!({
                            "code": resp.status(),
                            "description": resp.status().canonical_reason(),
                            "message": "成了，但是Endpoint没有返回任何数据"
                        }))
                    } else if resp.status().is_client_error() {
                        Response::builder(resp.status()).body(json!({
                            "code": resp.status(),
                            "description": resp.status().canonical_reason(),
                            "message": "客户端错误，请检查请求格式"
                        }))
                    } else if resp.status().is_server_error() {
                        warn!("Endpoint返回5xx空响应");
                        Response::builder(resp.status()).body(json!({
                            "code": resp.status(),
                            "description": resp.status().canonical_reason(),
                            "message": "服务器错误，请联系管理员。(错误位于：核心服务器 / WebWorkers / Endpoint空响应)"
                        }))
                    } else {
                        Response::builder(resp.status()).body(json!({
                            "code": resp.status(),
                            "description": resp.status().canonical_reason(),
                            "message": "未知错误，请联系管理员。(错误位于：核心服务器 / WebWorkers / Middleware)"
                        }))
                    }
                }
            }.build()
        } else {
            resp
        })
    }));
    register_apis(&mut app);
    log::info!("服务运行于: {}", config.network.address);
    app.listen(config.network.address).await?;
    Ok(())
}
