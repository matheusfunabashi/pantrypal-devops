(function () {
  const form = document.getElementById("lookup-form");
  const barcode = document.getElementById("barcode");
  const lookupButton = document.getElementById("lookup-button");
  const scanButton = document.getElementById("scan-button");
  const panel = document.getElementById("camera-panel");
  const preview = document.getElementById("camera-preview");
  const cancel = document.getElementById("camera-cancel");
  const message = document.getElementById("camera-message");
  const cameraUnavailable = "Camera unavailable. Type the barcode instead.";
  let activeScan = null;

  function showMessage(text, error = false) {
    message.textContent = text;
    message.classList.toggle("error", error);
  }

  function stopCamera() {
    const scan = activeScan;
    if (!scan) return;

    activeScan = null;
    scan.controls?.stop();
    // Cancel can run before ZXing returns the controls.
    scan.video.srcObject?.getTracks().forEach((track) => track.stop());
    scan.video.srcObject = null;
    scan.video.remove();
    panel.hidden = true;
    scanButton.disabled = false;
    scanButton.setAttribute("aria-expanded", "false");
    showMessage("");
  }

  async function startCamera() {
    if (activeScan) return;
    if (lookupButton.disabled) {
      showMessage("Wait for the current lookup to finish.");
      return;
    }
    const Reader = window.ZXingBrowser?.BrowserMultiFormatReader;
    if (!Reader || !navigator.mediaDevices?.getUserMedia) {
      showMessage(cameraUnavailable, true);
      return;
    }

    // Give each attempt its own video so late permission or decoder results
    // from a cancelled attempt cannot interrupt a newer scan.
    const video = document.createElement("video");
    video.playsInline = true;
    video.muted = true;
    video.setAttribute("aria-label", "Barcode camera preview");
    const scan = { video, controls: null };
    activeScan = scan;
    preview.append(video);
    panel.hidden = false;
    scanButton.setAttribute("aria-expanded", "true");
    scanButton.disabled = true;
    cancel.focus();
    showMessage("Point the camera at a product barcode.");

    try {
      const reader = new Reader();
      // The pinned ZXing build requests facingMode: "environment" by default.
      const controls = await reader.decodeFromVideoDevice(undefined, video, (result, _, controls) => {
        if (activeScan !== scan || !result) return;

        const code = result.getText().trim();
        if (!/^\d{8,14}$/.test(code)) return;

        scan.controls = controls;
        stopCamera();
        barcode.value = code;
        scanButton.focus();
        form.requestSubmit();
      });

      if (activeScan === scan) {
        scan.controls = controls;
      } else if (!scan.controls) {
        // The user cancelled while the browser was still opening the camera.
        controls.stop();
      }
    } catch {
      if (activeScan !== scan) return;
      stopCamera();
      scanButton.focus();
      showMessage(cameraUnavailable, true);
    }
  }

  scanButton.addEventListener("click", startCamera);
  cancel.addEventListener("click", () => {
    stopCamera();
    scanButton.focus();
  });
  form.addEventListener("submit", () => {
    stopCamera();
    showMessage("");
  });
  window.addEventListener("pagehide", stopCamera);
})();
