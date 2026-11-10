// Desktop wrapper: starts the compose stack, opens the dashboard in a native window
// once it responds, and stops the stack again when the app exits.
//
// Run the binary from the repo root, where docker-compose.yml is.

use std::{
  env,
  path::Path,
  process::{Child, Command},
  sync::Mutex,
  thread,
  time::Duration,
};

use tauri::{Manager, RunEvent, WebviewUrl, WebviewWindowBuilder};

const DASHBOARD_URL: &str = "http://localhost:8080";

/// The `docker compose up` process, so it can be killed on exit.
struct ComposeProcess(Mutex<Option<Child>>);

fn spawn_compose_up(cwd: &Path) -> Child {
  Command::new("docker")
    .args(["compose", "up"])
    .current_dir(cwd)
    .spawn()
    .expect("failed to spawn `docker compose up`")
}

fn compose_stop(cwd: &Path) {
  // Wait for it, so the containers are stopped before the app is gone
  if let Err(e) = Command::new("docker")
    .args(["compose", "stop"])
    .current_dir(cwd)
    .status()
  {
    eprintln!("failed to run `docker compose stop`: {e}");
  }
}

/// Poll `url` until it answers with a success status. Returns false on timeout.
fn wait_for_http(url: &str, retries: u32, delay: Duration) -> bool {
  let client = reqwest::blocking::Client::new();
  for _ in 0..retries {
    if let Ok(resp) = client.get(url).send() {
      if resp.status().is_success() {
        return true;
      }
    }
    thread::sleep(delay);
  }
  false
}

fn main() {
  let app = tauri::Builder::default()
    .setup(|app| {
      let cwd = env::current_dir()?;
      app.manage(ComposeProcess(Mutex::new(Some(spawn_compose_up(&cwd)))));

      // Wait for the dashboard off the main thread, then open the window. Creating the window
      // only now means the webview never loads the URL before the stack is up.
      let handle = app.handle().clone();
      thread::spawn(move || {
        if !wait_for_http(DASHBOARD_URL, 60, Duration::from_secs(1)) {
          eprintln!("{DASHBOARD_URL} did not respond within 60 s, opening the window anyway");
        }
        let url = WebviewUrl::External(DASHBOARD_URL.parse().expect("valid URL"));
        if let Err(e) = WebviewWindowBuilder::new(&handle, "main", url)
          .title("Luna Engine")
          .inner_size(1920.0, 1080.0)
          .resizable(true)
          .build()
        {
          eprintln!("failed to open the window: {e}");
          handle.exit(1);
        }
      });

      Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building the Tauri application");

  app.run(|app_handle, event| {
    // Closing the last window exits the app. Tear the stack down on the way out.
    if let RunEvent::Exit = event {
      if let Ok(cwd) = env::current_dir() {
        compose_stop(&cwd);
      }
      if let Some(mut child) = app_handle
        .state::<ComposeProcess>()
        .0
        .lock()
        .unwrap()
        .take()
      {
        let _ = child.kill();
      }
    }
  });
}
