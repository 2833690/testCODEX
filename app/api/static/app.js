const output = document.getElementById("output");
const safety = document.getElementById("safety");

async function runAction(method, url) {
  output.textContent = `Loading ${method} ${url}...`;
  try {
    const response = await fetch(url, { method });
    const text = await response.text();
    try {
      output.textContent = JSON.stringify(JSON.parse(text), null, 2);
    } catch {
      output.textContent = text;
    }
  } catch (error) {
    output.textContent = `Request failed: ${error}`;
  }
}

async function loadSafety() {
  try {
    const response = await fetch("/health");
    const payload = await response.json();
    const mode = payload?.data?.mode ?? "unknown";
    const live = payload?.data?.live_enabled;
    safety.className = live ? "warn" : "ok";
    safety.textContent = live
      ? `⚠ Live trading enabled for mode=${mode}`
      : `✅ Safe default active (mode=${mode}, live_enabled=${live})`;
  } catch (error) {
    safety.className = "warn";
    safety.textContent = `⚠ Could not load /health: ${error}`;
  }
}

for (const button of document.querySelectorAll("button[data-method][data-url]")) {
  button.addEventListener("click", () => {
    const method = button.getAttribute("data-method") ?? "GET";
    const url = button.getAttribute("data-url") ?? "/health";
    void runAction(method, url);
  });
}

void loadSafety();
void runAction("GET", "/config");
