use serde::Serialize;
use std::io::{self, BufRead, Write};
use std::path::PathBuf;
use std::sync::{atomic::{AtomicBool, Ordering}, Mutex};
use tauri::{AppHandle, Emitter, Manager, State};

/// The daemon may send its first open command before WebKit has loaded the
/// frontend. Keep it until JavaScript has installed its event listener.
struct BridgeState {
    ready: AtomicBool,
    pending: Mutex<Vec<String>>,
}

#[derive(Serialize)]
struct LaunchContext {
    overlay: bool,
    managed: bool,
    token: Option<String>,
}

fn token() -> Option<String> {
    let mut paths = vec![
        PathBuf::from("/tmp/hhd/token"),
        PathBuf::from("/etc/hhd/token"),
    ];
    if let Some(home) = std::env::var_os("HOME") {
        paths.push(PathBuf::from(home).join(".config/hhd/token"));
    }
    paths
        .into_iter()
        .find_map(|path| std::fs::read_to_string(path).ok())
}

#[tauri::command]
fn launch_context() -> LaunchContext {
    LaunchContext {
        overlay: std::env::var_os("STEAM_OVERLAY").is_some(),
        managed: std::env::var_os("HHD_MANAGED").is_some(),
        token: token(),
    }
}

#[tauri::command]
fn update_status(status: String) {
    println!("stat:{status}");
    println!(
        "grab:{}",
        if status == "closed" {
            "disable"
        } else {
            "enable"
        }
    );
    let _ = io::stdout().flush();
}

fn send_command(handle: &AppHandle, command: String) {
    let state = handle.state::<BridgeState>();
    if state.ready.load(Ordering::Acquire) {
        let _ = handle.emit("hhd-command", command);
        return;
    }
    if let Ok(mut pending) = state.pending.lock() {
        pending.push(command);
    };
}

#[tauri::command]
fn mark_ready(app: AppHandle, state: State<'_, BridgeState>) {
    state.ready.store(true, Ordering::Release);
    let pending = state
        .pending
        .lock()
        .map(|mut commands| std::mem::take(&mut *commands))
        .unwrap_or_default();
    for command in pending {
        let _ = app.emit("hhd-command", command);
    }
}

fn main() {
    tauri::Builder::default()
        .manage(BridgeState {
            ready: AtomicBool::new(false),
            pending: Mutex::new(Vec::new()),
        })
        .invoke_handler(tauri::generate_handler![launch_context, update_status, mark_ready])
        .setup(|app| {
            let overlay = std::env::var_os("STEAM_OVERLAY").is_some();
            if overlay {
                if let Some(window) = app.get_webview_window("main") {
                    window.set_decorations(false)?;
                    window.set_resizable(false)?;
                    window.set_fullscreen(true)?;
                    window.set_always_on_top(true)?;
                    window.set_focus()?;
                }
            }

            let handle = app.handle().clone();
            std::thread::spawn(move || {
                for line in io::stdin().lock().lines().map_while(Result::ok) {
                    send_command(&handle, line);
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run hhd-fan-ui");
}
