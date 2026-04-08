function extractVisibleText() {
  const text = document.body ? document.body.innerText || "" : "";
  return text.replace(/\s+/g, " ").trim().slice(0, 240);
}

let lastSignature = "";
let mutationTimer = null;

function emitObservation(mutated) {
  const payload = {
    type: "QTMOS_WEB_OBSERVE",
    url: window.location.href,
    title: document.title || "",
    textSnippet: extractVisibleText(),
    visible: !document.hidden,
    mutated
  };
  const signature = JSON.stringify([payload.url, payload.title, payload.textSnippet, payload.visible, payload.mutated]);
  if (signature === lastSignature) {
    return;
  }
  lastSignature = signature;
  chrome.runtime.sendMessage(payload);
}

emitObservation(false);

document.addEventListener("visibilitychange", () => emitObservation(false));
window.addEventListener("focus", () => emitObservation(false));
window.addEventListener("load", () => emitObservation(false));

const observer = new MutationObserver(() => {
  if (mutationTimer) {
    clearTimeout(mutationTimer);
  }
  mutationTimer = setTimeout(() => emitObservation(true), 700);
});

if (document.documentElement) {
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: false
  });
}
