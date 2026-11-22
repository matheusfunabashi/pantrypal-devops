// Already at home (S2-03). After a lookup, shows how many of that product are
// already in the pantry.
//
// - Listens to the "product:found" event from lookup.js.
// - Reads GET /pantry (5 s timeout) and matches the exact barcode string.
// - Only reads. It never writes to the pantry.
// - If the Pantry Service is down, says so; the product result still shows.

(function () {
  const PANTRY_TIMEOUT_MS = 5000;
  const UNAVAILABLE = "Pantry stock unavailable";

  const line = document.getElementById("at-home");
  let latest = 0; // only the newest lookup may update the line

  function show(text, isError) {
    line.textContent = text;
    line.className = isError ? "message error" : "message";
    line.hidden = false;
  }

  function hide() {
    latest += 1;
    line.textContent = "";
    line.hidden = true;
  }

  async function quantityAtHome(barcode) {
    const response = await fetch(`${window.API_CONFIG.pantryUrl}/pantry`, {
      signal: AbortSignal.timeout(PANTRY_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Pantry answered ${response.status}`);
    const items = await response.json();
    const item = items.find((entry) => String(entry.barcode) === barcode);
    return item ? item.quantity : 0;
  }

  async function handleFound(event) {
    const barcode = String(event.detail.barcode);
    const request = ++latest;
    show("Checking your pantry...", false);
    try {
      const count = await quantityAtHome(barcode);
      if (request !== latest) return;
      show(count > 0 ? `You have ${count} at home` : "None in your pantry", false);
    } catch (error) {
      if (request !== latest) return;
      console.error("Pantry stock check failed:", error);
      show(UNAVAILABLE, true);
    }
  }

  document.addEventListener("product:found", handleFound);
  document.addEventListener("product:cleared", hide);
})();
