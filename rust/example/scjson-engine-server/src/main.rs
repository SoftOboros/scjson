//! Agent Name: scjson-engine-server
//!
//! Part of the scjson project.
//! Developed by Softoboros Technology Inc.
//! Licensed under the BSD 1-Clause License.
//!
//! Minimal HTTP server example exposing `/doc` and `/event` endpoints.

use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;

/// Read the request body from the stream.
///
/// # Parameters
/// - `stream`: TCP stream positioned after headers.
/// - `content_length`: Number of bytes to read.
///
/// # Returns
/// Body string data.
fn read_body(stream: &mut TcpStream, content_length: usize) -> String {
    let mut body = vec![0; content_length];
    if let Ok(_) = stream.read_exact(&mut body) {
        String::from_utf8_lossy(&body).into_owned()
    } else {
        String::new()
    }
}

/// Handle a single HTTP client.
///
/// # Parameters
/// - `mut stream`: TCP connection to the client.
/// - `doc`: Shared optional scjson document.
/// - `events`: Shared list of event records.
fn handle_client(mut stream: TcpStream, doc: Arc<Mutex<Option<String>>>, events: Arc<Mutex<Vec<String>>>) {
    let mut buffer = [0u8; 1024];
    if let Ok(bytes_read) = stream.read(&mut buffer) {
        let req = String::from_utf8_lossy(&buffer[..bytes_read]);
        let mut lines = req.lines();
        let request_line = lines.next().unwrap_or("");
        let mut parts = request_line.split_whitespace();
        let method = parts.next().unwrap_or("");
        let path = parts.next().unwrap_or("");
        let mut content_length = 0usize;
        for line in lines.by_ref() {
            if line.is_empty() {
                break;
            }
            if let Some(v) = line.strip_prefix("Content-Length:") {
                content_length = v.trim().parse().unwrap_or(0);
            }
        }
        let mut body = String::new();
        if content_length > 0 {
            body = read_body(&mut stream, content_length);
        }
        match (method, path) {
            ("GET", "/doc") => {
                let doc = doc.lock().unwrap();
                if let Some(ref data) = *doc {
                    let response = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                        data.len(),
                        data
                    );
                    let _ = stream.write_all(response.as_bytes());
                } else {
                    let response = "HTTP/1.1 404 Not Found\r\n\r\n";
                    let _ = stream.write_all(response.as_bytes());
                }
            }
            ("POST", "/doc") => {
                {
                    let mut doc = doc.lock().unwrap();
                    *doc = Some(body.clone());
                }
                let response = format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                    body.len(),
                    body
                );
                let _ = stream.write_all(response.as_bytes());
            }
            ("POST", "/event") => {
                {
                    let mut ev = events.lock().unwrap();
                    ev.push(body.clone());
                    let list = format!("[{}]", ev.join(","));
                    let response = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                        list.len(),
                        list
                    );
                    let _ = stream.write_all(response.as_bytes());
                }
            }
            _ => {
                let response = "HTTP/1.1 404 Not Found\r\n\r\n";
                let _ = stream.write_all(response.as_bytes());
            }
        }
    }
}

fn main() {
    let listener = TcpListener::bind("127.0.0.1:8080").expect("bind");
    let doc = Arc::new(Mutex::new(None));
    let events = Arc::new(Mutex::new(Vec::new()));
    for stream in listener.incoming() {
        if let Ok(stream) = stream {
            let d = Arc::clone(&doc);
            let e = Arc::clone(&events);
            thread::spawn(move || handle_client(stream, d, e));
        }
    }
}

