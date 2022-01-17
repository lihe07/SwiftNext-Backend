use crate::apis::register_apis;

mod models;
mod apis;
mod config;

use log;
use badlog;
use tide::http::headers::HeaderValue;
use tide::security::{CorsMiddleware, Origin};


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
    register_apis(&mut app);
    log::info!("服务运行于: {}", config.network.address);
    app.listen(config.network.address).await?;
    Ok(())
}
