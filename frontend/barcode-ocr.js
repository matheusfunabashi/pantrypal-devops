(function () {
  const cdn = "https://cdn.jsdelivr.net/npm";
  const tesseract = `${cdn}/tesseract.js@6.0.1/dist`;
  let loading;

  function loadTesseract() {
    if (!loading) {
      loading = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = `${tesseract}/tesseract.min.js`;
        script.integrity = "sha384-r1ru3tcf6FhnCFR4B7pIFG+BhFF9LlFtz/P1y4pblWn3AGs9y3lBx5SKLNf4+rED";
        script.crossOrigin = "anonymous";
        script.onload = () => resolve(window.Tesseract);
        script.onerror = () => {
          script.remove();
          reject(new Error("Couldn't load the digit reader."));
        };
        document.head.append(script);
      }).catch((error) => {
        loading = null;
        throw error;
      });
    }
    return loading;
  }

  function hasValidCheckDigit(code) {
    if (!/^(?:\d{8}|\d{12,14})$/.test(code)) return false;
    const sum = [...code].reverse().reduce((total, digit, index) => (
      total + Number(digit) * (index % 2 === 0 ? 1 : 3)
    ), 0);
    return sum % 10 === 0;
  }

  window.readPrintedBarcode = async (file) => {
    const { createWorker, PSM } = await loadTesseract();
    const worker = await createWorker("eng", 1, {
      workerPath: `${tesseract}/worker.min.js`,
      corePath: `${cdn}/tesseract.js-core@6.0.0`,
    });
    try {
      await worker.setParameters({
        tessedit_char_whitelist: "0123456789",
        tessedit_pageseg_mode: PSM.SPARSE_TEXT,
      });
      const { data: { text } } = await worker.recognize(file);
      const candidates = new Set(
        text.split(/\r?\n/).map((line) => line.replace(/\s/g, "")).filter(hasValidCheckDigit)
      );
      return candidates.size === 1 ? candidates.values().next().value : null;
    } finally {
      await worker.terminate();
    }
  };
})();
