use log::{debug, info};
use tide::{Request, Response, Server};
use tide::convert::json;
use crate::GlobalState;

async fn index(req: Request<GlobalState>) -> tide::Result<Response> {
    let real_ip = req.remote().unwrap_or("unknown");
    debug!("{:?}", req.header_names());
    Ok(Response::builder(200)
        .body(json! ({
            "message": "Hello!".repeat(10),
            "remote_address": real_ip,
        }))
        .build())
}

pub fn register_apis(app: &mut Server<GlobalState>) {
    info!("注册资源 GET / => index");
    app.at("/").get(index);


}