(function () {
  const form = document.getElementById("lookup-form");
  const barcode = document.getElementById("barcode");
  const lookupButton = document.getElementById("lookup-button");
  const scanButton = document.getElementById("scan-button");
  const photoButton = document.getElementById("scan-photo-button");
  const photoFile = document.getElementById("scan-photo-file");
  const panel = document.getElementById("camera-panel");
  const preview = document.getElementById("camera-preview");
  const cancel = document.getElementById("camera-cancel");
  const message = document.getElementById("camera-message");
  const cameraUnavailable = "Camera unavailable. Type the barcode instead.";
  const cameraOptions = {
    audio: false,
    video: {
      facingMode: { ideal: "environment" },
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
  };
  let activeScan = null;
  let photoAttempt = 0;

  function showMessage(text, error = false) {
    message.textContent = text;
    message.classList.toggle("error", error);
  }

  function stopCamera() {
    const scan = activeScan;
    if (!scan) return;

    activeScan = null;
    clearTimeout(scan.hintTimer);
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

  function barcodeFromResult(result) {
    const code = result.getText().trim();
    return /^\d{8,14}$/.test(code) ? code : null;
  }

  function lookUpScan(code, button) {
    barcode.value = code;
    button.focus();
    form.requestSubmit();
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

    photoAttempt += 1;
    // Give each attempt its own video so late permission or decoder results
    // from a cancelled attempt cannot interrupt a newer scan.
    const video = document.createElement("video");
    video.playsInline = true;
    video.muted = true;
    video.setAttribute("aria-label", "Barcode camera preview");
    const scan = { video, controls: null, hintTimer: null };
    activeScan = scan;
    preview.append(video);
    panel.hidden = false;
    scanButton.setAttribute("aria-expanded", "true");
    scanButton.disabled = true;
    cancel.focus();
    showMessage("Opening camera…");

    try {
      const reader = new Reader();
      const controls = await reader.decodeFromConstraints(cameraOptions, video, (result, _, controls) => {
        if (activeScan !== scan || !result) return;

        const code = barcodeFromResult(result);
        if (!code) return;

        scan.controls = controls;
        stopCamera();
        lookUpScan(code, scanButton);
      });

      if (activeScan === scan) {
        scan.controls = controls;
        showMessage("Center the whole barcode in the preview. Move back until the bars look sharp.");
        scan.hintTimer = setTimeout(() => {
          if (activeScan === scan) {
            showMessage("Still scanning. Try more light, tilt to reduce glare, or select Scan photo.");
          }
        }, 8000);
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

  async function scanPhoto() {
    const file = photoFile.files[0];
    photoFile.value = "";
    if (!file) return;

    if (lookupButton.disabled) {
      showMessage("Wait for the current lookup to finish.");
      return;
    }

    stopCamera();
    const attempt = ++photoAttempt;
    showMessage("Reading barcode from photo…");
    const url = URL.createObjectURL(file);
    try {
      const image = new Image();
      image.src = url;
      await image.decode();
      if (attempt !== photoAttempt) return;

      const Reader = window.ZXingBrowser?.BrowserMultiFormatReader;
      let code;
      try {
        if (Reader) code = barcodeFromResult(await new Reader().decodeFromImageElement(image));
      } catch {
        // Try the human-readable digits if the bars could not be decoded.
      }
      if (attempt !== photoAttempt) return;
      if (code) {
        lookUpScan(code, photoButton);
        return;
      }

      showMessage("Trying the printed digits…");
      code = await window.readPrintedBarcode(file);
      if (attempt !== photoAttempt) return;
      if (code) {
        barcode.value = code;
        showMessage("Check the digits against the package, then select Look up product.");
      } else {
        showMessage("Couldn't read the barcode. Crop the photo to the printed digits or type them.", true);
      }
    } catch {
      if (attempt === photoAttempt) {
        showMessage("Couldn't read this image. Try a clear JPG or PNG of the printed digits, or type them.", true);
      }
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  scanButton.addEventListener("click", startCamera);
  photoButton.addEventListener("click", () => photoFile.click());
  photoFile.addEventListener("change", scanPhoto);
  cancel.addEventListener("click", () => {
    stopCamera();
    scanButton.focus();
  });
  form.addEventListener("submit", () => {
    photoAttempt += 1;
    stopCamera();
    showMessage("");
  });
  window.addEventListener("pagehide", () => {
    photoAttempt += 1;
    stopCamera();
  });
})();
