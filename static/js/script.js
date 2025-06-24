let lastDetectionTime = "";
let triggerTimeout;

function fetchLatestDetection() {
  fetch("/latest-detection")
    .then(res => res.json())
    .then(data => {
      if (!data.label || data.timestamp === lastDetectionTime) return;

      lastDetectionTime = data.timestamp;

      // Update alert text
      document.getElementById("live-alert").innerHTML = `
        <strong>KULINDA SHAMBA ALERT</strong><br />
        ${data.label} detected on ${data.timestamp.split(" ")[0]}<br />
        Time: ${data.timestamp.split(" ")[1]}<br />
        Confidence: ${data.confidence}%<br />
        Location: ${data.location || "Unknown"}
      `;

      // Update image preview
      if (data.image) {
        document.getElementById("alert-image-preview").innerHTML = `
          <img src="${data.image}" alt="Detected Animal" style="max-width:100%; border-radius:10px;">
        `;
      }

      // Auto-trigger deterrent after 5 seconds
      clearTimeout(triggerTimeout);
      triggerTimeout = setTimeout(() => {
        triggerDeterrent("auto");
      }, 5000);
    });
}

function manualTrigger() {
  clearTimeout(triggerTimeout);
  triggerDeterrent("manual");
}

function triggerDeterrent(source) {
  const status = document.getElementById("status-text");
  status.innerText = source === "manual"
    ? "🟢 Manual deterrent triggered!"
    : "🟢 Auto-triggered deterrent after 5 seconds.";
}

window.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("live-alert")) {
    setInterval(fetchLatestDetection, 4000);
    fetchLatestDetection();
  }
});
