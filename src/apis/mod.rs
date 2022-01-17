use log::info;
use tide::{Body, Request, Server};
use crate::GlobalState;
use crate::models;

async fn index(_: Request<GlobalState>) -> tide::Result<Body> {
    Body::from_json(&models::Hello {
        message: "Hello! ".repeat(10),
    })
}

pub fn register_apis(app: &mut Server<GlobalState>) {
    info!("注册资源 GET / => index");
    app.at("/").get(index);
}