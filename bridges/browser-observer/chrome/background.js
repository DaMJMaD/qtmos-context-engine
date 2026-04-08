const BRIDGE_URL = "http://127.0.0.1:8765/alpha/web-observe";
const WORKSPACE_LABEL = "qtmos-alpha";

async function postObservation(message, sender) {
  const tab = sender.tab || {};
  const payload = {
    host: "browser-observer",
    workspace: WORKSPACE_LABEL,
    session: "chrome-active",
    observer_id: "chrome-extension",
    browser: "chrome",
    url: message.url || tab.url || "",
    title: message.title || tab.title || "",
    text_snippet: message.textSnippet || "",
    tab_id: tab.id || 0,
    window_id: tab.windowId || 0,
    mutated: Boolean(message.mutated),
    visible: Boolean(message.visible !== false),
    linked_surface: {
      process_name: "chrome",
      window_title: tab.title || ""
    }
  };

  try {
    const response = await fetch(BRIDGE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    console.debug("QTMoS bridge:", result);
  } catch (error) {
    console.warn("QTMoS bridge unavailable:", error);
  }
}

chrome.runtime.onMessage.addListener((message, sender) => {
  if (!message || message.type !== "QTMOS_WEB_OBSERVE") {
    return;
  }
  postObservation(message, sender);
});
