import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";
import * as ui from "./model/electron";

type LaunchContext = {
  overlay: boolean;
  managed: boolean;
  token: string | null;
};

let currentType = "closed";
let preopened = false;

function processCommand(line: string) {
  if (line.startsWith("action:")) {
    ui.sendGamepadEvent(line.slice(7).trim());
    return;
  }
  if (!line.startsWith("cmd:")) return;

  const command = line.slice(4).trim();
  if (command === "mute") return ui.setControllerApi(false);
  if (command === "unmute") return ui.setControllerApi(true);

  let next: "closed" | "qam" | "expanded" | "notification" | null = null;
  if (command === "open_qam_if_closed" && currentType === "closed") {
    next = "qam";
    preopened = true;
  } else if (command === "open_qam") {
    next = currentType !== "closed" && !preopened ? "closed" : "qam";
    preopened = false;
  } else if (command === "open_expanded" || command === "open_overlay") {
    next = currentType === "expanded" ? "closed" : "expanded";
  } else if (command === "open_notification") next = "notification";
  else if (command === "close" || command === "close_now") next = "closed";

  if (next) {
    currentType = next;
    ui.setUiType(next);
  }
}

export async function initTauriBridge() {
  if (!("__TAURI_INTERNALS__" in window)) return;

  window.electronUtilsRender = {
    updateStatus: (status: string) => invoke("update_status", { status }),
  };

  const context = await invoke<LaunchContext>("launch_context");
  ui.setAppType(context.overlay ? "overlay" : "app");
  if (context.overlay) ui.setUiType("closed");
  if (context.token) ui.login(context.token);

  await listen<string>("hhd-command", (event) => processCommand(event.payload));
  await invoke("mark_ready");
}
