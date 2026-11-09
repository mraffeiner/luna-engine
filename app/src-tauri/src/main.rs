use std::{
  env,
  path::PathBuf,
  process::{Child, Command},
  sync::Mutex,
  thread,
  time::Duration,
};

use tauri::{Manager, WindowEvent};

// Spawn `docker compose up` in `cwd`
fn spawn_compose_up(cwd: &PathBuf) -> Child {
  Command::new("docker")
    .args(&["compose", "up"])
    .current_dir(cwd)
    .spawn()
    .expect("failed to spawn `docker compose up`")
}

// Spawn `docker compose stop` in `cwd`
fn spawn_compose_stop(cwd: &PathBuf) {
  let _ = Command::new("docker")
    .args(&["compose", "stop"])
    .current_dir(cwd)
    .spawn();
}

// Poll http://localhost:8080 until HTTP 200 or timeout
fn wait_for_http(url: &str, retries: u32, delay: Duration) {
  let client = reqwest::blocking::Client::new();
  for _ in 0..retries {
    if let Ok(resp) = client.get(url).send() {
      if resp.status().is_success() {
        return;
      }
    }
    thread::sleep(delay);
  }
  panic!("{} did not respond after {:?} retries", url, retries);
}

fn main() {
  tauri::Builder::default()
    // Manage a Mutex<Option<Child>> so we can kill it later
    .manage(Mutex::new(None::<Child>))
    .setup(|app| {
      // 1) Spawn `docker compose up`
      let cwd = env::current_dir().unwrap();
      let child = spawn_compose_up(&cwd);

      // 2) Store the Child in state
      *app.state::<Mutex<Option<Child>>>().lock().unwrap() = Some(child);

      // 3) Wait for your frontend to be healthy
      wait_for_http("http://localhost:8080", 60, Duration::from_secs(1));

      // 4) Show the hidden window (defined in tauri.conf.json)
      let win = app.get_window("main").unwrap();
      win.show().unwrap();

      Ok(())
    })
    .on_window_event(|event| {
      if let WindowEvent::CloseRequested { api, .. } = event.event() {
        // Prevent automatic close; we'll tear down first
        api.prevent_close();

        let cwd = env::current_dir().unwrap();
        let app_handle = event.window().app_handle();

        // 5) Run `docker compose stop`
        spawn_compose_stop(&cwd);

        // 6) Kill the original `compose up` process
        if let Some(mut child) = app_handle
          .state::<Mutex<Option<Child>>>()
          .lock()
          .unwrap()
          .take()
        {
          let _ = child.kill();
        }

        // 7) Finally close the window & exit
        event.window().close().unwrap();
      }
    })
    .run(tauri::generate_context!())
    .expect("error while running Tauri application");
}
