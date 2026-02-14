use super::models::Log;
use anyhow::Result;
use eventsource_client::{self as es, Client};
use futures_util::StreamExt;
use tokio::sync::mpsc;

pub struct LogStream {
    receiver: mpsc::Receiver<Log>,
}

impl LogStream {
    pub async fn new(stream_url: String) -> Result<Self> {
        let (tx, rx) = mpsc::channel(100);

        tokio::spawn(async move {
            let client = es::ClientBuilder::for_url(&stream_url)
                .expect("Failed to create SSE client")
                .build();

            let mut stream = client.stream();

            while let Some(event) = stream.next().await {
                match event {
                    Ok(es::SSE::Event(ev)) => {
                        if let Ok(log) = serde_json::from_str::<Log>(&ev.data) {
                            if tx.send(log).await.is_err() {
                                break;
                            }
                        }
                    }
                    Ok(es::SSE::Comment(_)) => {
                        // Keepalive, ignore
                    }
                    Ok(es::SSE::Connected(_)) => {
                        // Connection established, ignore
                    }
                    Err(e) => {
                        eprintln!("SSE error: {:?}", e);
                        break;
                    }
                }
            }
        });

        Ok(Self { receiver: rx })
    }

    pub async fn next(&mut self) -> Option<Log> {
        self.receiver.recv().await
    }
}
