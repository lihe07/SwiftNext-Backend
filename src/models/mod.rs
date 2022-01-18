use serde::Serialize;

#[derive(Serialize)]
pub struct Hello {
    pub message: String,
    pub remote_address: String
}